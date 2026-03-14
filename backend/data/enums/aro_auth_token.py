from enum import StrEnum, auto


class AROAuthToken(StrEnum):
    """
    The possible authentication token types for ARO users.
    """

    GOOGLE_OAUTH = auto()
    EMAIL_PASSWORD = auto()

    # Legacy/placeholder states (can be removed if unused)
    DUMMY = auto()
    ANOTHERDUMMY = auto()
    TEST = auto()
