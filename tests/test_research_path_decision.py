from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).parents[1]
PACKET = (
    ROOT
    / "workflows/studies/breast_clinical_molecular_discordance/reviews"
    / "RESEARCH_PATH_DECISION_PACKET_v1.0.0.yaml"
)


def _packet() -> dict[str, Any]:
    return cast(dict[str, Any], yaml.safe_load(PACKET.read_text(encoding="utf-8")))


def test_research_path_packet_preserves_three_distinct_dispositions() -> None:
    packet = _packet()
    assert packet["current_path"]["path_id"] == "PATH-A"
    assert packet["current_path"]["purpose_preserved"] is True
    assert packet["alternative_path"]["path_id"] == "PATH-B"
    assert packet["alternative_path"]["material_scope_change"] is True
    assert packet["nonrecommended_path"]["path_id"] == "PATH-C"
    assert packet["nonrecommended_path"]["scientifically_valid"] is False


def test_research_path_packet_grants_no_authority() -> None:
    packet = _packet()
    for field in (
        "external_contact_authorized",
        "scope_change_authorized",
        "spending_authorized",
        "procurement_authorized",
        "specimen_acquisition_authorized",
        "study_execution_authorized",
        "publication_authorized",
    ):
        assert packet[field] is False
    assert packet["final_human_review_preserved"] is True
