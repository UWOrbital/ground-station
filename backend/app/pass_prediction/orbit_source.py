"""
Orbit data source for the pass predictor: downloads OMM records from CelesTrak into orbit_elements.

CelesTrak blocks clients that violate the usage policy, so we make sure not to download more often than
the refresh interval, record every attempt, and then stop if CelesTrak returns an error.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Final

import httpx
from loguru import logger

from app.config.env_settings.pass_prediction_config import PassPredictionConfig
from app.data.enums.transactional import OrbitElementSource
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import OrbitFetchAttemptRepository
from app.pass_prediction.orbit import omm_epoch, satellite_from_omm

USER_AGENT: Final[str] = "UW Orbital ground station (https://github.com/UWOrbital/ground-station)"

# Small margin before an epoch counts as "in the future"
_MAX_EPOCH_AHEAD: Final[timedelta] = timedelta(minutes=5)


class OrbitSourceError(Exception):
    """
    Orbit data could not be downloaded or was rejected. This attempt has been recorded.
    """


class RefreshOutcome(StrEnum):
    """
    Outcome of a refresh that didn't fail.
    """

    SKIPPED = "skipped"  # last attempt was too recent
    INSERTED = "inserted"  # inserted in orbit_elements
    UNCHANGED = "unchanged"  # elements already existed


@dataclass(frozen=True)
class ValidatedOmm:
    """
    A validated OMM record and the fields needed for orbit_elements.
    """

    omm: dict[str, Any]
    norad_cat_id: int
    epoch: datetime


def validate_omm(omm: object, now: datetime, expected_norad_cat_id: int | None = None) -> ValidatedOmm:
    """
    Validate an OMM record before storing it.

    :param omm: the parsed OMM record (CelesTrak JSON field names).
    :param now: current time, used to reject epochs in the future.
    :param expected_norad_cat_id: if given, the catalog number the record must match.
    :return: the record with its catalog number and epoch.
    :raises ValueError: if the record is invalid.
    """
    if not isinstance(omm, dict):
        raise ValueError("OMM record must be a JSON object")

    # Build the satellite using the predictor to ensure validity
    try:
        satellite_from_omm(omm)
    except KeyError as e:
        raise ValueError(f"OMM record is missing field {e}") from e
    except (TypeError, ValueError) as e:
        raise ValueError(f"OMM record can't be used for prediction: {e}") from e

    try:
        norad_cat_id = int(omm["NORAD_CAT_ID"])
    except (TypeError, ValueError) as e:
        raise ValueError(f"NORAD_CAT_ID is not an integer: {omm['NORAD_CAT_ID']!r}") from e
    if expected_norad_cat_id is not None and norad_cat_id != expected_norad_cat_id:
        raise ValueError(f"expected NORAD_CAT_ID {expected_norad_cat_id}, got {norad_cat_id}")

    try:
        epoch = omm_epoch(omm)
    except ValueError as e:
        raise ValueError(f"EPOCH is not a valid timestamp: {omm['EPOCH']!r}") from e
    if epoch > now + _MAX_EPOCH_AHEAD:
        raise ValueError(f"EPOCH {epoch.isoformat()} is in the future")

    return ValidatedOmm(omm=omm, norad_cat_id=norad_cat_id, epoch=epoch)


def celestrak_client(config: PassPredictionConfig) -> httpx.AsyncClient:
    """
    Create an HTTP client for CelesTrak.

    :param config: pass predictor settings.
    :return: a client to use as async context manager.
    """
    return httpx.AsyncClient(
        timeout=config.request_timeout_s,
        headers={"User-Agent": USER_AGENT},
        follow_redirects=False,
    )


async def refresh_orbit_elements(
    config: PassPredictionConfig, client: httpx.AsyncClient, now: datetime | None = None
) -> RefreshOutcome:
    """
    Download the latest orbit elements for the satellite.

    :param config: pass predictor settings.
    :param client: HTTP client for CelesTrak (celestrak_client).
    :param now: current time, defaults to now in UTC.
    :return: refresh outcome.
    :raises OrbitSourceError: if the request failed or was rejected.
    """
    now = now or datetime.now(UTC)
    norad_cat_id = config.norad_cat_id
    attempts = DAL.orbit_fetch_attempts()

    last_attempt = await attempts.get_latest(norad_cat_id)
    if last_attempt is not None and now - last_attempt.attempted_at < timedelta(hours=config.refresh_hours):
        logger.info(
            f"Orbit elements for {norad_cat_id} last requested at {last_attempt.attempted_at.isoformat()}, skipping"
        )
        return RefreshOutcome.SKIPPED

    try:
        response = await client.get(config.celestrak_url, params={"CATNR": str(norad_cat_id), "FORMAT": "json"})
    except httpx.HTTPError as e:
        await _record_attempt(attempts, norad_cat_id, now, http_status=None, error=f"request failed: {e!r}")
        raise OrbitSourceError(f"Request to CelesTrak failed: {e!r}") from e

    if response.status_code != httpx.codes.OK:
        await _record_attempt(
            attempts, norad_cat_id, now, http_status=response.status_code, error="unexpected HTTP status"
        )
        raise OrbitSourceError(f"CelesTrak returned HTTP {response.status_code}, not retrying until next refresh")

    try:
        validated = validate_omm(_single_record(response), now, expected_norad_cat_id=norad_cat_id)
    except ValueError as e:
        await _record_attempt(attempts, norad_cat_id, now, http_status=response.status_code, error=str(e))
        raise OrbitSourceError(f"Rejected CelesTrak response: {e}") from e

    inserted = await DAL.orbit_elements().insert_if_new(
        validated.norad_cat_id, validated.epoch, validated.omm, OrbitElementSource.CELESTRAK
    )
    await _record_attempt(attempts, norad_cat_id, now, http_status=response.status_code, inserted=inserted)

    outcome = RefreshOutcome.INSERTED if inserted else RefreshOutcome.UNCHANGED
    logger.info(f"Orbit elements for {norad_cat_id}: {outcome} (epoch {validated.epoch.isoformat()})")
    return outcome


async def add_manual_omm(omm: object, now: datetime | None = None) -> bool:
    """
    Store a manual OMM record.

    :param omm: the parsed record (CelesTrak JSON field names).
    :param now: current time, defaults to now in UTC.
    :return: True if stored, False if elements with the same epoch were already stored.
    :raises ValueError: if the record is invalid.
    """
    validated = validate_omm(omm, now or datetime.now(UTC))
    return await DAL.orbit_elements().insert_if_new(
        validated.norad_cat_id, validated.epoch, validated.omm, OrbitElementSource.MANUAL
    )


def _single_record(response: httpx.Response) -> object:
    """
    Extract the one OMM record from a CelesTrak JSON.

    :param response: a 200 response from CelesTrak.
    :return: the record (not validated yet).
    :raises ValueError: if the body isn't a JSON array with exactly one record.
    """
    try:
        body = response.json()
    except ValueError as e:
        raise ValueError(f"response is not JSON: {response.text[:100]!r}") from e
    if not isinstance(body, list) or len(body) != 1:
        count = len(body) if isinstance(body, list) else "non-list"
        raise ValueError(f"expected a JSON array with one OMM record, got {count}")
    return body[0]


async def _record_attempt(
    attempts: OrbitFetchAttemptRepository,
    norad_cat_id: int,
    attempted_at: datetime,
    http_status: int | None,
    error: str | None = None,
    inserted: bool = False,
) -> None:
    """
    Store a fetch attempt.

    :param attempts: fetch attempt repository.
    :param norad_cat_id: catalog number that was requested.
    :param attempted_at: when the request was made.
    :param http_status: response status, or None if no response was received.
    :param error: why the attempt failed, or None if it was successful.
    :param inserted: whether the orbit elements were stored.
    """
    await attempts.create({
        "norad_cat_id": norad_cat_id,
        "attempted_at": attempted_at,
        "http_status": http_status,
        "error": error,
        "inserted": inserted,
    })
