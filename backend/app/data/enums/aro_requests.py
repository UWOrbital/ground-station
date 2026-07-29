from enum import StrEnum, auto


class ARORequestStatus(StrEnum):
    """
    The possible states that an ARO request can be
    """

    PENDING = auto()  # Command to take picture was created in the database but not sent to the OBC
    SCHEDULED = auto()  # Command to take picture sent to OBC
    TAKEN = auto()  # Picture was taken but waiting to be transmitted
    CANCELLED = auto()  # ARO cancelled the picture being taken. This is a final state of a picture
    FAILED = auto()  # Picture cannot be taken but it was not cancelled. This is a final state of a picture
    COMPLETED = auto()  # Final status of picture if all was successful
