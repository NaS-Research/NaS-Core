"""Shared review provenance for founder-led and externally reviewed research."""

from enum import StrEnum


class ReviewType(StrEnum):
    """Review provenance; only human review types may authorize lifecycle gates."""

    INTERNAL_SELF_REVIEW = "internal_self_review"
    AI_ASSISTED_INTERNAL_REVIEW = "ai_assisted_internal_review"
    INDEPENDENT_HUMAN_REVIEW = "independent_human_review"
    JOURNAL_PEER_REVIEW = "journal_peer_review"
