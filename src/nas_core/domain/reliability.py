"""Governed contracts for single-sample molecular-classifier reliability."""

from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

PAM50_HISTORICAL_GENES = frozenset(
    {
        "ACTR3B",
        "ANLN",
        "BAG1",
        "BCL2",
        "BIRC5",
        "BLVRA",
        "CCNB1",
        "CCNE1",
        "CDC20",
        "CDC6",
        "CDH3",
        "CENPF",
        "CEP55",
        "CXXC5",
        "EGFR",
        "ERBB2",
        "ESR1",
        "EXO1",
        "FGFR4",
        "FOXA1",
        "FOXC1",
        "GPR160",
        "GRB7",
        "KIF2C",
        "KRT14",
        "KRT17",
        "KRT5",
        "MAPT",
        "MDM2",
        "MELK",
        "MIA",
        "MKI67",
        "MLPH",
        "MMP11",
        "MYBL2",
        "MYC",
        "NAT1",
        "NDC80",
        "NUF2",
        "ORC6",
        "PGR",
        "PHGDH",
        "PTTG1",
        "RRM2",
        "SFRP1",
        "SLC39A6",
        "TMEM45B",
        "TYMS",
        "UBE2C",
        "UBE2T",
    }
)

REQUIRED_RELIABILITY_OUTPUT_FIELDS = frozenset(
    {
        "sample_id",
        "method_version",
        "input_artifact_sha256",
        "data_quality_state",
        "canonical_subtype",
        "top_score",
        "runner_up_subtype",
        "runner_up_score",
        "margin",
        "valid_perturbation_count",
        "total_perturbation_count",
        "valid_perturbation_fraction",
        "canonical_label_retention_fraction",
        "reliability_state",
        "report_action",
        "reason_codes",
        "provenance",
        "limitations",
    }
)


class ReliabilityModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SpecificationStatus(StrEnum):
    DRAFT = "draft"
    LOCKED = "locked"


class DependencyStatus(StrEnum):
    UNRESOLVED = "unresolved"
    SPECIFIED = "specified"
    APPROVED = "approved"


class CorrelationMetric(StrEnum):
    SPEARMAN = "spearman"


class PerturbationKind(StrEnum):
    LEAVE_ONE_GENE_OUT = "leave_one_gene_out"
    TECHNICAL_MEASUREMENT_ERROR = "technical_measurement_error"


class DataQualityState(StrEnum):
    VALID = "valid"
    INSUFFICIENT_GENE_COVERAGE = "insufficient_gene_coverage"
    AMBIGUOUS_GENE_MAPPING = "ambiguous_gene_mapping"
    INVALID_TRANSFORMATION = "invalid_transformation"
    NONFINITE_INPUT = "nonfinite_input"
    INVALID_CENTROID = "invalid_centroid"


class ReliabilityState(StrEnum):
    RELIABLE = "reliable"
    UNSTABLE = "unstable"
    UNCLASSIFIABLE = "unclassifiable"
    INSUFFICIENT_DATA = "insufficient_data"


class ReportAction(StrEnum):
    REPORT_LABEL = "report_label"
    ABSTAIN = "abstain"


class GovernedArtifact(ReliabilityModel):
    artifact_id: str = Field(min_length=1)
    role: str = Field(min_length=1)
    provenance: str = Field(min_length=1)
    source_url: str = Field(min_length=1)
    access_and_license_basis: str = Field(min_length=1)
    status: DependencyStatus
    sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")

    @model_validator(mode="after")
    def approved_artifact_is_immutable(self) -> GovernedArtifact:
        if self.status is DependencyStatus.APPROVED and self.sha256 is None:
            raise ValueError("an approved method artifact requires an immutable SHA-256")
        return self


class InputContract(ReliabilityModel):
    panel_name: str = Field(pattern=r"^PAM50_historical_50$")
    canonical_gene_symbols: list[str] = Field(min_length=50, max_length=50)
    historical_aliases: dict[str, str]
    required_gene_count: int = Field(ge=50, le=50)
    missing_gene_tolerance: int = Field(ge=0, le=0)
    imputation_allowed: bool
    duplicate_or_ambiguous_mapping_action: ReportAction
    nonfinite_value_action: ReportAction
    one_primary_tumor_per_call: bool

    @model_validator(mode="after")
    def validate_pam50_panel(self) -> InputContract:
        if len(self.canonical_gene_symbols) != len(set(self.canonical_gene_symbols)):
            raise ValueError("canonical PAM50 gene symbols must be unique")
        if set(self.canonical_gene_symbols) != PAM50_HISTORICAL_GENES:
            raise ValueError("canonical symbols must match the historical PAM50 50-gene panel")
        required_aliases = {"CDCA1": "NUF2", "KNTC2": "NDC80", "ORC6L": "ORC6"}
        if self.historical_aliases != required_aliases:
            raise ValueError("historical PAM50 aliases must be explicit and complete")
        if self.imputation_allowed:
            raise ValueError("the canonical run cannot impute missing PAM50 genes")
        if (
            self.duplicate_or_ambiguous_mapping_action is not ReportAction.ABSTAIN
            or self.nonfinite_value_action is not ReportAction.ABSTAIN
        ):
            raise ValueError("invalid mappings and nonfinite inputs must abstain")
        if not self.one_primary_tumor_per_call:
            raise ValueError("this contract requires exactly one primary tumor per call")
        return self


