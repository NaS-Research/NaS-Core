"""Deterministic, source-isolated technical-replicate feasibility pilots."""

from __future__ import annotations

import csv
import gzip
import hashlib
import io
import itertools
import json
import math
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy.stats import pearsonr, spearmanr  # type: ignore[import-untyped]

from nas_core.domain.calibration_feasibility_artifact import (
    CalibrationFeasibilityAcquisitionReceipt,
    CalibrationFeasibilityArtifactKind,
)
from nas_core.domain.calibration_feasibility_pilot import (
    CalibrationFeasibilityPilotPlan,
    CalibrationFeasibilityPilotReceipt,
    SourcePilotSummary,
)
from nas_core.domain.reliability import SingleSampleReliabilitySpecification
from nas_core.ingestion.gdc import sha256
from nas_core.storage.object_store import ObjectStore

_GSE60788_PRIMARY = re.compile(r"^(P[0-9]+)$")
_GSE60788_REPLICATE = re.compile(r"^(P[0-9]+)-replicate$")
_GSE130397_TRIPLICATE = re.compile(
    r"^GSM[0-9]+_FFPE_RNASeq_(OVA|ACC)_(S[12])_(0[123])_readsPerGene\.txt\.gz$"
)
_GSE130397_RESEQUENCE = re.compile(
    r"^GSM[0-9]+_FFPE_RNASeq_ACC_ER_(S0[1-6])(_Reseq)?_readsPerGene\.txt\.gz$"
)


class CalibrationFeasibilityPilotError(RuntimeError):
    """Raised when an excluded feasibility pilot cannot be reproduced safely."""


@dataclass(frozen=True, slots=True)
class PairMetrics:
    spearman: float
    pearson: float
    mae: float
    rmse: float


@dataclass(frozen=True, slots=True)
class GroupMetrics:
    group_id: str
    pair_count: int
    spearman: float
    pearson: float
    mae: float
    rmse: float
    gene_absolute_differences: dict[str, float]


def calculate_pair_metrics(left: np.ndarray, right: np.ndarray) -> PairMetrics:
    """Calculate the four prespecified metrics on one 50-gene pair."""
    if left.shape != (50,) or right.shape != (50,):
        raise CalibrationFeasibilityPilotError("pair must contain exactly 50 genes")
    if not np.all(np.isfinite(left)) or not np.all(np.isfinite(right)):
        raise CalibrationFeasibilityPilotError("pair contains a nonfinite value")
    if np.ptp(left) == 0 or np.ptp(right) == 0:
        raise CalibrationFeasibilityPilotError("correlation is undefined for constant data")
    delta = left - right
    spearman = float(spearmanr(left, right).statistic)
    pearson = float(pearsonr(left, right).statistic)
    if not math.isfinite(spearman) or not math.isfinite(pearson):
        raise CalibrationFeasibilityPilotError("pair correlation is nonfinite")
    return PairMetrics(
        spearman=spearman,
        pearson=pearson,
        mae=float(np.mean(np.abs(delta))),
        rmse=float(np.sqrt(np.mean(np.square(delta)))),
    )


def summarize_group(
    group_id: str,
    profiles: list[dict[str, float]],
    genes: list[str],
) -> GroupMetrics:
    """Use all unordered pairs, then reduce to one independent-group estimate."""
    if len(profiles) < 2:
        raise CalibrationFeasibilityPilotError("replicate group must have at least two profiles")
    vectors = [np.asarray([profile[gene] for gene in genes], dtype=float) for profile in profiles]
    pair_metrics: list[PairMetrics] = []
    gene_differences: dict[str, list[float]] = defaultdict(list)
    for left, right in itertools.combinations(vectors, 2):
        pair_metrics.append(calculate_pair_metrics(left, right))
        for gene, difference in zip(genes, np.abs(left - right), strict=True):
            gene_differences[gene].append(float(difference))
    return GroupMetrics(
        group_id=group_id,
        pair_count=len(pair_metrics),
        spearman=float(np.median([item.spearman for item in pair_metrics])),
        pearson=float(np.median([item.pearson for item in pair_metrics])),
        mae=float(np.median([item.mae for item in pair_metrics])),
        rmse=float(np.median([item.rmse for item in pair_metrics])),
        gene_absolute_differences={
            gene: float(np.median(values))
            for gene, values in sorted(gene_differences.items())
        },
    )


