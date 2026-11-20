import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from app.pass_prediction.orbit import PredictedPass, Station, omm_epoch, predict_passes

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "iss_omm.json"

# UW E7 location
STATION = Station(latitude_deg=43.4730, longitude_deg=-80.5395, altitude_m=372.0)
MIN_ELEVATION_DEG = 15.0


def assert_same_pass(actual: PredictedPass, expected: PredictedPass) -> None:
    """Assert two predictions describe the same pass.

    Skyfield's event search refines times to a tolerance that depends on the search window,
    so the same pass found from different windows differs by milliseconds.

    :param actual: the pass to check.
    :param expected: the pass to match.
    """
    tolerance = timedelta(seconds=1)
    assert abs(actual.rise_time - expected.rise_time) < tolerance
    assert abs(actual.peak_time - expected.peak_time) < tolerance
    assert abs(actual.set_time - expected.set_time) < tolerance
    assert actual.max_elevation_deg == pytest.approx(
        expected.max_elevation_deg, abs=0.01
    )
    assert actual.rise_azimuth_deg == pytest.approx(expected.rise_azimuth_deg, abs=0.1)
    assert actual.set_azimuth_deg == pytest.approx(expected.set_azimuth_deg, abs=0.1)


@pytest.fixture(scope="module")
def iss_omm() -> dict[str, Any]:
    """Load the committed ISS OMM record (CelesTrak JSON: a one-item array).

    :return: the OMM record.
    """
    records: list[dict[str, Any]] = json.loads(FIXTURE_PATH.read_text())
    return records[0]


@pytest.fixture(scope="module")
def window_start(iss_omm: dict[str, Any]) -> datetime:
    """Start predictions at the fixture's epoch, where SGP4 is most accurate.

    :param iss_omm: the ISS OMM record.
    :return: the window start.
    """
    return omm_epoch(iss_omm)


@pytest.fixture(scope="module")
def day_of_passes(
    iss_omm: dict[str, Any], window_start: datetime
) -> list[PredictedPass]:
    """Predict one day of passes from the fixture epoch.

    :param iss_omm: the ISS OMM record.
    :param window_start: the window start.
    :return: the predicted passes.
    """
    return predict_passes(
        iss_omm,
        STATION,
        window_start,
        window_start + timedelta(days=1),
        MIN_ELEVATION_DEG,
    )


def test_omm_epoch_is_utc() -> None:
    """A naive CelesTrak epoch is read as UTC, not local time."""
    epoch = omm_epoch({"EPOCH": "2026-11-20T11:24:04.123456"})
    assert epoch == datetime(2026, 11, 20, 11, 24, 4, 123456, tzinfo=UTC)


def test_omm_epoch_converts_offset_to_utc() -> None:
    """An epoch that does carry an offset is converted to UTC."""
    epoch = omm_epoch({"EPOCH": "2026-11-20T11:24:04-05:00"})
    assert epoch == datetime(2026, 11, 20, 16, 24, 4, tzinfo=UTC)


def test_finds_passes_in_a_day(day_of_passes: list[PredictedPass]) -> None:
    """The ISS passes over Waterloo above 15 degrees a few times a day."""
    assert 1 <= len(day_of_passes) <= 10


def test_pass_shape(day_of_passes: list[PredictedPass]) -> None:
    for p in day_of_passes:
        assert p.rise_time < p.peak_time < p.set_time
        assert MIN_ELEVATION_DEG < p.max_elevation_deg <= 90
        assert p.min_elevation_deg == MIN_ELEVATION_DEG
        assert timedelta(seconds=30) < p.set_time - p.rise_time < timedelta(minutes=15)
        assert 0 <= p.rise_azimuth_deg < 360
        assert 0 <= p.set_azimuth_deg < 360
        for t in (p.rise_time, p.peak_time, p.set_time):
            assert t.utcoffset() == timedelta(0)


def test_passes_ordered_and_not_overlapping(day_of_passes: list[PredictedPass]) -> None:
    """Passes are in time order and never overlap."""
    for earlier, later in zip(day_of_passes, day_of_passes[1:], strict=False):
        assert earlier.set_time < later.rise_time


def test_rises_inside_window(iss_omm: dict[str, Any], window_start: datetime) -> None:
    """Every returned pass rises inside [start, end)."""
    end = window_start + timedelta(hours=12)
    for p in predict_passes(iss_omm, STATION, window_start, end, MIN_ELEVATION_DEG):
        assert window_start <= p.rise_time < end


def test_window_starting_mid_pass_skips_that_pass(
    iss_omm: dict[str, Any], window_start: datetime, day_of_passes: list[PredictedPass]
) -> None:
    """A pass already in progress at the window start is not returned."""
    first = day_of_passes[0]
    passes = predict_passes(
        iss_omm,
        STATION,
        first.peak_time,
        window_start + timedelta(days=1),
        MIN_ELEVATION_DEG,
    )
    assert all(p.rise_time > first.peak_time for p in passes)
    assert len(passes) == len(day_of_passes) - 1
    for actual, expected in zip(passes, day_of_passes[1:], strict=True):
        assert_same_pass(actual, expected)


def test_window_ending_mid_pass_returns_full_pass(
    iss_omm: dict[str, Any], window_start: datetime, day_of_passes: list[PredictedPass]
) -> None:
    """A pass that rises before the window end is returned complete, set time included."""
    first = day_of_passes[0]
    passes = predict_passes(
        iss_omm, STATION, window_start, first.peak_time, MIN_ELEVATION_DEG
    )
    assert len(passes) == 1
    assert_same_pass(passes[0], first)


def test_higher_cutoff_gives_shorter_subset(
    iss_omm: dict[str, Any], window_start: datetime, day_of_passes: list[PredictedPass]
) -> None:
    """Raising the cutoff will keep only high passes, which are each a sub-window of a 15 degree pass."""
    high = predict_passes(
        iss_omm, STATION, window_start, window_start + timedelta(days=1), 45.0
    )
    assert len(high) <= len(day_of_passes)
    for h in high:
        containing = [
            p
            for p in day_of_passes
            if p.rise_time < h.rise_time and h.set_time < p.set_time
        ]
        assert len(containing) == 1
        assert h.max_elevation_deg == pytest.approx(
            containing[0].max_elevation_deg, abs=0.01
        )


def test_rejects_naive_datetimes(iss_omm: dict[str, Any]) -> None:
    """Naive datetimes are rejected instead of being read in the machine's local time."""
    with pytest.raises(ValueError, match="timezone"):
        predict_passes(
            iss_omm,
            STATION,
            datetime(2026, 11, 17),
            datetime(2026, 11, 18),
            MIN_ELEVATION_DEG,
        )


def test_rejects_empty_window(iss_omm: dict[str, Any], window_start: datetime) -> None:
    """An end before the start is an error, not an empty result."""
    with pytest.raises(ValueError, match="after start"):
        predict_passes(iss_omm, STATION, window_start, window_start, MIN_ELEVATION_DEG)
