import csv
import hashlib
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
FIRST_APPENDIX = LITERATURE / "FOUNDER_CITATION_PASS_0002_APPENDIX_v1.0.0.csv"
FIRST_PACKET = LITERATURE / "FOUNDER_CITATION_PASS_0002_PACKET_v1.0.0.md"
SECOND_APPENDIX = (
    LITERATURE / "FOUNDER_CITATION_PASS_0002_ADJUDICATION_APPENDIX_v1.0.0.csv"
)
SECOND_PACKET = (
    LITERATURE / "FOUNDER_CITATION_PASS_0002_ADJUDICATION_PACKET_v1.0.0.md"
)
COMBINED_REVIEW = LITERATURE / "FOUNDER_CITATION_PASS_0002_COMBINED_REVIEW_v1.0.0.md"
FIRST_RECEIPT = LITERATURE / "citation-chain" / "pass-0002-founder-packet.yaml"
SECOND_RECEIPT = (
    LITERATURE / "citation-chain" / "pass-0002-adjudication-packet.yaml"
)


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pass2_combined_packet_covers_every_candidate_once() -> None:
    first = _rows(FIRST_APPENDIX)
    second = _rows(SECOND_APPENDIX)
    first_decided = [row for row in first if row["recommendation"] != "unclear"]

    assert len(first) == 2479
    assert len(first_decided) == 2379
    assert len(second) == 100
    combined = first_decided + second
    assert len(combined) == 2479
    assert len({row["record_key"] for row in combined}) == 2479
    assert sum(row["recommendation"] == "include" for row in combined) == 9
    assert sum(row["recommendation"] == "exclude" for row in combined) == 2470
    assert all(row["recommendation"] != "unclear" for row in combined)
    assert all(row["founder_decision_recorded"] == "false" for row in combined)


def test_pass2_review_binds_both_verified_packet_pairs() -> None:
    text = COMBINED_REVIEW.read_text(encoding="utf-8")
    first_receipt = yaml.safe_load(FIRST_RECEIPT.read_text(encoding="utf-8"))
    second_receipt = yaml.safe_load(SECOND_RECEIPT.read_text(encoding="utf-8"))

    assert first_receipt["appendix_sha256"] == _sha256(FIRST_APPENDIX)
    assert first_receipt["packet_sha256"] == _sha256(FIRST_PACKET)
    assert second_receipt["appendix_sha256"] == _sha256(SECOND_APPENDIX)
    assert second_receipt["packet_sha256"] == _sha256(SECOND_PACKET)
    for receipt in (first_receipt, second_receipt):
        assert receipt["packet_sha256"] in text
        assert receipt["appendix_sha256"] in text
        assert receipt["final_screening_decisions_recorded"] == 0
    assert "# Founder Citation Screening Packet — Pass 2" in FIRST_PACKET.read_text()
    assert "# Founder Citation Screening Packet — Pass 2" in SECOND_PACKET.read_text()
    assert "Unique candidate records: 2,479" in text
    assert "Proposed includes: 9" in text
    assert "Proposed excludes: 2,470" in text
    assert (
        "`I confirm both checksum-bound citation pass 2 packets as written.`"
        in text
    )
