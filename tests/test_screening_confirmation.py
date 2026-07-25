from datetime import UTC, datetime
from pathlib import Path

import pytest

from nas_core.domain.literature import (
    ScreeningProgressReceipt,
    ScreeningQueueReceipt,
    ScreeningQueueRecord,
)
from nas_core.domain.screening_confirmation import (
    CONFIRMATION_STATEMENT,
    ScreeningConfirmation,
)
from nas_core.ingestion.gdc import sha256
from nas_core.retrieval.screening_confirmation import (
    ScreeningConfirmationError,
    ScreeningConfirmationService,
)


class _ReviewStub:
    def __init__(self, records: list[ScreeningQueueRecord]) -> None:
        self._records = records

    def pending_records(
        self,
        queue_receipt: ScreeningQueueReceipt,
        *,
        progress_receipt: ScreeningProgressReceipt,
    ) -> list[ScreeningQueueRecord]:
        del queue_receipt, progress_receipt
        return self._records


def _records() -> list[ScreeningQueueRecord]:
    return [
        ScreeningQueueRecord(
            screening_id="a" * 64,
            record_key="pmid:1",
            source_ids=["pubmed"],
            pmid="1",
            title="Included method",
        ),
        ScreeningQueueRecord(
            screening_id="b" * 64,
            record_key="europe-pmc:PPR:PPR2",
            source_ids=["europe-pmc"],
            title="Excluded outcome study",
        ),
    ]


def _packet(path: Path) -> bytes:
    body = b"""# Synthetic packet

## Recommended inclusions

| # | Record | Short title | Confidence | Why full text is warranted |
|---:|---|---|---|---|
| 1 | PMID 1 | Included | High | Direct method. |

## Recommended exclusions

| # | Record | Short title | Reason | Rationale |
|---:|---|---|---:|---|
| 2 | PPR2 | Excluded | 3 | Outcome only. |

## Founder confirmation
"""
    path.write_bytes(body)
    return body


def _confirmation(packet: bytes, **updates: object) -> ScreeningConfirmation:
    payload: dict[str, object] = {
        "confirmation_version": "1.0.0",
        "queue_id": "c" * 64,
        "expected_previous_progress_id": "d" * 64,
        "packet_sha256": sha256(packet),
        "reviewer_id": "dalron-j-robertson",
        "reviewer_name": "Dalron J. Robertson",
        "confirmation_statement": CONFIRMATION_STATEMENT,
        "author_year_links_rejected": True,
        "founder_authorized": True,
        "confirmed_at": datetime(2026, 7, 24, tzinfo=UTC),
    }
    payload.update(updates)
    return ScreeningConfirmation.model_validate(payload)


def _service() -> ScreeningConfirmationService:
    return ScreeningConfirmationService(review_service=_ReviewStub(_records()))  # type: ignore[arg-type]


def test_confirmation_builds_exact_typed_batch(tmp_path: Path) -> None:
    packet_path = tmp_path / "packet.md"
    packet = _packet(packet_path)
    queue = ScreeningQueueReceipt.model_construct(queue_id="c" * 64)
    progress = ScreeningProgressReceipt.model_construct(progress_id="d" * 64)

    batch = _service().build_decision_batch(
        queue_receipt=queue,
        progress_receipt=progress,
        packet_path=packet_path,
        confirmation=_confirmation(packet),
    )

    assert batch.expected_previous_progress_id == "d" * 64
    assert [item.screening_id for item in batch.decisions] == ["a" * 64, "b" * 64]
    assert [item.decision for item in batch.decisions] == ["include", "exclude"]
    assert (
        batch.decisions[1].exclusion_reason
        == "no_relevant_discordance_stability_or_classifier_method"
    )


def test_preview_verifies_packet_without_claiming_founder_authority(
    tmp_path: Path,
) -> None:
    packet_path = tmp_path / "packet.md"
    packet = _packet(packet_path)

    preview = _service().preview_packet(
        queue_receipt=ScreeningQueueReceipt.model_construct(queue_id="c" * 64),
        progress_receipt=ScreeningProgressReceipt.model_construct(
            progress_id="d" * 64
        ),
        packet_path=packet_path,
    )

    assert preview.packet_sha256 == sha256(packet)
    assert preview.pending_record_count == 2
    assert preview.proposed_include_count == 1
    assert preview.proposed_exclude_count == 1
    assert preview.founder_authorized is False


def test_confirmation_fails_closed_when_packet_changes(tmp_path: Path) -> None:
    packet_path = tmp_path / "packet.md"
    packet = _packet(packet_path)
    packet_path.write_bytes(packet + b"\nchanged\n")

    with pytest.raises(ScreeningConfirmationError, match="checksum"):
        _service().build_decision_batch(
            queue_receipt=ScreeningQueueReceipt.model_construct(queue_id="c" * 64),
            progress_receipt=ScreeningProgressReceipt.model_construct(
                progress_id="d" * 64
            ),
            packet_path=packet_path,
            confirmation=_confirmation(packet),
        )


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("confirmation_statement", "Looks good.", "statement"),
        ("author_year_links_rejected", False, "author-year"),
        ("founder_authorized", False, "authorization"),
        ("scientific_conclusions_drawn", True, "scientific conclusions"),
    ],
)
def test_confirmation_rejects_incomplete_authority(
    field: str, value: object, message: str, tmp_path: Path
) -> None:
    packet = _packet(tmp_path / "packet.md")

    with pytest.raises(ValueError, match=message):
        _confirmation(packet, **{field: value})


def test_confirmation_rejects_packet_identity_mismatch(tmp_path: Path) -> None:
    packet_path = tmp_path / "packet.md"
    _packet(packet_path)
    packet_path.write_text(
        packet_path.read_text().replace("PPR2", "PPR999"),
        encoding="utf-8",
    )
    confirmation = _confirmation(packet_path.read_bytes())

    with pytest.raises(ScreeningConfirmationError, match="record 2"):
        _service().build_decision_batch(
            queue_receipt=ScreeningQueueReceipt.model_construct(queue_id="c" * 64),
            progress_receipt=ScreeningProgressReceipt.model_construct(
                progress_id="d" * 64
            ),
            packet_path=packet_path,
            confirmation=confirmation,
        )
