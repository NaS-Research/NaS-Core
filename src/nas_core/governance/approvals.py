from nas_core.domain.datasets import SourceStatus
from nas_core.governance.exceptions import (
    InvalidLifecycleTransitionError,
)

_ALLOWED_TRANSITIONS: dict[SourceStatus, set[SourceStatus]] = {
    SourceStatus.PROPOSED: {SourceStatus.UNDER_REVIEW},
    SourceStatus.UNDER_REVIEW: {SourceStatus.APPROVED, SourceStatus.SUSPENDED},
    SourceStatus.APPROVED: {SourceStatus.ACTIVE, SourceStatus.SUSPENDED},
    SourceStatus.ACTIVE: {
        SourceStatus.SUSPENDED,
        SourceStatus.EXPIRED,
        SourceStatus.ARCHIVED,
    },
    SourceStatus.SUSPENDED: {SourceStatus.UNDER_REVIEW, SourceStatus.ARCHIVED},
    SourceStatus.EXPIRED: {SourceStatus.UNDER_REVIEW, SourceStatus.ARCHIVED},
    SourceStatus.ARCHIVED: {SourceStatus.DELETED},
    SourceStatus.DELETED: set(),
}


def transition_source(current: SourceStatus, target: SourceStatus) -> SourceStatus:
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise InvalidLifecycleTransitionError(
            f"Cannot transition a source from {current.value} to {target.value}"
        )
    return target
