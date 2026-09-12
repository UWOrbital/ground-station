from enum import StrEnum, auto


class MCCAdminRequestStatus(StrEnum):
    """
    The possible states of an MCC user's request for admin access
    """

    NOT_REQUESTED = auto()
    PENDING = auto()
    APPROVED = auto()
    REJECTED = auto()
