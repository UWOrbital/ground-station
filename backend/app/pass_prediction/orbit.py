"""
Orbit math for the ground station.
Loads OMM data and predicts passes over a station.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final

from skyfield.api import EarthSatellite, GeographicPosition, Timescale, load, wgs84

# Search a little past the window to allow passes that rise before `end` but set after
_SEARCH_MARGIN: Final[timedelta] = timedelta(minutes=30)

# Skyfield event codes
_RISE: Final[int] = 0
_PEAK: Final[int] = 1
_SET: Final[int] = 2

_timescale: Timescale = load.timescale()


@dataclass(frozen=True)
class Station:
    """
    A ground station location.
    """

    latitude_deg: float
    longitude_deg: float
    altitude_m: float


@dataclass(frozen=True)
class PredictedPass:
    """
    Pass of the satellite above minimum elevation, from a station.

    All times are UTC datetimes.
    """

    rise_time: datetime
    peak_time: datetime
    set_time: datetime
    min_elevation_deg: float
    max_elevation_deg: float
    rise_azimuth_deg: float
    set_azimuth_deg: float


def omm_epoch(omm: dict[str, Any]) -> datetime:
    """
    Parse epoch from an OMM record as a UTC datetime.

    :param omm: OMM record using CelesTrak JSON field names.
    :return: the epoch as a UTC datetime.
    """
    epoch = datetime.fromisoformat(str(omm["EPOCH"]))
    return epoch.replace(tzinfo=UTC) if epoch.tzinfo is None else epoch.astimezone(UTC)


def predict_passes(
    omm: dict[str, Any], station: Station, start: datetime, end: datetime, min_elevation_deg: float
) -> list[PredictedPass]:
    """
    Predict passes that rise above minimum elevation and within a time window.

    Passes are included if their rise time is within [start, end).

    :param omm: OMM record using CelesTrak JSON field names.
    :param station: ground station to predict passes for.
    :param start: window start (timezone-aware).
    :param end: window end (timezone-aware).
    :param min_elevation_deg: elevation cutoff in degrees for rise and set.
    :return: passes ordered by rise time.
    :raises ValueError: if datetime has no timezone or window is empty.
    """
    if start.tzinfo is None or end.tzinfo is None:
        raise ValueError("start and end must have timezone")
    if end <= start:
        raise ValueError("end must be after start")

    satellite = _satellite(omm)
    observer = _satellite(station)


def _satellite(omm: dict[str, Any]) -> EarthSatellite:
    """
    Create a Skyfield satellite from an OMM record.

    :param omm: OMM record using CelesTrak JSON field names.
    :return: the satellite.
    """
    return EarthSatellite.from_omm(_timescale, omm)


def _observer(station: Station) -> GeographicPosition:
    """
    Create a Skyfield observer position based on a station.

    :param station: ground station location.
    :return: WGS84 position for the ground station.
    """
    return wgs84.latlon(station.latitude_deg, station.longitude_deg, elevation_m=station.altitude_m)
