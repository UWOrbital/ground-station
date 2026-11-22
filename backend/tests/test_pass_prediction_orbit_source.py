import argparse
import json
from collections.abc import Callable
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import httpx
import pytest
from app.config.env_settings.pass_prediction_config import PassPredictionConfig
from app.data.enums.transactional import OrbitElementSource
from app.data.repositories.dal import DAL
from app.pass_prediction.__main__ import run_command
from app.pass_prediction.orbit import omm_epoch
from app.pass_prediction.orbit_source import (
    OrbitSourceError,
    RefreshOutcome,
    add_manual_omm,
    refresh_orbit_elements,
    validate_omm,
)
from pydantic import ValidationError

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "iss_omm.json"


@pytest.fixture
def iss_record() -> dict[str, Any]:
    """Load the committed ISS OMM record (CelesTrak JSON: a one-item array).

    :return: a fresh copy of the record.
    """
    records: list[dict[str, Any]] = json.loads(FIXTURE_PATH.read_text())
    return records[0]


@pytest.fixture
def config(iss_record: dict[str, Any]) -> PassPredictionConfig:
    """Pass predictor settings for the ISS with a 6 hour refresh interval.

    :param iss_record: the ISS OMM record.
    :return: the settings.
    """
    return PassPredictionConfig(norad_cat_id=int(iss_record["NORAD_CAT_ID"]), refresh_hours=6)


@pytest.fixture
def now(iss_record: dict[str, Any]) -> datetime:
    """A fixed "current time" an hour after the fixture's epoch.

    :param iss_record: the ISS OMM record.
    :return: the time.
    """
    return omm_epoch(iss_record) + timedelta(hours=1)