class PreprocessingContract(ReliabilityModel):
    expression_input_unit: str = Field(min_length=1)
    transformation: str = Field(min_length=1)
    gene_centering: str = Field(min_length=1)
    parameters_status: DependencyStatus
    reference_artifact: GovernedArtifact
    test_cohort_statistics_allowed: bool
    validation_cohort_adaptation_allowed: bool

    @model_validator(mode="after")
    def validate_patient_independence(self) -> PreprocessingContract:
        if self.test_cohort_statistics_allowed or self.validation_cohort_adaptation_allowed:
            raise ValueError("preprocessing must remain independent of every test cohort")
        return self


class ClassifierContract(ReliabilityModel):
    family: str = Field(pattern=r"^fixed_nearest_centroid$")
    subtype_order: list[str] = Field(min_length=5, max_length=5)
    correlation_metric: CorrelationMetric
    score_formula: str = Field(min_length=1)
    top_label_rule: str = Field(min_length=1)
    runner_up_rule: str = Field(min_length=1)
    margin_formula: str = Field(min_length=1)
    centroids: GovernedArtifact
    test_cohort_dependent_operations_allowed: bool
    outcome_guided_tuning_allowed: bool

    @model_validator(mode="after")
    def validate_classifier_boundary(self) -> ClassifierContract:
        expected = {"Luminal A", "Luminal B", "HER2-enriched", "Basal-like", "Normal-like"}
        if len(self.subtype_order) != len(set(self.subtype_order)):
            raise ValueError("subtype labels must be unique")
        if set(self.subtype_order) != expected:
            raise ValueError("the fixed classifier requires all five PAM50 centroid labels")
        if self.test_cohort_dependent_operations_allowed or self.outcome_guided_tuning_allowed:
            raise ValueError("classifier scoring cannot depend on test cohorts or outcomes")
        return self


class PerturbationDefinition(ReliabilityModel):
    perturbation_id: str = Field(min_length=1)
    kind: PerturbationKind
    status: DependencyStatus
    purpose: str = Field(min_length=1)
    procedure: str = Field(min_length=1)
    run_count: int | None = Field(default=None, ge=1)
    governing_artifact: GovernedArtifact | None = None
    random_seed: int | None = Field(default=None, ge=0)
    outcome_data_used: bool
    changes_canonical_result: bool

    @model_validator(mode="after")
    def validate_perturbation(self) -> PerturbationDefinition:
        if self.outcome_data_used:
            raise ValueError("technical perturbations cannot use outcome data")
        if self.changes_canonical_result:
            raise ValueError(
                "perturbations may characterize but never replace the canonical result"
            )
        if self.kind is PerturbationKind.LEAVE_ONE_GENE_OUT:
            if self.run_count != 50 or self.governing_artifact is not None:
                raise ValueError("leave-one-gene-out requires exactly 50 deterministic runs")
            if self.random_seed is not None:
                raise ValueError("leave-one-gene-out is deterministic and has no random seed")
        if self.kind is PerturbationKind.TECHNICAL_MEASUREMENT_ERROR:
            if self.governing_artifact is None:
                raise ValueError("measurement-error perturbation requires a governed error model")
            if self.status is DependencyStatus.APPROVED and self.random_seed is None:
                raise ValueError("approved stochastic perturbation requires a fixed random seed")
        return self


class ThresholdDefinition(ReliabilityModel):
    threshold_id: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    operator: str = Field(pattern=r"^(>=|>)$")
    value: float | None = Field(default=None, ge=0.0, le=1.0)
    status: DependencyStatus
    selection_basis: str = Field(min_length=1)
    outcome_guided_selection_allowed: bool
    validation_performance_selection_allowed: bool

    @model_validator(mode="after")
    def validate_threshold(self) -> ThresholdDefinition:
        if self.status is DependencyStatus.APPROVED and self.value is None:
            raise ValueError("an approved threshold requires a numeric value")
        if self.status is DependencyStatus.UNRESOLVED and self.value is not None:
            raise ValueError("an unresolved threshold cannot contain a provisional value")
        if (
            self.outcome_guided_selection_allowed
            or self.validation_performance_selection_allowed
        ):
            raise ValueError(
                "thresholds cannot be selected using outcomes or validation performance"
            )
        return self


