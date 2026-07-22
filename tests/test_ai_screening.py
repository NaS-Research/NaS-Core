import json
from datetime import UTC, datetime
from pathlib import Path

import pytest
import yaml

from nas_core.ai.gateway import (
    ModelGatewayError,
    OpenAIScreeningGateway,
    ScreeningGatewayRequest,
    ScreeningGatewayResponse,
)
from nas_core.ai.screening import AIAdvisoryError, AIAdvisoryScreeningService
from nas_core.domain.advisory import (
    AIAdvisoryBatchOutput,
    AIAdvisoryManifest,
    AIAdvisoryPolicy,
    AIAdvisoryReceipt,
    AIModelCall,
)
from nas_core.domain.literature import (
    BibliographicRecord,
    LiteratureSearchReceipt,
    ScreeningQueueReceipt,
)
from nas_core.ingestion.gdc import canonical_json, sha256
from nas_core.retrieval.screening import ScreeningQueueService
from nas_core.storage.object_store import InMemoryObjectStore

ROOT = Path(__file__).parents[1]
STUDY = ROOT / "workflows" / "studies" / "breast_clinical_molecular_discordance"
SEARCH_RECEIPT = STUDY / "literature" / "search_receipt.yaml"
POLICY_PATH = STUDY / "literature" / "AI_SCREENING_POLICY.yaml"
PROMPT_PATH = STUDY / "literature" / "AI_SCREENING_PROMPT.md"
OUTPUT_SCHEMA = ROOT / "workflows" / "ai_screening_output.schema.json"
MANIFEST_SCHEMA = ROOT / "workflows" / "ai_screening_manifest.schema.json"
RECEIPT_SCHEMA = ROOT / "workflows" / "ai_screening_receipt.schema.json"
NOW = datetime(2026, 7, 22, 22, 0, tzinfo=UTC)


class FakeGateway:
    def __init__(self, output: AIAdvisoryBatchOutput) -> None:
        self.output = output
        self.requests: list[ScreeningGatewayRequest] = []

    def screen(self, request: ScreeningGatewayRequest) -> ScreeningGatewayResponse:
        self.requests.append(request)
        return ScreeningGatewayResponse(
            output=self.output,
            model_call=AIModelCall(
                provider="openai",
                model="gpt-5.6-sol",
                response_id="resp_synthetic",
                input_tokens=100,
                output_tokens=25,
            ),
        )


def _fixture() -> tuple[InMemoryObjectStore, ScreeningQueueReceipt, list[str]]:
    records = [
        BibliographicRecord(
            record_key="pmid:ai-1",
            source_ids=["pubmed"],
            title="Synthetic PAM50 stability study",
            abstract=(
                "<p>Primary human breast tumors were evaluated. PAM50 stability was tested.</p>"
            ),
        ),
        BibliographicRecord(
            record_key="pmid:ai-2",
            source_ids=["pubmed"],
            title="Synthetic xenograft treatment study",
            abstract="Only xenograft models were evaluated with a PAM50 label.",
        ),
    ]
    normalized = canonical_json(
        [record.model_dump(mode="json", exclude_none=True) for record in records]
    )
    normalized_key = "literature/NAS-BRCA-002/synthetic-ai/normalized-records.json"
    store = InMemoryObjectStore()
    store.put_bytes(normalized_key, normalized, content_type="application/json")
    payload = yaml.safe_load(SEARCH_RECEIPT.read_text())
    payload.update(
        {
            "unique_record_count": 2,
            "normalized_records_object_key": normalized_key,
            "normalized_records_sha256": sha256(normalized),
            "normalized_records_size_bytes": len(normalized),
        }
    )
    search_receipt = LiteratureSearchReceipt.model_validate(payload)
    manifest = ScreeningQueueService(store=store, clock=lambda: NOW).build(
        search_receipt,
        code_revision="a0346ee",
    )
    queue_object = next(item for item in manifest.artifacts if item.object_key.endswith(".jsonl"))
    receipt = ScreeningQueueReceipt(
        queue_id=manifest.queue_id,
        study_id=manifest.study_id,
        search_execution_id=manifest.search_execution_id,
        algorithm_version=manifest.algorithm_version,
        code_revision=manifest.code_revision,
        created_at=manifest.created_at,
        manifest_object_key=(
            f"literature-screening/{manifest.study_id}/{manifest.search_execution_id}/"
            f"{manifest.queue_id}/manifest.json"
        ),
        manifest_sha256=manifest.manifest_sha256 or "",
        queue_object_key=queue_object.object_key,
        queue_sha256=queue_object.sha256,
        queue_size_bytes=queue_object.size_bytes,
        summary=manifest.summary,
        verified_at=NOW,
        manifest_checksum_verified=True,
        artifact_checksums_verified=True,
        record_count_verified=True,
        screening_status="not_started",
        scientific_conclusions_drawn=False,
    )
    rows = [json.loads(line) for line in store.get_bytes(queue_object.object_key).splitlines()]
    return store, receipt, [row["screening_id"] for row in rows]


