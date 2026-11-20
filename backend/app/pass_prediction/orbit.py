"""
Orbit math for the ground station.
Loads OMM data and predicts passes over a station.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Final

from skyfield.api import EarthSatellite, Time, Timescale, load, wgs84
from skyfield.toposlib import GeographicPosition

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
    observer = _observer(station)
    times, events = satellite.find_events(
        observer,
        _timescale.from_datetime(start),
        _timescale.from_datetime(end + _SEARCH_MARGIN),
        altitude_degrees=min_elevation_deg,
    )

    passes: list[PredictedPass] = []
    rise: Time | None = None
    peak: Time | None = None
    peak_elevation = 0.0

    for t, event in zip(times, events, strict=True):
        if event == _RISE:
            rise, peak, peak_elevation = t, None, 0.0
        elif event == _PEAK and rise is not None:
            elevation = _elevation_deg(satellite, observer, t)
            # Skyfield can potentially report several peaks in one pass, keep the highest
            if peak is None or elevation > peak_elevation:
                peak, peak_elevation = t, elevation
        elif event == _SET:
            if rise is not None and peak is not None:
                rise_time = rise.utc_datetime()
                if start <= rise_time < end:
                    passes.append(
                        PredictedPass(
                            rise_time=rise_time,
                            peak_time=peak.utc_datetime(),
                            set_time=t.utc_datetime(),
                            min_elevation_deg=min_elevation_deg,
                            max_elevation_deg=peak_elevation,
                            rise_azimuth_deg=_azimuth_deg(satellite, observer, rise),
                            set_azimuth_deg=_azimuth_deg(satellite, observer, t),
                        )
                    )
            rise, peak, peak_elevation = None, None, 0.0

    return passes


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


def _elevation_deg(satellite: EarthSatellite, observer: GeographicPosition, t: Time) -> float:
    """
    Compute the satellite's elevation deg above the station's horizon.

    :param satellite: the satellite.
    :param observer: the ground station position.
    :param t: the time to evaluate at.
    :return: elevation in degrees.
    """
    altitude, _, _ = (satellite - observer).at(t).altaz()
    return float(altitude.degrees)


def _azimuth_deg(satellite: EarthSatellite, observer: GeographicPosition, t: Time) -> float:
    """
    Compute the satellite's compass direction from the station.

    :param satellite: the satellite.
    :param observer: the ground station position.
    :param t: the time to evaluate at.
    :return: azimuth in degrees clockwise from north, [0, 360)
    """
    _, azimuth, _ = (satellite - observer).at(t).altaz()
    return float(azimuth.degrees) % 360.0  # mod by 360 to prevent rounding errors to 360
