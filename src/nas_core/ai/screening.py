"""Governed AI advisory triage over a verified human-screening queue."""

from __future__ import annotations

import html
import json
import re
from collections.abc import Callable
from datetime import UTC, datetime

from pydantic import ValidationError

from nas_core.ai.gateway import ScreeningGatewayRequest, ScreeningModelGateway
from nas_core.domain.advisory import (
    AdvisoryConfidence,
    AIAdvisoryManifest,
    AIAdvisoryPolicy,
    AIAdvisoryReceipt,
    AIAdvisoryRecommendation,
    AIAdvisorySummary,
)
from nas_core.domain.literature import (
    ScreeningDecision,
    ScreeningProgressReceipt,
    ScreeningQueueReceipt,
    ScreeningQueueRecord,
)
from nas_core.domain.snapshots import StoredObject
from nas_core.ingestion.gdc import ImmutableObjectConflictError, canonical_json, sha256
from nas_core.retrieval.review import ScreeningReviewService
from nas_core.storage.object_store import ObjectStore

ALGORITHM_VERSION = "ai-literature-advisory-1.0.0"
JSON_MEDIA_TYPE = "application/json"
JSONL_MEDIA_TYPE = "application/x-ndjson"
_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_HTML_TAG = re.compile(r"<[^>]+>")


class AIAdvisoryError(RuntimeError):
    """Raised when AI advisory provenance or output invariants fail."""