def _policy(queue_id: str) -> AIAdvisoryPolicy:
    return AIAdvisoryPolicy(
        policy_version="1.0.0",
        study_id="NAS-BRCA-002",
        queue_id=queue_id,
        status="implementation_locked",
        provider="openai",
        model="gpt-5.6-sol",
        reasoning_effort="medium",
        max_records_per_call=10,
        prompt_path=str(PROMPT_PATH),
        permitted_data_classes=["public_open"],
        provider_store_enabled=False,
        live_execution_authorized=True,
        standard_abuse_monitoring_acknowledged=True,
        zero_data_retention_required=False,
        autonomous_decisions_allowed=False,
        human_review_required=True,
        calibration_required_before_routing=True,
    )


def _output(identifiers: list[str], *, bad_evidence: bool = False) -> AIAdvisoryBatchOutput:
    return AIAdvisoryBatchOutput(
        recommendations=[
            {
                "screening_id": identifiers[0],
                "recommendation": "include",
                "confidence": "high",
                "matched_criteria": ["classification_stability_or_uncertainty"],
                "evidence_sentence_ids": ["A99" if bad_evidence else "A2"],
                "rationale": "The synthetic abstract directly evaluates PAM50 stability.",
                "human_review_required": True,
            },
            {
                "screening_id": identifiers[1],
                "recommendation": "exclude",
                "confidence": "high",
                "matched_criteria": ["molecular_intrinsic_subtype"],
                "exclusion_reason": "nonhuman_or_no_primary_human_tumor_cohort",
                "evidence_sentence_ids": ["A1"],
                "rationale": "The synthetic abstract describes only xenograft models.",
                "human_review_required": True,
            },
        ]
    )


def test_checked_in_ai_screening_contracts() -> None:
    assert json.loads(OUTPUT_SCHEMA.read_text()) == AIAdvisoryBatchOutput.model_json_schema()
    assert json.loads(MANIFEST_SCHEMA.read_text()) == AIAdvisoryManifest.model_json_schema()
    assert json.loads(RECEIPT_SCHEMA.read_text()) == AIAdvisoryReceipt.model_json_schema()
    policy = AIAdvisoryPolicy.model_validate(yaml.safe_load(POLICY_PATH.read_text()))
    assert policy.autonomous_decisions_allowed is False
    assert policy.human_review_required is True
    assert policy.live_execution_authorized is False
    assert PROMPT_PATH.read_text().strip()


def test_ai_advisory_run_is_structured_verified_and_non_authoritative() -> None:
    store, receipt, identifiers = _fixture()
    gateway = FakeGateway(_output(identifiers))
    service = AIAdvisoryScreeningService(store=store, gateway=gateway, clock=lambda: NOW)

    manifest = service.run(
        receipt,
        _policy(receipt.queue_id),
        prompt_text=PROMPT_PATH.read_text(),
        code_revision="f5b94a3",
    )
    verified = service.verify(manifest)

    assert manifest.summary.include_count == 1
    assert manifest.summary.exclude_count == 1
    assert manifest.summary.human_decisions_recorded == 0
    assert manifest.final_decisions_recorded == 0
    assert verified.calibration_status == "required"
    assert verified.autonomous_decisions_allowed is False
    assert verified.scientific_conclusions_drawn is False
    assert len(gateway.requests) == 1
    request = json.loads(gateway.requests[0].input_text)
    assert request["records"][0]["sentences"][1]["id"] == "A1"
    assert "<p>" not in gateway.requests[0].input_text


def test_ai_advisory_rejects_unverifiable_evidence_reference() -> None:
    store, receipt, identifiers = _fixture()
    service = AIAdvisoryScreeningService(
        store=store,
        gateway=FakeGateway(_output(identifiers, bad_evidence=True)),
        clock=lambda: NOW,
    )

    with pytest.raises(AIAdvisoryError, match="unknown evidence"):
        service.run(
            receipt,
            _policy(receipt.queue_id),
            prompt_text=PROMPT_PATH.read_text(),
            code_revision="f5b94a3",
        )


def test_checked_in_policy_blocks_live_provider_execution() -> None:
    store, receipt, identifiers = _fixture()
    policy = AIAdvisoryPolicy.model_validate(yaml.safe_load(POLICY_PATH.read_text()))
    service = AIAdvisoryScreeningService(
        store=store,
        gateway=FakeGateway(_output(identifiers)),
        clock=lambda: NOW,
    )

    with pytest.raises(AIAdvisoryError, match="does not authorize live"):
        service.run(
            receipt,
            policy.model_copy(update={"queue_id": receipt.queue_id}),
            prompt_text=PROMPT_PATH.read_text(),
            code_revision="f5b94a3",
        )


def test_openai_gateway_fails_closed_without_api_key() -> None:
    with pytest.raises(ModelGatewayError, match="OPENAI_API_KEY"):
        OpenAIScreeningGateway(
            api_key=None,
            model="gpt-5.6-sol",
            reasoning_effort="medium",
        )
