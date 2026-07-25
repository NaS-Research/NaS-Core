import re
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
LITERATURE = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
)
PACKET = LITERATURE / "FOUNDER_REMAINING_SCREENING_PACKET_v1.0.0.md"
CONFIRMATION = LITERATURE / "FOUNDER_REMAINING_SCREENING_CONFIRMATION_v1.0.0.md"
PROGRESS_RECEIPT = LITERATURE / "revised-screening-progress" / "batch-0002.yaml"


def _record_numbers(section: str) -> list[int]:
    return [
        int(match.group(1))
        for match in re.finditer(r"^\| (\d+) \|", section, flags=re.MULTILINE)
    ]


def test_remaining_screening_packet_covers_every_pending_record_once() -> None:
    text = PACKET.read_text(encoding="utf-8")
    inclusion_section, exclusion_tail = text.split(
        "## Recommended exclusions", maxsplit=1
    )
    exclusion_section, _ = exclusion_tail.split("## Founder confirmation", maxsplit=1)

    included = _record_numbers(inclusion_section)
    excluded = _record_numbers(exclusion_section)

    assert len(included) == 17
    assert len(excluded) == 70
    assert sorted(included + excluded) == list(range(1, 88))


def test_remaining_screening_packet_stays_advisory() -> None:
    text = PACKET.read_text(encoding="utf-8")

    assert "Advisory only—founder confirmation required" in text
    assert "No decision in this packet may be represented as founder-confirmed" in text
    assert "17 `include`" in text
    assert "70 `exclude`" in text
    assert "5 author-year candidate links rejected" in text


def test_exact_packet_confirmation_has_complete_verified_receipt() -> None:
    confirmation = CONFIRMATION.read_text(encoding="utf-8")
    receipt = yaml.safe_load(PROGRESS_RECEIPT.read_text(encoding="utf-8"))

    assert (
        "`I confirm the screening packet as written.`"
        in confirmation
    )
    assert (
        "`210a4d8ef80fc90aeee194ad3d3c299c4e70570a9a0bb1804f2ac385224304aa`"
        in confirmation
    )
    assert receipt["progress_id"] == (
        "7b90c37aa7fcab3607b5fde99c6aa97a0a3e440889b0d44727ba4f685863218c"
    )
    assert receipt["screening_status"] == "complete"
    assert receipt["summary"] == {
        "total_record_count": 100,
        "decided_record_count": 100,
        "pending_record_count": 0,
        "included_record_count": 30,
        "excluded_record_count": 70,
        "unclear_record_count": 0,
        "decision_event_count": 100,
        "completion_percent": 100.0,
    }
    assert receipt["ai_decisions_recorded"] == 0
    assert receipt["scientific_conclusions_drawn"] is False