class FakeCelesTrak:
    """Fake CelesTrak that records requests and returns a response."""

    def __init__(self, respond: Callable[[httpx.Request], httpx.Response]) -> None:
        """Create the fake.

        :param respond: builds the response for each request.
        """
        self.requests: list[httpx.Request] = []
        self._respond = respond

    def client(self) -> httpx.AsyncClient:
        """Return an HTTP client whose requests go to this fake.

        :return: the client.
        """

        def handler(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return self._respond(request)

        return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def json_response(body: object, status: int = 200) -> Callable[[httpx.Request], httpx.Response]:
    """Build a responder returning a fixed JSON body.

    :param body: the JSON body.
    :param status: HTTP status code.
    :return: the responder.
    """
    return lambda _request: httpx.Response(status, json=body)


async def stored_elements(norad_cat_id: int) -> list[Any]:
    """Return all stored orbit elements for a satellite.

    :param norad_cat_id: catalog number.
    :return: the rows.
    """
    return await DAL.orbit_elements().get_all_by(norad_cat_id=norad_cat_id)


async def stored_attempts(norad_cat_id: int) -> list[Any]:
    """Return all recorded fetch attempts for a satellite.

    :param norad_cat_id: catalog number.
    :return: the rows.
    """
    return await DAL.orbit_fetch_attempts().get_all_by(norad_cat_id=norad_cat_id)


# --- config ---


def test_config_refuses_refresh_faster_than_two_hours() -> None:
    with pytest.raises(ValidationError):
        PassPredictionConfig(refresh_hours=1)


# --- validate_omm ---


def test_validate_omm_extracts_catalog_number_and_epoch(iss_record: dict[str, Any], now: datetime) -> None:
    validated = validate_omm(iss_record, now, expected_norad_cat_id=int(iss_record["NORAD_CAT_ID"]))
    assert validated.norad_cat_id == int(iss_record["NORAD_CAT_ID"])
    assert validated.epoch == omm_epoch(iss_record)


@pytest.mark.parametrize(
    ("change", "message"),
    [
        (lambda r: r.pop("MEAN_MOTION"), "missing field 'MEAN_MOTION'"),
        (lambda r: r.pop("MEAN_MOTION_DOT"), "missing field 'MEAN_MOTION_DOT'"),
        (lambda r: r.pop("OBJECT_ID"), "missing field 'OBJECT_ID'"),
        (
            lambda r: r.update(EPOCH=r["EPOCH"].split(".")[0]),
            "can't be used for prediction",
        ),
        (lambda r: r.update(EPOCH=r["EPOCH"] + "Z"), "can't be used for prediction"),
        (lambda r: r.update(EPOCH="not a date"), "can't be used for prediction"),
        (lambda r: r.update(NORAD_CAT_ID="abc"), "can't be used for prediction"),
        (lambda r: r.update(NORAD_CAT_ID=99999), "expected NORAD_CAT_ID"),
        (lambda r: r.update(EPOCH="2099-01-01T00:00:00.000000"), "in the future"),
    ],
)
def test_validate_omm_rejects_bad_records(
    iss_record: dict[str, Any],
    now: datetime,
    change: Callable[[dict[str, Any]], object],
    message: str,
) -> None:
    change(iss_record)
    with pytest.raises(ValueError, match=message):
        validate_omm(iss_record, now, expected_norad_cat_id=25544)


def test_validate_omm_rejects_non_object(now: datetime) -> None:
    with pytest.raises(ValueError, match="JSON object"):
        validate_omm(["not", "a", "record"], now)


# --- refresh_orbit_elements ---


async def test_first_refresh_stores_elements(
    config: PassPredictionConfig, iss_record: dict[str, Any], now: datetime
) -> None:
    """With no previous attempt, the elements are downloaded, stored, and the attempt recorded."""
    celestrak = FakeCelesTrak(json_response([iss_record]))
    async with celestrak.client() as client:
        outcome = await refresh_orbit_elements(config, client, now)

    assert outcome == RefreshOutcome.INSERTED
    assert len(celestrak.requests) == 1
    assert celestrak.requests[0].url.params["CATNR"] == str(config.norad_cat_id)
    assert celestrak.requests[0].url.params["FORMAT"] == "json"

    elements = await stored_elements(config.norad_cat_id)
    assert len(elements) == 1
    assert elements[0].epoch == omm_epoch(iss_record)
    assert elements[0].source == OrbitElementSource.CELESTRAK

    attempts = await stored_attempts(config.norad_cat_id)
    assert len(attempts) == 1
    assert attempts[0].http_status == 200
    assert attempts[0].error is None
    assert attempts[0].inserted is True


async def test_recent_attempt_skips_request(
    config: PassPredictionConfig, iss_record: dict[str, Any], now: datetime
) -> None:
    """Within the refresh interval, the request should be skipped."""
    celestrak = FakeCelesTrak(json_response([iss_record]))
    async with celestrak.client() as client:
        await refresh_orbit_elements(config, client, now)
        outcome = await refresh_orbit_elements(config, client, now + timedelta(hours=1))

    assert outcome == RefreshOutcome.SKIPPED
    assert len(celestrak.requests) == 1


async def test_same_epoch_records_attempt_without_duplicate(
    config: PassPredictionConfig, iss_record: dict[str, Any], now: datetime
) -> None:
    """Re-downloading unchanged elements records the attempt but stores no duplicate row."""
    celestrak = FakeCelesTrak(json_response([iss_record]))
    async with celestrak.client() as client:
        await refresh_orbit_elements(config, client, now)
        outcome = await refresh_orbit_elements(config, client, now + timedelta(hours=7))

    assert outcome == RefreshOutcome.UNCHANGED
    assert len(await stored_elements(config.norad_cat_id)) == 1
    attempts = await stored_attempts(config.norad_cat_id)
    assert len(attempts) == 2
    assert sorted(a.inserted for a in attempts) == [False, True]


async def test_http_error_is_recorded_and_not_retried(
    config: PassPredictionConfig, now: datetime
) -> None:
    """An error status is recorded, raises, and blocks requests until the next refresh is due."""
    celestrak = FakeCelesTrak(json_response({"detail": "forbidden"}, status=403))
    async with celestrak.client() as client:
        with pytest.raises(OrbitSourceError, match="HTTP 403"):
            await refresh_orbit_elements(config, client, now)
        outcome = await refresh_orbit_elements(config, client, now + timedelta(hours=1))

    assert outcome == RefreshOutcome.SKIPPED
    assert len(celestrak.requests) == 1
    assert await stored_elements(config.norad_cat_id) == []
    attempts = await stored_attempts(config.norad_cat_id)
    assert attempts[0].http_status == 403
    assert attempts[0].error is not None


async def test_redirect_is_not_followed(config: PassPredictionConfig, now: datetime) -> None:
    """A 301 redirect should be treated as an error."""
    celestrak = FakeCelesTrak(lambda _r: httpx.Response(301, headers={"Location": "https://example.com"}))
    async with celestrak.client() as client:
        with pytest.raises(OrbitSourceError, match="HTTP 301"):
            await refresh_orbit_elements(config, client, now)
    assert len(celestrak.requests) == 1


async def test_network_error_is_recorded(config: PassPredictionConfig, now: datetime) -> None:
    """When no response arrives, the attempt is recorded without an HTTP status."""

    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    async with FakeCelesTrak(fail).client() as client:
        with pytest.raises(OrbitSourceError, match="Request to CelesTrak failed"):
            await refresh_orbit_elements(config, client, now)

    attempts = await stored_attempts(config.norad_cat_id)
    assert len(attempts) == 1
    assert attempts[0].http_status is None


@pytest.mark.parametrize(
    ("respond", "message"),
    [
        (lambda _r: httpx.Response(200, text="No GP data found"), "not JSON"),
        (json_response([]), "one OMM record, got 0"),
        (json_response({"EPOCH": "x"}), "non-list"),
    ],
)
async def test_bad_body_is_rejected(
    config: PassPredictionConfig,
    now: datetime,
    respond: Callable[[httpx.Request], httpx.Response],
    message: str,
) -> None:
    """Bodies that aren't exactly one OMM record are recorded as failures and nothing is stored."""
    async with FakeCelesTrak(respond).client() as client:
        with pytest.raises(OrbitSourceError, match=message):
            await refresh_orbit_elements(config, client, now)

    assert await stored_elements(config.norad_cat_id) == []
    attempts = await stored_attempts(config.norad_cat_id)
    assert attempts[0].http_status == 200
    assert attempts[0].inserted is False


async def test_record_for_wrong_satellite_is_rejected(
    config: PassPredictionConfig, iss_record: dict[str, Any], now: datetime
) -> None:
    """A record whose catalog number doesn't match the request is not stored."""
    iss_record["NORAD_CAT_ID"] = 99999
    async with FakeCelesTrak(json_response([iss_record])).client() as client:
        with pytest.raises(OrbitSourceError, match="expected NORAD_CAT_ID"):
            await refresh_orbit_elements(config, client, now)
    assert await stored_elements(99999) == []


# --- manual entry ---


async def test_add_manual_omm_stores_with_manual_source(iss_record: dict[str, Any], now: datetime) -> None:
    """Hand-entered elements are stored as MANUAL. Entering the same epoch again stores nothing."""
    assert await add_manual_omm(iss_record, now) is True
    assert await add_manual_omm(iss_record, now) is False

    elements = await stored_elements(int(iss_record["NORAD_CAT_ID"]))
    assert len(elements) == 1
    assert elements[0].source == OrbitElementSource.MANUAL


@pytest.mark.parametrize("wrap_in_array", [False, True])
async def test_cli_add_omm_accepts_object_or_one_item_array(
    tmp_path: Path, iss_record: dict[str, Any], wrap_in_array: bool
) -> None:
    """The add-omm command accepts a single record, or a saved CelesTrak response (a one-item array)."""
    path = tmp_path / "omm.json"
    path.write_text(json.dumps([iss_record] if wrap_in_array else iss_record))

    assert await run_command(argparse.Namespace(command="add-omm", path=path)) == 0
    assert len(await stored_elements(int(iss_record["NORAD_CAT_ID"]))) == 1


async def test_cli_add_omm_fails_on_invalid_file(tmp_path: Path) -> None:
    """Invalid input exits with code 1."""
    path = tmp_path / "omm.json"
    path.write_text("[{}, {}]")
    assert await run_command(argparse.Namespace(command="add-omm", path=path)) == 1
    assert await run_command(argparse.Namespace(command="add-omm", path=tmp_path / "missing.json")) == 1
