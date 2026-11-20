from enum import StrEnum, auto


class SatelliteStatus(StrEnum):
    """
    Represents the possible states that a satellite connection can be in
    """

    PENDING = auto()
    SCHEDULED = auto()
    ONLINE = auto()
    COMPLETED = auto()
    OFFLINE = auto()  # no session has been recorded
