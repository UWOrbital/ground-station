from enum import StrEnum, auto


class AROAuthToken(StrEnum):
    """
    The possible authentication token types for ARO users.
    """

    # Email/password authentication
    EMAIL_PASSWORD = auto()

    # Google OAuth authentication
    GOOGLE_OAUTH = auto()

    # Legacy/placeholder states (can be removed if unused)
    DUMMY = auto()
    ANOTHERDUMMY = auto()
    TEST = auto()
