class GovernanceError(Exception):
    """Base exception for governance failures."""


class SourceNotFoundError(GovernanceError):
    """Raised when a requested source is not registered."""


class InvalidLifecycleTransitionError(GovernanceError):
    """Raised when a source lifecycle transition is prohibited."""


class PolicyDeniedError(GovernanceError):
    """Raised when a requested data action is denied."""
