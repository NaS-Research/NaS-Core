from __future__ import annotations

import json
from pathlib import Path

import pytest

from nas_core.analysis.uncalibrated_scoring import (
    UncalibratedScoringError,
    UncalibratedScoringService,
    load_centroids,
)
from nas_core.domain.retrospective_qc import (
    RetrospectiveProfileQCResult,
    RetrospectiveQCState,
    RetrospectiveSourceRole,
)
from nas_core.domain.uncalibrated_scoring import (
    AttemptedDenominatorAccounting,
    UncalibratedScoringReceipt,
    UncalibratedScoringSpecification,
    UncalibratedScoringState,
    load_uncalibrated_scoring_specification,
)

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows/studies/breast_clinical_molecular_discordance"
SPECIFICATION = STUDY / "protocol/uncalibrated_scoring_specification_v1.0.0.yaml"
QC_RECEIPT = STUDY / "protocol/retrospective_processed_input_qc_receipt_v1.0.0.yaml"
BRIDGE_RECEIPT = STUDY / "protocol/retrospective_expression_bridge_receipt_v1.0.0.yaml"
CENTROID_CANDIDATE = (
    STUDY / "protocol/artifact-candidates/genefu_2.44.0_pam50_candidate_v1.0.0.yaml"
)
CONFORMANCE_RECEIPT = STUDY / "protocol/numerical_conformance_receipt_v1.0.0.yaml"
SPECIFICATION_SCHEMA = ROOT / "workflows/uncalibrated_scoring_specification.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows/uncalibrated_scoring_receipt.schema.json"


def _service() -> tuple[UncalibratedScoringService, list[str], dict[str, dict[str, float]]]:
    specification = load_uncalibrated_scoring_specification(SPECIFICATION)
    genes, centroids = load_centroids(CENTROID_CANDIDATE)
    return (
        UncalibratedScoringService(
            specification,
            centroids=centroids,
            gene_order=genes,
        ),
        genes,
        centroids,
    )


def _valid_qc() -> RetrospectiveProfileQCResult:
    return RetrospectiveProfileQCResult(
        source_role=RetrospectiveSourceRole.TCGA_DISCOVERY,
        state=RetrospectiveQCState.VALID,
        valid=True,
        canonical_gene_count=50,
        reason_codes=[],
        report_action="continue_to_locked_scoring",
    )


def test_valid_synthetic_profile_scores_but_always_abstains() -> None:
    service, genes, centroids = _service()
    profile = tuple(centroids["Basal-like"][gene] for gene in genes)
    result = service.score(_valid_qc(), profile)
    assert result.state is UncalibratedScoringState.UNCALIBRATED
    assert result.scored is True
    assert result.top_subtype == "Basal-like"
    assert result.report_action == "abstain"
    assert result.reason_codes == ["technical_calibration_incomplete"]


def test_qc_failure_bypasses_scoring_and_abstains() -> None:
    service, _genes, _centroids = _service()
    qc = RetrospectiveProfileQCResult(
        source_role=RetrospectiveSourceRole.TCGA_DISCOVERY,
        state=RetrospectiveQCState.INSUFFICIENT_GENE_COVERAGE,
        valid=False,
        canonical_gene_count=49,
        reason_codes=["insufficient_gene_coverage"],
        report_action="abstain",
    )
    result = service.score(qc, None)
    assert result.state is UncalibratedScoringState.QC_FAILED
    assert result.scored is False
    assert result.top_subtype is None
    assert result.report_action == "abstain"


def test_score_tie_fails_closed() -> None:
    specification = load_uncalibrated_scoring_specification(SPECIFICATION)
    genes, centroids = load_centroids(CENTROID_CANDIDATE)
    centroids["HER2-enriched"] = centroids["Basal-like"].copy()
    service = UncalibratedScoringService(
        specification,
        centroids=centroids,
        gene_order=genes,
    )
    profile = tuple(centroids["Basal-like"][gene] for gene in genes)
    result = service.score(_valid_qc(), profile)
    assert result.state is UncalibratedScoringState.SCORE_FAILED
    assert result.reason_codes == ["top_score_tie"]


def test_denominator_accounting_reconciles_every_attempt_and_abstention() -> None:
    service, genes, centroids = _service()
    valid = service.score(
        _valid_qc(),
        tuple(centroids["Basal-like"][gene] for gene in genes),
    )
    failed_qc = RetrospectiveProfileQCResult(
        source_role=RetrospectiveSourceRole.TCGA_DISCOVERY,
        state=RetrospectiveQCState.NONFINITE_INPUT,
        valid=False,
        canonical_gene_count=50,
        reason_codes=["nonfinite_input"],
        report_action="abstain",
    )
    accounting = service.account([valid, service.score(failed_qc, None)])
    assert accounting.attempted_count == 2
    assert accounting.qc_valid_count == 1
    assert accounting.qc_failed_count == 1
    assert accounting.scored_count == 1
    assert accounting.uncalibrated_count == 1
    assert accounting.abstained_count == 2
    assert accounting.reported_label_count == 0


def test_inconsistent_denominators_are_rejected() -> None:
    with pytest.raises(ValueError, match="attempted count"):
        AttemptedDenominatorAccounting(
            attempted_count=2,
            qc_valid_count=1,
            qc_failed_count=0,
            scored_count=1,
            score_failed_count=0,
            uncalibrated_count=1,
            abstained_count=2,
            reported_label_count=0,
        )


def test_boundary_receipt_verifies_dependencies_without_study_execution() -> None:
    service, _genes, _centroids = _service()
    receipt = service.freeze_receipt(
        specification_path=SPECIFICATION,
        processed_input_qc_receipt_path=QC_RECEIPT,
        expression_bridge_receipt_path=BRIDGE_RECEIPT,
        centroid_candidate_path=CENTROID_CANDIDATE,
        numerical_conformance_receipt_path=CONFORMANCE_RECEIPT,
        code_revision="c3a1fa0",
    )
    assert receipt.decision == "uncalibrated_scoring_boundary_frozen"
    assert receipt.reported_label_count == 0
    assert receipt.study_classifier_executed is False
    assert receipt.outcomes_accessed is False


def test_specification_rejects_premature_label_reporting() -> None:
    specification = load_uncalibrated_scoring_specification(SPECIFICATION)
    with pytest.raises(ValueError, match="cannot cross calibration firewalls"):
        UncalibratedScoringSpecification.model_validate(
            {**specification.model_dump(), "reported_label_allowed": True}
        )


def test_qc_valid_profile_requires_exact_centered_panel() -> None:
    service, _genes, _centroids = _service()
    with pytest.raises(UncalibratedScoringError, match="exact panel"):
        service.score(_valid_qc(), None)


def test_uncalibrated_scoring_schemas_match_runtime_models() -> None:
    assert json.loads(SPECIFICATION_SCHEMA.read_text()) == (
        UncalibratedScoringSpecification.model_json_schema()
    )
    assert json.loads(RECEIPT_SCHEMA.read_text()) == (
        UncalibratedScoringReceipt.model_json_schema()
    )
