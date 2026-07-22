"""Deterministic TCGA clinical cohort construction without outcome modeling."""

from __future__ import annotations

import csv
import io
import json
import math
import re
import statistics
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import cast

from nas_core.domain.cohorts import (
    CohortArtifact,
    CohortBuildManifest,
    CohortExclusionReason,
    CohortQASummary,
    SelectionDescriptives,
    SnapshotReceipt,
)
from nas_core.domain.research import AnalysisPlan, PlanStatus
from nas_core.domain.snapshots import DatasetSnapshot, StoredObject
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.storage.object_store import ObjectStore

ALGORITHM_VERSION = "tcga-brca-cohort-1.0.0"
CSV_MEDIA_TYPE = "text/csv"
JSON_MEDIA_TYPE = "application/json"
STAGE_PATTERN = re.compile(r"^stage\s+(iv|iii|ii|i)(?:[a-c]\d*)?$", re.IGNORECASE)


class CohortBuildError(RuntimeError):
    """Raised when immutable inputs or cohort invariants are invalid."""


@dataclass(frozen=True, slots=True)
class CohortRow:
    case_id: str
    submitter_id: str
    diagnosis_id: str
    pathologic_stage: str
    advanced_pathologic_stage: int
    ajcc_staging_system_edition: str
    age_at_diagnosis_days: float
    age_at_diagnosis_years: float
    vital_status: str
    duration_days: float
    event: int
    survival_time_source: str


@dataclass(frozen=True, slots=True)
class Exclusion:
    case_id: str
    reason: CohortExclusionReason


