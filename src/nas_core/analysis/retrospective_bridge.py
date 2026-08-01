"""Evidence-bound selection of the retrospective RNA-seq expression bridge."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import yaml

from nas_core.domain.retrospective_bridge import (
    RetrospectiveExpressionBridgePlan,
    RetrospectiveExpressionBridgeReceipt,
)
from nas_core.ingestion.gdc import sha256
from nas_core.storage.object_store import ObjectStore


class RetrospectiveExpressionBridgeError(RuntimeError):
    """Raised when the retrospective bridge lacks exact supporting evidence."""


class RetrospectiveExpressionBridgeService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._store = store

    def freeze(
        self,
        plan: RetrospectiveExpressionBridgePlan,
        *,
        plan_path: Path,
        centroid_candidate_path: Path,
        centroid_import_receipt_path: Path,
        reference_construction_receipt_path: Path,
        matrix_audit_receipt_path: Path,
        metadata_receipt_path: Path,
        numerical_conformance_receipt_path: Path,
        reliability_specification_path: Path,
        code_revision: str,
    ) -> RetrospectiveExpressionBridgeReceipt:
        declared = (
            (plan.centroid_candidate_sha256, centroid_candidate_path),
            (plan.centroid_import_receipt_sha256, centroid_import_receipt_path),
            (
                plan.reference_construction_receipt_sha256,
                reference_construction_receipt_path,
            ),
            (plan.matrix_audit_receipt_sha256, matrix_audit_receipt_path),
            (plan.metadata_receipt_sha256, metadata_receipt_path),
            (
                plan.numerical_conformance_receipt_sha256,
                numerical_conformance_receipt_path,
            ),
            (plan.reliability_specification_sha256, reliability_specification_path),
        )
        if any(expected != sha256(path.read_bytes()) for expected, path in declared):
            raise RetrospectiveExpressionBridgeError("bridge evidence changed")

        candidate = yaml.safe_load(centroid_candidate_path.read_text(encoding="utf-8"))
        genes = candidate.get("gene_order")
        centroids = candidate.get("centroids")
        if not isinstance(genes, list) or len(genes) != 50 or len(set(genes)) != 50:
            raise RetrospectiveExpressionBridgeError("centroid panel is not unique PAM50")
        if not isinstance(centroids, dict) or len(centroids) != 5:
            raise RetrospectiveExpressionBridgeError("centroid artifact lacks five subtypes")
        if any(set(values) != set(genes) for values in centroids.values()):
            raise RetrospectiveExpressionBridgeError("centroid gene sets differ")

        reference_payload = self._store.get_bytes(plan.reference_object_key)
        if hashlib.sha256(reference_payload).hexdigest() != plan.reference_sha256:
            raise RetrospectiveExpressionBridgeError("fixed reference object changed")
        reference = json.loads(reference_payload)
        reference_values = reference.get("reference")
        if not isinstance(reference_values, dict) or set(reference_values) != set(genes):
            raise RetrospectiveExpressionBridgeError("fixed reference panel differs")

        return RetrospectiveExpressionBridgeReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            code_revision=code_revision,
            plan_sha256=sha256(plan_path.read_bytes()),
            evidence_hashes_verified=True,
            reference_object_verified=True,
            reference_gene_count=len(reference_values),
            centroid_gene_count=len(genes),
            centroid_subtype_count=len(centroids),
            tcga_input_field=plan.tcga_input_field,
            tcga_transform=plan.tcga_transform,
            gse96058_transform=plan.gse96058_transform,
            centering_operation=plan.centering_operation,
            scoring_operation=plan.scoring_operation,
            decision="retrospective_research_bridge_frozen",
            reference_locked_for_retrospective_bridge=True,
            centroids_locked_for_retrospective_bridge=True,
            performance_blind_validation_bridge_frozen=True,
            prospective_primary_assay_selected=False,
            primary_calibration_ready=False,
            classifier_executed=False,
            validation_molecular_values_accessed=False,
            outcomes_accessed=False,
            external_publication_authorized=False,
            limitations=[
                "GDC STAR/GENCODE-36 FPKM and SCAN-B Cufflinks FPKM arise from "
                "different upstream workflows.",
                "The fixed reference shares SCAN-B laboratory context with GSE96058.",
                "External validation must quantify transport degradation without "
                "adapting this bridge.",
                "This bridge does not select the future prospective primary-calibration assay.",
            ],
            next_actions=[
                "Freeze processed-input QC, failure, and abstention rules for this bridge.",
                "Keep GSE96058 molecular values inaccessible until preregistration "
                "and method lock.",
                "Select a target-matched prospective assay only under separate "
                "nonspending planning.",
            ],
        )
