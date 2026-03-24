from enum import Enum, StrEnum, auto


class CommandStatus(StrEnum):
    """
    Represents the possible states that a command can be in
    """

    PENDING = "PENDING"  # Command was created in the db but not yet sent to the OBC
    SCHEDULED = "SCHEDULED"  # Command is queued and ready to be packeted
    PACKETED = "PACKETED"  # Command is packeted and ready to be sent to the OBC
    SENT = "SENT"  # Command was sent to the OBC
    CANCELLED = "CANCELLED"  # Command was cancelled by MCC or an ARO. This is a final state of a command
    FAILED = "FAILED"  # Command failed to complete. This is a final state of a command
    COMPLETED = "COMPLETED"  # Command executed successfully. this should be the final state of a command if successful


class SessionStatus(StrEnum):
    """
    Represents the possible states that a session can be in
    """

    PENDING = auto()  # Initial state of a session. Optional or can start at SCHEDULED status
    SCHEDULED = auto()  # Session has been scheduled. GS has not received any data yet but the start time is known
    ONGOING = auto()  # Session has been started. GS is receiving data
    COMPLETED = auto()  # Session is complete. GS has received all the data for the session. Final state of session


class MainPacketType(Enum):
    """
    Represents the type of packets that can be transmited/received
    """

    UPLINK = auto()
    DOWNLINK = auto()
