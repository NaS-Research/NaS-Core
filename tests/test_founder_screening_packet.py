import re
from pathlib import Path

ROOT = Path(__file__).parents[1]
PACKET = (
    ROOT
    / "workflows"
    / "studies"
    / "breast_clinical_molecular_discordance"
    / "literature"
    / "FOUNDER_REMAINING_SCREENING_PACKET_v1.0.0.md"
)


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