def bootstrap_median_interval(
    values: list[float],
    *,
    replicates: int,
    random_seed: int,
) -> tuple[float, float]:
    """Return a deterministic group-resampling percentile interval."""
    if not values:
        raise CalibrationFeasibilityPilotError("bootstrap requires independent groups")
    array = np.asarray(values, dtype=float)
    rng = np.random.default_rng(random_seed)
    indices = rng.integers(0, len(array), size=(replicates, len(array)))
    estimates = np.median(array[indices], axis=1)
    lower, upper = np.percentile(estimates, [2.5, 97.5])
    return float(lower), float(upper)


class CalibrationFeasibilityPilotService:
    def __init__(self, *, store: ObjectStore) -> None:
        self._store = store

    def execute(
        self,
        plan: CalibrationFeasibilityPilotPlan,
        acquisition: CalibrationFeasibilityAcquisitionReceipt,
        specification: SingleSampleReliabilitySpecification,
        *,
        plan_path: Path,
        acquisition_receipt_path: Path,
        feasibility_audit_receipt_path: Path,
        annotation_resolution_receipt_path: Path,
        annotation_mapping_receipt_path: Path,
        reliability_specification_path: Path,
        code_revision: str,
    ) -> CalibrationFeasibilityPilotReceipt:
        self._validate_provenance(
            plan,
            acquisition_receipt_path=acquisition_receipt_path,
            feasibility_audit_receipt_path=feasibility_audit_receipt_path,
            annotation_resolution_receipt_path=annotation_resolution_receipt_path,
            annotation_mapping_receipt_path=annotation_mapping_receipt_path,
            reliability_specification_path=reliability_specification_path,
        )
        payloads = self._verified_payloads(acquisition)
        mapping = self._load_mapping(plan)
        genes = list(specification.input_contract.canonical_gene_symbols)
        if set(genes) != set(mapping):
            raise CalibrationFeasibilityPilotError("PAM50 mapping and specification differ")

        gse60788_groups = self._gse60788_groups(
            payloads,
            genes,
            specification.input_contract.historical_aliases,
        )
        gse130397_groups = self._gse130397_groups(
            acquisition,
            payloads,
            genes,
            mapping,
            plan,
        )
        summaries: list[SourcePilotSummary] = []
        details: dict[str, Any] = {
            "schema_version": "1.0.0",
            "study_id": plan.study_id,
            "estimands": {
                "pair_metrics": plan.pair_metrics,
                "group_aggregation": plan.group_aggregation,
                "source_summary": plan.source_summary,
                "bootstrap_unit": plan.bootstrap_unit,
                "bootstrap_replicates": plan.bootstrap_replicates,
                "random_seed": plan.random_seed,
            },
            "sources": [],
        }
        for source_id, scale, groups in (
            (
                "ncbi-geo-gse60788",
                "unchanged_source_normalized_values",
                gse60788_groups,
            ),
            ("ncbi-geo-gse130397", "log2_cpm_plus_1", gse130397_groups),
        ):
            summary, source_details = self._summarize_source(
                source_id,
                scale,
                groups,
                genes,
                plan,
            )
            summaries.append(summary)
            details["sources"].append(source_details)

        details_payload = json.dumps(
            details,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        if self._store.exists(plan.details_object_key):
            raise CalibrationFeasibilityPilotError("immutable pilot details already exist")
        self._store.put_bytes(
            plan.details_object_key,
            details_payload,
            content_type="application/json",
        )
        details_sha = hashlib.sha256(details_payload).hexdigest()
        return CalibrationFeasibilityPilotReceipt(
            receipt_version="1.0.0",
            study_id=plan.study_id,
            code_revision=code_revision,
            plan_sha256=sha256(plan_path.read_bytes()),
            source_summaries=summaries,
            details_object_key=plan.details_object_key,
            details_sha256=details_sha,
            details_object_verified=(
                self._store.exists(plan.details_object_key)
                and hashlib.sha256(
                    self._store.get_bytes(plan.details_object_key)
                ).hexdigest()
                == details_sha
            ),
            decision="excluded_pilots_complete_primary_calibration_not_ready",
            sources_pooled=False,
            thresholds_estimated=False,
            classifier_executed=False,
            outcomes_accessed=False,
            source_identifiers_retained=False,
            molecular_values_retained_in_git=False,
            external_export_authorized=False,
            external_publication_authorized=False,
            limitations=[
                "GSE60788 contains only six declared pairs and its exact source "
                "transform is not inferred.",
                "GSE130397 contains seven replicate-capable groups and mixes "
                "library-preparation methods.",
                "Public title patterns do not independently prove same-RNA or "
                "same-specimen lineage.",
                "Bootstrap intervals describe small feasibility sets and are not "
                "population inference.",
            ],
            next_actions=[
                "Use these source-specific estimates only to inform blinded precision planning.",
                "Do not derive reliability thresholds or pool either excluded source.",
                "Keep primary calibration on hold pending an eligible independent calibration set.",
            ],
        )

    @staticmethod
    def _validate_provenance(
        plan: CalibrationFeasibilityPilotPlan,
        *,
        acquisition_receipt_path: Path,
        feasibility_audit_receipt_path: Path,
        annotation_resolution_receipt_path: Path,
        annotation_mapping_receipt_path: Path,
        reliability_specification_path: Path,
    ) -> None:
        declared = (
            (plan.feasibility_acquisition_receipt_sha256, acquisition_receipt_path),
            (plan.feasibility_audit_receipt_sha256, feasibility_audit_receipt_path),
            (plan.annotation_resolution_receipt_sha256, annotation_resolution_receipt_path),
            (plan.annotation_mapping_receipt_sha256, annotation_mapping_receipt_path),
            (plan.reliability_specification_sha256, reliability_specification_path),
        )
        if any(expected != sha256(path.read_bytes()) for expected, path in declared):
            raise CalibrationFeasibilityPilotError("pilot provenance changed")

    def _verified_payloads(
        self,
        acquisition: CalibrationFeasibilityAcquisitionReceipt,
    ) -> dict[str, bytes]:
        payloads: dict[str, bytes] = {}
        for artifact in acquisition.artifacts:
            if (
                artifact.artifact_kind
                is not CalibrationFeasibilityArtifactKind.PROCESSED_EXPRESSION
            ):
                continue
            payload = self._store.get_bytes(artifact.object_key)
            if (
                len(payload) != artifact.content_length_bytes
                or hashlib.sha256(payload).hexdigest() != artifact.sha256
            ):
                raise CalibrationFeasibilityPilotError(
                    f"stored source artifact changed: {artifact.filename}"
                )
            payloads[artifact.filename] = payload
        return payloads

    def _load_mapping(self, plan: CalibrationFeasibilityPilotPlan) -> dict[str, str]:
        payload = self._store.get_bytes(plan.annotation_mapping_object_key)
        if hashlib.sha256(payload).hexdigest() != plan.annotation_mapping_artifact_sha256:
            raise CalibrationFeasibilityPilotError("annotation mapping artifact changed")
        document = json.loads(payload)
        mapping = document.get("gene_to_ensembl_id")
        if not isinstance(mapping, dict) or len(mapping) != 50:
            raise CalibrationFeasibilityPilotError("annotation mapping is incomplete")
        return {str(gene): str(gene_id).split(".", 1)[0] for gene, gene_id in mapping.items()}

    @staticmethod
    def _gse60788_groups(
        payloads: dict[str, bytes],
        genes: list[str],
        aliases: dict[str, str],
    ) -> list[GroupMetrics]:
        filename = "GSE60788_rnaseq_gex_normalized.txt.gz"
        try:
            reader = csv.reader(
                io.TextIOWrapper(gzip.GzipFile(fileobj=io.BytesIO(payloads[filename]))),
                delimiter="\t",
            )
            header = next(reader)
        except (KeyError, OSError, StopIteration) as error:
            raise CalibrationFeasibilityPilotError("invalid GSE60788 matrix") from error
        if not header or header[0] != "Gene Symbol":
            raise CalibrationFeasibilityPilotError("unexpected GSE60788 matrix header")
        indices = {label: index for index, label in enumerate(header[1:])}
        pair_bases = sorted(
            match.group(1)
            for label in indices
            if (match := _GSE60788_REPLICATE.fullmatch(label)) is not None
        )
        if len(pair_bases) != 6 or any(base not in indices for base in pair_bases):
            raise CalibrationFeasibilityPilotError("GSE60788 must contain six complete pairs")
        profiles: dict[str, dict[str, float]] = {
            label: {}
            for base in pair_bases
            for label in (base, f"{base}-replicate")
        }
        canonical = set(genes)
        for row in reader:
            if len(row) != len(header):
                raise CalibrationFeasibilityPilotError("ragged GSE60788 matrix")
            gene = aliases.get(row[0], row[0])
            if gene not in canonical:
                continue
            for label in profiles:
                if gene in profiles[label]:
                    raise CalibrationFeasibilityPilotError("duplicate PAM50 gene in GSE60788")
                profiles[label][gene] = float(row[indices[label] + 1])
        if any(set(profile) != canonical for profile in profiles.values()):
            raise CalibrationFeasibilityPilotError("GSE60788 PAM50 panel is incomplete")
        return [
            summarize_group(
                _hashed_group_id("ncbi-geo-gse60788", base),
                [profiles[base], profiles[f"{base}-replicate"]],
                genes,
            )
            for base in pair_bases
        ]

    @staticmethod
    def _gse130397_groups(
        acquisition: CalibrationFeasibilityAcquisitionReceipt,
        payloads: dict[str, bytes],
        genes: list[str],
        mapping: dict[str, str],
        plan: CalibrationFeasibilityPilotPlan,
    ) -> list[GroupMetrics]:
        id_to_gene = {gene_id: gene for gene, gene_id in mapping.items()}
        grouped_profiles: dict[str, list[dict[str, float]]] = defaultdict(list)
        artifacts = [
            item
            for item in acquisition.artifacts
            if item.source_id == "ncbi-geo-gse130397"
            and item.artifact_kind is CalibrationFeasibilityArtifactKind.PROCESSED_EXPRESSION
        ]
        for artifact in artifacts:
            match = _GSE130397_TRIPLICATE.fullmatch(artifact.filename)
            reseq = _GSE130397_RESEQUENCE.fullmatch(artifact.filename)
            if match is not None:
                method, sample, _replicate = match.groups()
                group_label = f"{method}_{sample}"
            elif reseq is not None:
                sample, _reseq = reseq.groups()
                group_label = f"ACC_ER_{sample}"
            else:
                raise CalibrationFeasibilityPilotError(
                    "unrecognized GSE130397 processed-expression filename"
                )
            selected_column = (
                plan.gse130397_ovation_count_column
                if "_OVA_" in artifact.filename
                else plan.gse130397_access_count_column
            )
            reader = csv.reader(
                io.TextIOWrapper(
                    gzip.GzipFile(fileobj=io.BytesIO(payloads[artifact.filename]))
                ),
                delimiter="\t",
            )
            header = next(reader, None)
            if header != ["Gene", "Unstranded", "fwd", "rev"]:
                raise CalibrationFeasibilityPilotError("unexpected GSE130397 count header")
            column_index = header.index(selected_column)
            total = 0
            counts: dict[str, int] = {}
            rows = 0
            for row in reader:
                if len(row) != 4:
                    raise CalibrationFeasibilityPilotError("ragged GSE130397 count file")
                rows += 1
                count = int(row[column_index])
                if count < 0:
                    raise CalibrationFeasibilityPilotError("negative GSE130397 count")
                total += count
                gene_id = row[0].split(".", 1)[0]
                if gene_id in id_to_gene:
                    counts[id_to_gene[gene_id]] = count
            if rows != 60675 or total <= 0 or set(counts) != set(genes):
                raise CalibrationFeasibilityPilotError("GSE130397 panel or library is invalid")
            grouped_profiles[group_label].append(
                {gene: math.log2((counts[gene] / total * 1_000_000) + 1) for gene in genes}
            )
        eligible = {
            label: profiles
            for label, profiles in grouped_profiles.items()
            if len(profiles) >= 2
        }
        pair_count = sum(math.comb(len(profiles), 2) for profiles in eligible.values())
        if len(eligible) != 7 or pair_count != 15:
            raise CalibrationFeasibilityPilotError(
                "GSE130397 must contain seven eligible groups and fifteen pairs"
            )
        return [
            summarize_group(
                _hashed_group_id("ncbi-geo-gse130397", label),
                profiles,
                genes,
            )
            for label, profiles in sorted(eligible.items())
        ]

    @staticmethod
    def _summarize_source(
        source_id: str,
        scale: str,
        groups: list[GroupMetrics],
        genes: list[str],
        plan: CalibrationFeasibilityPilotPlan,
    ) -> tuple[SourcePilotSummary, dict[str, Any]]:
        spearman_values = [group.spearman for group in groups]
        rmse_values = [group.rmse for group in groups]
        spearman_interval = bootstrap_median_interval(
            spearman_values,
            replicates=plan.bootstrap_replicates,
            random_seed=plan.random_seed,
        )
        rmse_interval = bootstrap_median_interval(
            rmse_values,
            replicates=plan.bootstrap_replicates,
            random_seed=plan.random_seed + 1,
        )
        gene_differences = {
            gene: float(
                np.median([group.gene_absolute_differences[gene] for group in groups])
            )
            for gene in genes
        }
        highest = sorted(
            gene_differences,
            key=lambda gene: (-gene_differences[gene], gene),
        )[:5]
        summary = SourcePilotSummary(
            source_id=source_id,
            eligible_replicate_group_count=len(groups),
            unordered_pair_comparison_count=sum(group.pair_count for group in groups),
            panel_gene_count=50,
            analysis_scale=scale,
            median_group_spearman=float(np.median(spearman_values)),
            bootstrap_spearman_ci_lower=spearman_interval[0],
            bootstrap_spearman_ci_upper=spearman_interval[1],
            minimum_group_spearman=min(spearman_values),
            maximum_group_spearman=max(spearman_values),
            median_group_pearson=float(np.median([group.pearson for group in groups])),
            median_group_mae=float(np.median([group.mae for group in groups])),
            median_group_rmse=float(np.median(rmse_values)),
            bootstrap_rmse_ci_lower=rmse_interval[0],
            bootstrap_rmse_ci_upper=rmse_interval[1],
            median_gene_absolute_difference=float(np.median(list(gene_differences.values()))),
            maximum_gene_absolute_difference=max(gene_differences.values()),
            highest_difference_genes=highest,
            inferential_claim_authorized=False,
            primary_calibration_eligible=False,
        )
        details = {
            "source_id": source_id,
            "analysis_scale": scale,
            "groups": [
                {
                    "group_id": group.group_id,
                    "pair_count": group.pair_count,
                    "metrics": {
                        "spearman": group.spearman,
                        "pearson": group.pearson,
                        "mae": group.mae,
                        "rmse": group.rmse,
                    },
                    "gene_median_absolute_differences": group.gene_absolute_differences,
                }
                for group in groups
            ],
            "source_gene_median_absolute_differences": gene_differences,
            "highest_difference_genes": highest,
            "exploratory_gene_ranking_only": True,
            "inferential_claim_authorized": False,
            "primary_calibration_eligible": False,
        }
        return summary, details


def _hashed_group_id(source_id: str, group_label: str) -> str:
    digest = hashlib.sha256(f"{source_id}\0{group_label}".encode()).hexdigest()[:16]
    return f"group-{digest}"