class OutputContract(ReliabilityModel):
    required_fields: list[str] = Field(min_length=1)
    repeatability_formula: str = Field(min_length=1)
    valid_perturbation_fraction_formula: str = Field(min_length=1)
    allowed_quality_states: list[DataQualityState] = Field(min_length=1)
    allowed_reliability_states: list[ReliabilityState] = Field(min_length=1)
    state_actions: dict[ReliabilityState, ReportAction]
    invalid_quality_reliability_state: ReliabilityState
    biological_truth_probability_reported: bool
    clinical_recommendation_reported: bool

    @model_validator(mode="after")
    def validate_output_states(self) -> OutputContract:
        if len(self.required_fields) != len(set(self.required_fields)):
            raise ValueError("required output fields must be unique")
        if set(self.required_fields) != REQUIRED_RELIABILITY_OUTPUT_FIELDS:
            raise ValueError("output contract is missing required reliability fields")
        if set(self.allowed_quality_states) != set(DataQualityState):
            raise ValueError("output contract must preserve every declared quality state")
        if set(self.allowed_reliability_states) != set(ReliabilityState):
            raise ValueError("output contract must preserve every declared reliability state")
        if set(self.state_actions) != set(ReliabilityState):
            raise ValueError("every reliability state requires exactly one report action")
        if self.state_actions[ReliabilityState.RELIABLE] is not ReportAction.REPORT_LABEL:
            raise ValueError("only a reliable result may report a subtype label")
        for state in ReliabilityState:
            if (
                state is not ReliabilityState.RELIABLE
                and self.state_actions[state] is not ReportAction.ABSTAIN
            ):
                raise ValueError("every non-reliable state must abstain")
        if self.invalid_quality_reliability_state is not ReliabilityState.INSUFFICIENT_DATA:
            raise ValueError("an invalid quality state must produce insufficient_data")
        if self.biological_truth_probability_reported or self.clinical_recommendation_reported:
            raise ValueError("this analytical output cannot claim truth or recommend care")
        return self


class SingleSampleReliabilitySpecification(ReliabilityModel):
    schema_version: str = "1.0.0"
    specification_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    study_id: str = Field(pattern=r"^NAS-[A-Z0-9]+-[0-9]{3}$")
    question_id: str = Field(pattern=r"^NAS-RQ-[A-Z0-9]+$")
    question_version: str = Field(pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    status: SpecificationStatus
    input_contract: InputContract
    preprocessing: PreprocessingContract
    classifier: ClassifierContract
    perturbations: list[PerturbationDefinition] = Field(min_length=2)
    thresholds: list[ThresholdDefinition] = Field(min_length=2)
    outputs: OutputContract
    state_logic: list[str] = Field(min_length=4)
    unresolved_dependencies: list[str]
    execution_authorized: bool
    molecular_data_access_authorized: bool
    outcome_data_access_authorized: bool
    clinical_use_authorized: bool

    @model_validator(mode="after")
    def validate_governed_method(self) -> SingleSampleReliabilitySpecification:
        perturbation_ids = [item.perturbation_id for item in self.perturbations]
        if len(perturbation_ids) != len(set(perturbation_ids)):
            raise ValueError("perturbation IDs must be unique")
        if {item.kind for item in self.perturbations} != set(PerturbationKind):
            raise ValueError("the minimum perturbation panel requires both declared families")
        threshold_ids = [item.threshold_id for item in self.thresholds]
        if len(threshold_ids) != len(set(threshold_ids)):
            raise ValueError("threshold IDs must be unique")
        if self.outcome_data_access_authorized or self.clinical_use_authorized:
            raise ValueError("this method specification cannot authorize outcomes or clinical use")
        if self.status is SpecificationStatus.DRAFT:
            if self.execution_authorized or self.molecular_data_access_authorized:
                raise ValueError("a draft specification cannot authorize molecular execution")
            return self

        dependencies: list[DependencyStatus] = [
            self.preprocessing.parameters_status,
            self.preprocessing.reference_artifact.status,
            self.classifier.centroids.status,
            *(item.status for item in self.perturbations),
            *(item.status for item in self.thresholds),
        ]
        if any(status is not DependencyStatus.APPROVED for status in dependencies):
            raise ValueError("a locked specification requires every dependency to be approved")
        if self.unresolved_dependencies:
            raise ValueError("a locked specification cannot retain unresolved dependencies")
        if self.execution_authorized != self.molecular_data_access_authorized:
            raise ValueError(
                "execution and molecular-data authorization must be granted or withheld together"
            )
        return self


def load_reliability_specification(path: Path) -> SingleSampleReliabilitySpecification:
    return SingleSampleReliabilitySpecification.model_validate(
        yaml.safe_load(path.read_text(encoding="utf-8"))
    )


def write_reliability_schema(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        SingleSampleReliabilitySpecification.model_json_schema(),
        indent=2,
        sort_keys=True,
    )
    path.write_text(f"{payload}\n", encoding="utf-8")
