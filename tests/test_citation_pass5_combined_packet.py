import csv
import hashlib
from pathlib import Path

import yaml

ROOT = Path(__file__).parents[1]
LITERATURE = ROOT / "workflows" / "studies" / "breast_clinical_molecular_discordance" / "literature"
FIRST_APPENDIX = LITERATURE / "FOUNDER_CITATION_PASS_0005_APPENDIX_v1.0.0.csv"
SECOND_APPENDIX = LITERATURE / "FOUNDER_CITATION_PASS_0005_ADJUDICATION_APPENDIX_v1.0.0.csv"
FIRST_PACKET = LITERATURE / "FOUNDER_CITATION_PASS_0005_PACKET_v1.0.0.md"
SECOND_PACKET = LITERATURE / "FOUNDER_CITATION_PASS_0005_ADJUDICATION_PACKET_v1.0.0.md"
FIRST_RECEIPT = LITERATURE / "citation-chain" / "pass-0005-founder-packet.yaml"
SECOND_RECEIPT = LITERATURE / "citation-chain" / "pass-0005-adjudication-packet.yaml"
COMBINED = LITERATURE / "FOUNDER_CITATION_PASS_0005_COMBINED_REVIEW_v1.0.0.md"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_pass5_packet_has_complete_nonoverlapping_coverage() -> None:
    first = _rows(FIRST_APPENDIX)
    second = _rows(SECOND_APPENDIX)
    decided = [row for row in first if row["recommendation"] != "unclear"] + second

    assert len(first) == 99
    assert len(second) == 5
    assert len(decided) == 99
    assert len({row["record_key"] for row in decided}) == 99
    assert sum(row["recommendation"] == "include" for row in decided) == 1
    assert sum(row["recommendation"] == "exclude" for row in decided) == 98
    assert all(row["founder_decision_recorded"] == "false" for row in decided)


def test_pass5_combined_review_binds_both_packet_pairs() -> None:
    text = COMBINED.read_text(encoding="utf-8")
    first = yaml.safe_load(FIRST_RECEIPT.read_text())
    second = yaml.safe_load(SECOND_RECEIPT.read_text())

    assert first["packet_sha256"] == _sha(FIRST_PACKET)
    assert first["appendix_sha256"] == _sha(FIRST_APPENDIX)
    assert second["packet_sha256"] == _sha(SECOND_PACKET)
    assert second["appendix_sha256"] == _sha(SECOND_APPENDIX)
    for receipt in (first, second):
        assert receipt["packet_sha256"] in text
        assert receipt["appendix_sha256"] in text
    assert "`I confirm both checksum-bound citation pass 5 packets as written.`" in text
