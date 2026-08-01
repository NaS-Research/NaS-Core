from pathlib import Path
from typing import Any, cast

import yaml

ROOT = Path(__file__).parents[1]
REVIEWS = ROOT / "workflows/studies/breast_clinical_molecular_discordance/reviews"


def _yaml(name: str) -> dict[str, Any]:
    return cast(
        dict[str, Any],
        yaml.safe_load((REVIEWS / name).read_text(encoding="utf-8")),
    )


def test_path_a_authorization_is_route_and_action_bounded() -> None:
    record = _yaml("FOUNDER_PATH_A_AUTHORIZATION_v1.0.0.yaml")
    decision = record["interpreted_decision"]
    assert decision["selected_path_id"] == "PATH-A"
    assert decision["bounded_external_contact_authorized"] is True
    assert decision["authorized_route_id"] == "ROUTE-1"
    assert "one eligibility-only inquiry" in decision["authorized_action"].lower()
    assert record["final_human_review_preserved"] is True


def test_path_a_authorization_retains_external_action_stops() -> None:
    record = _yaml("FOUNDER_PATH_A_AUTHORIZATION_v1.0.0.yaml")
    prohibited = set(record["prohibited_actions"])
    assert "Application submission" in prohibited
    assert "Spending or procurement" in prohibited
    assert "Specimen reservation, acquisition, receipt, or use" in prohibited
    assert "Controlled-data or PHI request, receipt, or use" in prohibited
    assert "External publication or submission" in prohibited


def test_chtn_inquiry_is_eligibility_only() -> None:
    packet = _yaml("CHTN_ELIGIBILITY_INQUIRY_PACKET_v1.0.0.yaml")
    assert packet["route_id"] == "ROUTE-1"
    assert packet["send_status"] == "authorized_not_yet_sent"
    assert len(packet["eligibility_questions"]) == 6
    boundaries = " ".join(packet["explicit_boundaries"]).lower()
    for term in ("application", "reservation", "quote", "purchase", "phi"):
        assert term in boundaries


def test_chtn_dispatch_receipt_records_only_the_authorized_side_effect() -> None:
    receipt = _yaml("CHTN_ELIGIBILITY_INQUIRY_DISPATCH_RECEIPT_v1.0.0.yaml")
    assert receipt["submission_result"] == "accepted_by_contact_form"
    effects = receipt["external_side_effects"]
    assert effects.pop("inquiry_sent") is True
    assert all(value is False for value in effects.values())
    assert receipt["next_state"] == "awaiting_provider_response"
    assert receipt["final_human_review_preserved"] is True