class CohortBuildService:
    """Build and persist a governed analysis-ready cohort from one snapshot."""

    def __init__(
        self,
        *,
        store: ObjectStore,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._clock = clock or (lambda: datetime.now(UTC))

    def build(
        self,
        plan: AnalysisPlan,
        receipt: SnapshotReceipt,
        *,
        code_revision: str,
    ) -> CohortBuildManifest:
        self._validate_bindings(plan, receipt, code_revision)
        snapshot = self._load_snapshot(receipt)
        cases = self._load_cases(snapshot)

        missingness = self._missingness_counts(cases, plan.data_requirements[0].fields)
        rows: list[CohortRow] = []
        exclusions: list[Exclusion] = []
        normalization_counts: Counter[str] = Counter()
        for case in sorted(cases, key=self._case_id):
            result = self._derive_case(case, normalization_counts)
            if isinstance(result, Exclusion):
                exclusions.append(result)
            else:
                rows.append(result)

        exclusion_counts = Counter(exclusion.reason.value for exclusion in exclusions)
        excluded_ids = {exclusion.case_id for exclusion in exclusions}
        qa = CohortQASummary(
            study_id=plan.study_id,
            snapshot_id=receipt.snapshot_id,
            input_case_count=len(cases),
            included_case_count=len(rows),
            excluded_case_count=len(exclusions),
            exclusion_counts=dict(sorted(exclusion_counts.items())),
            missingness_counts=dict(sorted(missingness.items())),
            stage_normalization_counts=dict(sorted(normalization_counts.items())),
            included_descriptives=self._included_descriptives(rows),
            excluded_descriptives=self._excluded_descriptives(
                [case for case in cases if self._case_id(case) in excluded_ids]
            ),
        )

        built_at = self._clock()
        identity = {
            "algorithm_version": ALGORITHM_VERSION,
            "built_at": built_at.isoformat(),
            "code_revision": code_revision,
            "protocol_version": plan.protocol_version,
            "snapshot_id": receipt.snapshot_id,
            "snapshot_manifest_sha256": receipt.manifest_sha256,
            "study_id": plan.study_id,
        }
        build_id = sha256(canonical_json(identity))
        prefix = (
            f"analysis-ready/{receipt.source_id}/{plan.study_id}/{receipt.snapshot_id}/{build_id}"
        )

        cohort_bytes = self._cohort_csv(rows)
        exclusions_bytes = self._exclusions_csv(exclusions)
        qa_bytes = canonical_json(qa.model_dump(mode="json"))
        artifacts: list[CohortArtifact] = []
        for name, body, media_type in (
            ("cohort.csv", cohort_bytes, CSV_MEDIA_TYPE),
            ("exclusions.csv", exclusions_bytes, CSV_MEDIA_TYPE),
            ("qa-summary.json", qa_bytes, JSON_MEDIA_TYPE),
        ):
            key = f"{prefix}/{name}"
            self._put_immutable(key, body, content_type=media_type)
            artifacts.append(
                CohortArtifact(
                    object_key=key,
                    media_type=media_type,
                    size_bytes=len(body),
                    sha256=sha256(body),
                )
            )

        manifest = CohortBuildManifest(
            build_id=build_id,
            study_id=plan.study_id,
            protocol_version=plan.protocol_version,
            protocol_tag=receipt.protocol_tag,
            snapshot_id=receipt.snapshot_id,
            snapshot_manifest_sha256=receipt.manifest_sha256,
            algorithm_version=ALGORITHM_VERSION,
            code_revision=code_revision,
            built_at=built_at,
            input_case_count=len(cases),
            included_case_count=len(rows),
            excluded_case_count=len(exclusions),
            artifacts=artifacts,
        )
        unhashed = canonical_json(manifest.model_dump(mode="json", exclude_none=True))
        manifest = manifest.model_copy(update={"manifest_sha256": sha256(unhashed)})
        self._put_immutable(
            f"{prefix}/manifest.json",
            canonical_json(manifest.model_dump(mode="json", exclude_none=True)),
            content_type=JSON_MEDIA_TYPE,
        )
        return manifest

    @staticmethod
    def _validate_bindings(
        plan: AnalysisPlan,
        receipt: SnapshotReceipt,
        code_revision: str,
    ) -> None:
        if plan.status is not PlanStatus.PREREGISTERED:
            raise CohortBuildError("cohort construction requires a preregistered plan")
        if plan.study_id != receipt.study_id or plan.protocol_version != receipt.protocol_version:
            raise CohortBuildError("plan and snapshot receipt do not identify the same protocol")
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise CohortBuildError("code revision must be a 7-to-40 character Git SHA")

    def _load_snapshot(self, receipt: SnapshotReceipt) -> DatasetSnapshot:
        manifest_bytes = self._store.get_bytes(receipt.manifest_object_key)
        try:
            payload = json.loads(manifest_bytes)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CohortBuildError("snapshot manifest is not valid JSON") from error
        snapshot = DatasetSnapshot.model_validate(payload)
        recorded_hash = snapshot.manifest_sha256
        unhashed = snapshot.model_dump(mode="json", exclude_none=True)
        unhashed.pop("manifest_sha256", None)
        actual_hash = sha256(canonical_json(unhashed))
        if recorded_hash != actual_hash or actual_hash != receipt.manifest_sha256:
            raise CohortBuildError("snapshot manifest checksum does not match the receipt")
        if snapshot.snapshot_id != receipt.snapshot_id:
            raise CohortBuildError("snapshot manifest ID does not match the receipt")
        return snapshot

    def _load_cases(self, snapshot: DatasetSnapshot) -> list[dict[str, object]]:
        page_objects = sorted(
            (obj for obj in snapshot.objects if "/pages/" in obj.object_key),
            key=lambda obj: obj.object_key,
        )
        if not page_objects:
            raise CohortBuildError("snapshot has no case pages")
        cases: list[dict[str, object]] = []
        for page_object in page_objects:
            cases.extend(self._load_page(page_object))
        case_ids = [self._case_id(case) for case in cases]
        if len(case_ids) != len(set(case_ids)):
            raise CohortBuildError("snapshot contains duplicate case IDs")
        if len(cases) != snapshot.record_count:
            raise CohortBuildError("snapshot case count does not match its manifest")
        return cases

    def _load_page(self, page_object: StoredObject) -> list[dict[str, object]]:
        body = self._store.get_bytes(page_object.object_key)
        if sha256(body) != page_object.sha256:
            raise CohortBuildError(f"snapshot page checksum mismatch: {page_object.object_key}")
        try:
            payload = json.loads(body)
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise CohortBuildError("snapshot page is not valid JSON") from error
        data = payload.get("data") if isinstance(payload, dict) else None
        hits = data.get("hits") if isinstance(data, dict) else None
        if not isinstance(hits, list) or any(not isinstance(hit, dict) for hit in hits):
            raise CohortBuildError("snapshot page does not contain object hits")
        typed_hits = cast(list[dict[str, object]], hits)
        actual_ids = [self._case_id(hit) for hit in typed_hits]
        if actual_ids != page_object.record_ids:
            raise CohortBuildError("snapshot page IDs do not match the manifest")
        return typed_hits

    @staticmethod
    def _case_id(case: dict[str, object]) -> str:
        case_id = case.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            raise CohortBuildError("case is missing a stable case_id")
        return case_id

    def _derive_case(
        self,
        case: dict[str, object],
        normalization_counts: Counter[str],
    ) -> CohortRow | Exclusion:
        case_id = self._case_id(case)
        index_date = case.get("index_date")
        if not isinstance(index_date, str) or index_date.casefold() != "diagnosis":
            return Exclusion(case_id, CohortExclusionReason.INVALID_INDEX_DATE)

        diagnoses = self._object_list(case.get("diagnoses"))
        primary = [item for item in diagnoses if item.get("diagnosis_is_primary_disease") is True]
        if not primary:
            return Exclusion(case_id, CohortExclusionReason.NO_PRIMARY_DIAGNOSIS)

        staged: list[tuple[dict[str, object], str]] = []
        for item in primary:
            normalized_stage = self._normalize_stage(item.get("ajcc_pathologic_stage"))
            if normalized_stage is not None:
                staged.append((item, normalized_stage))
        if not staged:
            return Exclusion(case_id, CohortExclusionReason.INVALID_PATHOLOGIC_STAGE)

        identified = [
            (item, stage)
            for item, stage in staged
            if isinstance(item.get("diagnosis_id"), str) and item.get("diagnosis_id")
        ]
        if not identified:
            return Exclusion(case_id, CohortExclusionReason.MISSING_DIAGNOSIS_ID)

        aged: list[tuple[dict[str, object], str, float]] = []
        saw_underage = False
        for diagnosis, stage in identified:
            age_days = self._number(diagnosis.get("age_at_diagnosis"))
            if age_days is None or age_days < 0:
                continue
            if age_days / 365.25 < 18:
                saw_underage = True
                continue
            aged.append((diagnosis, stage, age_days))
        if not aged:
            reason = (
                CohortExclusionReason.UNDERAGE
                if saw_underage
                else CohortExclusionReason.MISSING_OR_INVALID_AGE
            )
            return Exclusion(case_id, reason)

        diagnosis, stage, age_days = min(aged, key=self._diagnosis_sort_key)
        diagnosis_id = cast(str, diagnosis["diagnosis_id"])
        raw_stage = cast(str, diagnosis["ajcc_pathologic_stage"])
        normalization_counts[f"{raw_stage} -> {stage}"] += 1

        demographic = case.get("demographic")
        if not isinstance(demographic, dict):
            return Exclusion(case_id, CohortExclusionReason.INVALID_VITAL_STATUS)
        vital_raw = demographic.get("vital_status")
        if not isinstance(vital_raw, str) or vital_raw.casefold() not in {"alive", "dead"}:
            return Exclusion(case_id, CohortExclusionReason.INVALID_VITAL_STATUS)
        vital_status = vital_raw.casefold()

        if vital_status == "dead":
            duration = self._number(demographic.get("days_to_death"))
            if duration is None or duration <= 0:
                return Exclusion(case_id, CohortExclusionReason.INVALID_SURVIVAL_TIME)
            event = 1
            time_source = "demographic.days_to_death"
        else:
            candidates: list[tuple[float, str]] = []
            diagnosis_follow_up = self._number(diagnosis.get("days_to_last_follow_up"))
            if diagnosis_follow_up is not None and diagnosis_follow_up > 0:
                candidates.append((diagnosis_follow_up, "diagnoses.days_to_last_follow_up"))
            for follow_up in self._object_list(case.get("follow_ups")):
                value = self._number(follow_up.get("days_to_follow_up"))
                if value is not None and value > 0:
                    candidates.append((value, "follow_ups.days_to_follow_up"))
            if not candidates:
                return Exclusion(case_id, CohortExclusionReason.INVALID_SURVIVAL_TIME)
            duration, time_source = max(candidates, key=lambda item: (item[0], item[1]))
            event = 0

        submitter_id = case.get("submitter_id")
        edition = diagnosis.get("ajcc_staging_system_edition")
        return CohortRow(
            case_id=case_id,
            submitter_id=submitter_id if isinstance(submitter_id, str) else "",
            diagnosis_id=diagnosis_id,
            pathologic_stage=stage,
            advanced_pathologic_stage=1 if stage in {"III", "IV"} else 0,
            ajcc_staging_system_edition=edition if isinstance(edition, str) else "",
            age_at_diagnosis_days=age_days,
            age_at_diagnosis_years=age_days / 365.25,
            vital_status=vital_status,
            duration_days=duration,
            event=event,
            survival_time_source=time_source,
        )

    @staticmethod
    def _diagnosis_sort_key(item: tuple[dict[str, object], str, float]) -> tuple[int, float, str]:
        diagnosis = item[0]
        days = CohortBuildService._number(diagnosis.get("days_to_diagnosis"))
        diagnosis_id = cast(str, diagnosis["diagnosis_id"])
        return (1, math.inf, diagnosis_id) if days is None else (0, abs(days), diagnosis_id)

    @staticmethod
    def _normalize_stage(value: object) -> str | None:
        if not isinstance(value, str):
            return None
        match = STAGE_PATTERN.fullmatch(value.strip())
        return match.group(1).upper() if match else None

    @staticmethod
    def _number(value: object) -> float | None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return None
        number = float(value)
        return number if math.isfinite(number) else None

    @staticmethod
    def _object_list(value: object) -> list[dict[str, object]]:
        if not isinstance(value, list):
            return []
        return [cast(dict[str, object], item) for item in value if isinstance(item, dict)]

    def _missingness_counts(
        self,
        cases: list[dict[str, object]],
        required_fields: list[str],
    ) -> Counter[str]:
        counts: Counter[str] = Counter({field: 0 for field in required_fields})
        for case in cases:
            for field in required_fields:
                if not self._field_present(case, field):
                    counts[field] += 1
        return counts

    def _field_present(self, case: dict[str, object], field: str) -> bool:
        parts = field.split(".")
        if len(parts) == 1:
            return self._present(case.get(field))
        parent, child = parts[0], ".".join(parts[1:])
        if parent == "demographic":
            demographic = case.get(parent)
            return isinstance(demographic, dict) and self._present(demographic.get(child))
        if parent in {"diagnoses", "follow_ups"}:
            return any(
                self._present(item.get(child)) for item in self._object_list(case.get(parent))
            )
        return False

    @staticmethod
    def _present(value: object) -> bool:
        return value is not None and value != ""

    def _included_descriptives(self, rows: list[CohortRow]) -> SelectionDescriptives:
        return self._selection_descriptives(
            ages=[row.age_at_diagnosis_years for row in rows],
            vital_statuses=[row.vital_status for row in rows],
            case_count=len(rows),
        )

    def _excluded_descriptives(
        self,
        cases: list[dict[str, object]],
    ) -> SelectionDescriptives:
        ages: list[float] = []
        vital_statuses: list[str] = []
        for case in cases:
            demographic = case.get("demographic")
            vital = demographic.get("vital_status") if isinstance(demographic, dict) else None
            vital_statuses.append(vital.casefold() if isinstance(vital, str) else "")
            primary = [
                item
                for item in self._object_list(case.get("diagnoses"))
                if item.get("diagnosis_is_primary_disease") is True
            ]
            age_values = [
                age
                for item in primary
                if (age := self._number(item.get("age_at_diagnosis"))) is not None and age >= 0
            ]
            if age_values:
                ages.append(min(age_values) / 365.25)
        return self._selection_descriptives(
            ages=ages,
            vital_statuses=vital_statuses,
            case_count=len(cases),
        )

    @staticmethod
    def _selection_descriptives(
        *,
        ages: list[float],
        vital_statuses: list[str],
        case_count: int,
    ) -> SelectionDescriptives:
        return SelectionDescriptives(
            case_count=case_count,
            age_available_count=len(ages),
            mean_age_years=sum(ages) / len(ages) if ages else None,
            median_age_years=statistics.median(ages) if ages else None,
            vital_alive_count=sum(value == "alive" for value in vital_statuses),
            vital_dead_count=sum(value == "dead" for value in vital_statuses),
            vital_other_or_missing_count=sum(
                value not in {"alive", "dead"} for value in vital_statuses
            ),
        )

    @staticmethod
    def _format_number(value: float) -> str:
        return format(value, ".12g")

    def _cohort_csv(self, rows: list[CohortRow]) -> bytes:
        output = io.StringIO(newline="")
        fieldnames = list(CohortRow.__dataclass_fields__)
        writer = csv.DictWriter(output, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            payload = {
                "case_id": row.case_id,
                "submitter_id": row.submitter_id,
                "diagnosis_id": row.diagnosis_id,
                "pathologic_stage": row.pathologic_stage,
                "advanced_pathologic_stage": row.advanced_pathologic_stage,
                "ajcc_staging_system_edition": row.ajcc_staging_system_edition,
                "age_at_diagnosis_days": self._format_number(row.age_at_diagnosis_days),
                "age_at_diagnosis_years": self._format_number(row.age_at_diagnosis_years),
                "vital_status": row.vital_status,
                "duration_days": self._format_number(row.duration_days),
                "event": row.event,
                "survival_time_source": row.survival_time_source,
            }
            writer.writerow(payload)
        return output.getvalue().encode("utf-8")

    @staticmethod
    def _exclusions_csv(exclusions: list[Exclusion]) -> bytes:
        output = io.StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(("case_id", "reason"))
        for exclusion in exclusions:
            writer.writerow((exclusion.case_id, exclusion.reason.value))
        return output.getvalue().encode("utf-8")

    def _put_immutable(self, key: str, data: bytes, *, content_type: str) -> None:
        if self._store.exists(key):
            if self._store.get_bytes(key) != data:
                raise CohortBuildError(f"immutable cohort-object conflict: {key}")
            return
        self._store.put_bytes(key, data, content_type=content_type)