class AIAdvisoryScreeningService:
    def __init__(
        self,
        *,
        store: ObjectStore,
        gateway: ScreeningModelGateway,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._store = store
        self._gateway = gateway
        self._clock = clock or (lambda: datetime.now(UTC))
        self._review = ScreeningReviewService(store=store)

    def run(
        self,
        queue_receipt: ScreeningQueueReceipt,
        policy: AIAdvisoryPolicy,
        *,
        prompt_text: str,
        code_revision: str,
        progress_receipt: ScreeningProgressReceipt | None = None,
    ) -> AIAdvisoryManifest:
        self._validate_inputs(queue_receipt, policy, prompt_text, code_revision)
        batch = self._review.next_batch(
            queue_receipt,
            progress_receipt=progress_receipt,
            batch_size=policy.max_records_per_call,
        )
        if not batch.records:
            raise AIAdvisoryError("no pending records are available for AI advisory review")
        request_payload, evidence_ids = self._request_payload(batch.records)
        request_body = canonical_json(request_payload)
        prompt_sha = sha256(prompt_text.encode("utf-8"))
        policy_sha = sha256(canonical_json(policy.model_dump(mode="json")))
        gateway_response = self._gateway.screen(
            ScreeningGatewayRequest(
                instructions=prompt_text,
                input_text=request_body.decode("utf-8"),
                safety_identifier=f"nas-screening-{sha256(queue_receipt.queue_id.encode())[:24]}",
            )
        )
        if (
            gateway_response.model_call.provider != policy.provider
            or gateway_response.model_call.model != policy.model
        ):
            raise AIAdvisoryError("model gateway response does not match the locked policy")
        recommendations = gateway_response.output.recommendations
        self._validate_recommendations(recommendations, evidence_ids)
        summary = self._summary(recommendations)
        created_at = self._clock()
        identity = {
            "algorithm_version": ALGORITHM_VERSION,
            "code_revision": code_revision,
            "input_sha256": sha256(request_body),
            "policy_sha256": policy_sha,
            "prompt_sha256": prompt_sha,
            "queue_id": queue_receipt.queue_id,
            "response_id": gateway_response.model_call.response_id,
        }
        run_id = sha256(canonical_json(identity))
        prefix = f"ai-screening-advisory/{queue_receipt.queue_id}/{run_id}"
        recommendations_body = b"".join(
            canonical_json(item.model_dump(mode="json", exclude_none=True)) + b"\n"
            for item in recommendations
        )
        summary_body = canonical_json(summary.model_dump(mode="json"))
        artifacts: list[StoredObject] = []
        for name, body, media_type in (
            ("request.json", request_body, JSON_MEDIA_TYPE),
            ("recommendations.jsonl", recommendations_body, JSONL_MEDIA_TYPE),
            ("summary.json", summary_body, JSON_MEDIA_TYPE),
        ):
            key = f"{prefix}/{name}"
            self._put_immutable(key, body, content_type=media_type)
            artifacts.append(
                StoredObject(
                    object_key=key,
                    media_type=media_type,
                    size_bytes=len(body),
                    sha256=sha256(body),
                )
            )
        manifest = AIAdvisoryManifest(
            advisory_run_id=run_id,
            queue_id=queue_receipt.queue_id,
            based_on_progress_id=(progress_receipt.progress_id if progress_receipt else None),
            policy_version=policy.policy_version,
            policy_sha256=policy_sha,
            prompt_sha256=prompt_sha,
            input_sha256=sha256(request_body),
            code_revision=code_revision,
            created_at=created_at,
            model_call=gateway_response.model_call,
            artifacts=artifacts,
            summary=summary,
            autonomous_decisions_allowed=False,
            final_decisions_recorded=0,
            scientific_conclusions_drawn=False,
        )
        unhashed = canonical_json(manifest.model_dump(mode="json", exclude_none=True))
        manifest = manifest.model_copy(update={"manifest_sha256": sha256(unhashed)})
        self._put_immutable(
            self.manifest_object_key(manifest),
            canonical_json(manifest.model_dump(mode="json", exclude_none=True)),
            content_type=JSON_MEDIA_TYPE,
        )
        return manifest

    def verify(self, manifest: AIAdvisoryManifest) -> AIAdvisoryReceipt:
        manifest_key = self.manifest_object_key(manifest)
        stored = self._store.get_bytes(manifest_key)
        try:
            reloaded = AIAdvisoryManifest.model_validate(json.loads(stored))
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as error:
            raise AIAdvisoryError("stored AI advisory manifest is invalid") from error
        if reloaded != manifest:
            raise AIAdvisoryError("stored AI advisory manifest differs from supplied manifest")
        expected_hash = sha256(
            canonical_json(
                manifest.model_copy(update={"manifest_sha256": None}).model_dump(
                    mode="json", exclude_none=True
                )
            )
        )
        if manifest.manifest_sha256 != expected_hash:
            raise AIAdvisoryError("AI advisory manifest checksum is invalid")
        request_object = self._artifact(manifest, "request.json")
        recommendations_object = self._artifact(manifest, "recommendations.jsonl")
        summary_object = self._artifact(manifest, "summary.json")
        request_body = self._verified_object(request_object)
        recommendations_body = self._verified_object(recommendations_object)
        summary_body = self._verified_object(summary_object)
        if sha256(request_body) != manifest.input_sha256:
            raise AIAdvisoryError("AI advisory request does not match manifest input")
        request_payload = json.loads(request_body)
        evidence_ids = self._evidence_index(request_payload)
        recommendations = self._parse_recommendations(recommendations_body)
        self._validate_recommendations(recommendations, evidence_ids)
        derived_summary = self._summary(recommendations)
        try:
            stored_summary = AIAdvisorySummary.model_validate(json.loads(summary_body))
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as error:
            raise AIAdvisoryError("stored AI advisory summary is invalid") from error
        if stored_summary != derived_summary or manifest.summary != derived_summary:
            raise AIAdvisoryError("AI advisory counts do not reconcile")
        return AIAdvisoryReceipt(
            advisory_run_id=manifest.advisory_run_id,
            queue_id=manifest.queue_id,
            based_on_progress_id=manifest.based_on_progress_id,
            policy_version=manifest.policy_version,
            provider=manifest.model_call.provider,
            model=manifest.model_call.model,
            code_revision=manifest.code_revision,
            created_at=manifest.created_at,
            manifest_object_key=manifest_key,
            manifest_sha256=expected_hash,
            summary=derived_summary,
            verified_at=self._clock(),
            manifest_checksum_verified=True,
            artifact_checksums_verified=True,
            evidence_references_verified=True,
            count_invariants_verified=True,
            calibration_status="required",
            autonomous_decisions_allowed=False,
            final_decisions_recorded=0,
            scientific_conclusions_drawn=False,
        )

    @staticmethod
    def manifest_object_key(manifest: AIAdvisoryManifest) -> str:
        return f"ai-screening-advisory/{manifest.queue_id}/{manifest.advisory_run_id}/manifest.json"

    @staticmethod
    def _validate_inputs(
        receipt: ScreeningQueueReceipt,
        policy: AIAdvisoryPolicy,
        prompt_text: str,
        code_revision: str,
    ) -> None:
        if receipt.queue_id != policy.queue_id or receipt.study_id != policy.study_id:
            raise AIAdvisoryError("AI advisory policy does not match the screening queue")
        if not re.fullmatch(r"[a-f0-9]{7,40}", code_revision):
            raise AIAdvisoryError("code revision must be a 7-to-40 character Git SHA")
        if not prompt_text.strip():
            raise AIAdvisoryError("AI advisory prompt cannot be empty")
        if not policy.live_execution_authorized:
            raise AIAdvisoryError("AI advisory policy does not authorize live provider execution")

    @classmethod
    def _request_payload(
        cls,
        records: list[ScreeningQueueRecord],
    ) -> tuple[dict[str, object], dict[str, set[str]]]:
        rendered: list[dict[str, object]] = []
        evidence_ids: dict[str, set[str]] = {}
        for record in records:
            sentences = [{"id": "T1", "text": cls._clean(record.title)}]
            for index, sentence in enumerate(cls._sentences(record.abstract), start=1):
                sentences.append({"id": f"A{index}", "text": sentence})
            evidence_ids[record.screening_id] = {str(item["id"]) for item in sentences}
            rendered.append({"screening_id": record.screening_id, "sentences": sentences})
        return {"records": rendered}, evidence_ids

    @classmethod
    def _sentences(cls, value: str | None) -> list[str]:
        if not value:
            return []
        cleaned = cls._clean(value)
        return [part.strip() for part in _SENTENCE_SPLIT.split(cleaned) if part.strip()]

    @staticmethod
    def _clean(value: str) -> str:
        return " ".join(html.unescape(_HTML_TAG.sub(" ", value)).split())

    @staticmethod
    def _validate_recommendations(
        recommendations: list[AIAdvisoryRecommendation],
        evidence_ids: dict[str, set[str]],
    ) -> None:
        actual = {item.screening_id for item in recommendations}
        if actual != set(evidence_ids):
            raise AIAdvisoryError("AI must return exactly one recommendation per requested record")
        for item in recommendations:
            if not set(item.evidence_sentence_ids).issubset(evidence_ids[item.screening_id]):
                raise AIAdvisoryError("AI recommendation references unknown evidence sentences")

    @staticmethod
    def _summary(recommendations: list[AIAdvisoryRecommendation]) -> AIAdvisorySummary:
        return AIAdvisorySummary(
            requested_record_count=len(recommendations),
            recommendation_count=len(recommendations),
            include_count=sum(
                item.recommendation is ScreeningDecision.INCLUDE for item in recommendations
            ),
            exclude_count=sum(
                item.recommendation is ScreeningDecision.EXCLUDE for item in recommendations
            ),
            unclear_count=sum(
                item.recommendation is ScreeningDecision.UNCLEAR for item in recommendations
            ),
            high_confidence_count=sum(
                item.confidence is AdvisoryConfidence.HIGH for item in recommendations
            ),
            moderate_confidence_count=sum(
                item.confidence is AdvisoryConfidence.MODERATE for item in recommendations
            ),
            low_confidence_count=sum(
                item.confidence is AdvisoryConfidence.LOW for item in recommendations
            ),
            human_decisions_recorded=0,
        )

    @staticmethod
    def _evidence_index(payload: object) -> dict[str, set[str]]:
        if not isinstance(payload, dict) or not isinstance(payload.get("records"), list):
            raise AIAdvisoryError("stored AI request has an invalid record structure")
        evidence: dict[str, set[str]] = {}
        for record in payload["records"]:
            if not isinstance(record, dict) or not isinstance(record.get("sentences"), list):
                raise AIAdvisoryError("stored AI request has invalid sentence evidence")
            screening_id = record.get("screening_id")
            if not isinstance(screening_id, str):
                raise AIAdvisoryError("stored AI request has an invalid screening ID")
            identifiers = {
                sentence.get("id")
                for sentence in record["sentences"]
                if isinstance(sentence, dict) and isinstance(sentence.get("id"), str)
            }
            evidence[screening_id] = {str(identifier) for identifier in identifiers}
        return evidence

    @staticmethod
    def _parse_recommendations(body: bytes) -> list[AIAdvisoryRecommendation]:
        try:
            return [
                AIAdvisoryRecommendation.model_validate(json.loads(line))
                for line in body.splitlines()
            ]
        except (json.JSONDecodeError, UnicodeDecodeError, ValidationError) as error:
            raise AIAdvisoryError("stored AI recommendations are invalid") from error

    @staticmethod
    def _artifact(manifest: AIAdvisoryManifest, suffix: str) -> StoredObject:
        matches = [item for item in manifest.artifacts if item.object_key.endswith(suffix)]
        if len(matches) != 1:
            raise AIAdvisoryError(f"AI advisory manifest must contain one {suffix}")
        return matches[0]

    def _verified_object(self, artifact: StoredObject) -> bytes:
        body = self._store.get_bytes(artifact.object_key)
        if len(body) != artifact.size_bytes or sha256(body) != artifact.sha256:
            raise AIAdvisoryError(
                f"AI advisory artifact failed verification: {artifact.object_key}"
            )
        return body

    def _put_immutable(self, key: str, body: bytes, *, content_type: str) -> None:
        if self._store.exists(key):
            if self._store.get_bytes(key) != body:
                raise ImmutableObjectConflictError(f"immutable object conflict: {key}")
            return
        self._store.put_bytes(key, body, content_type=content_type)
