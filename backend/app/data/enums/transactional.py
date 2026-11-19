from enum import Enum, StrEnum, auto


class CommandStatus(StrEnum):
    """
    Represents the possible states that a command can be in
    """

    PENDING = auto()  # Command was created in the db but not yet sent to the OBC
    SCHEDULED = auto()  # Command was sent to the OBC
    ONGOING = auto()  # Command is executing on the OBC
    CANCELLED = auto()  # Command was cancelled by MCC. This is a final state of a command
    FAILED = auto()  # Command failed to complete. This is a final state of a command
    COMPLETED = (
        auto()
    )  # Command executed successfully. this should be the final state of a command if all was successful


class SessionStatus(StrEnum):
    """
    Represents the lifecycle of a session. Status changes at schedule freeze, start_time, and end_time.
    """

    PENDING = auto()  # Initial state of a session until schedule freeze begins
    SCHEDULED = auto()  # Times are final, set by the pass predictor at schedule freeze. Manual sessions start here
    ONGOING = auto()  # Session is in progress, set at start_time
    COMPLETED = auto()  # Session is complete, set at end_time. Final state of session


class SessionSource(StrEnum):
    """
    Represents who created a session
    """

    PREDICTED = auto()  # Created and kept in sync by the pass predictor
    MANUAL = auto()  # Created by an operator, never modified by the pass predictor


class OrbitElementSource(StrEnum):
    """
    Represents where a set of orbit elements came from
    """

    CELESTRAK = auto()  # Downloaded from CelesTrak
    MANUAL = auto()  # Manually inserted


class MainPacketType(Enum):
    """
    Represents the type of packets that can be transmited/received
    """

    UPLINK = auto()
    DOWNLINK = auto()
