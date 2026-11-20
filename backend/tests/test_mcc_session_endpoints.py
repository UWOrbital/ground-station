from collections.abc import AsyncGenerator, Callable
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest_asyncio
from app.config.data_values import MAX_PAGE_LIMIT
from app.data.enums.transactional import SessionStatus
from app.data.models.mcc_user_models import MCCUsers
from app.data.models.transactional_models import OrbitElement, Session
from app.mcc_keycloak.client import keycloak
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from main import app
from sqlmodel.ext.asyncio.session import AsyncSession

SESSIONS_URL = "/api/mcc/sessions/"


@pytest_asyncio.fixture
async def mcc_user(db_session: AsyncSession) -> MCCUsers:
    """Create a test MCC user in the database.

    :param db_session: test database session
    :return: the persisted user
    """
    user = MCCUsers(id=uuid4(), email="test@uworbital.ca", phone_number=None)
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def client(mcc_user: MCCUsers) -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient with Keycloak auth dependencies overridden.

    :param mcc_user: user returned as the authenticated caller
    :return: an authenticated client
    """
    app.dependency_overrides[keycloak.get_current_user] = lambda: mcc_user
    app.dependency_overrides[keycloak.authenticate] = lambda: {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def _add_session(
    db_session: AsyncSession, start_offset: timedelta, minutes: int = 10, **fields: object
) -> Session:
    """Add a manual session starting relative to now.

    :param db_session: test database session
    :param start_offset: start time relative to the current time
    :param minutes: session length in minutes
    :param fields: extra Session fields
    :return: the persisted session
    """
    start = datetime.now(UTC) + start_offset
    session = Session(start_time=start, end_time=start + timedelta(minutes=minutes), **fields)
    db_session.add(session)
    await db_session.commit()
    return session


def _ids(body: dict[str, list[dict[str, object]]]) -> list[str]:
    """Extract the session IDs from a list response body.

    :param body: decoded JSON response
    :return: IDs in response order
    """
    return [item["id"] for item in body["data"]]


# ------------------------------------------------------GET /sessions/------------------------------------------------------ #


async def test_get_sessions_end_after_includes_running(client: AsyncClient, db_session: AsyncSession) -> None:
    """end_after now should return a session already in progress. start_after now should not"""
    running = await _add_session(db_session, timedelta(minutes=-2), minutes=7)
    await _add_session(db_session, timedelta(hours=-1))
    now = datetime.now(UTC).isoformat()

    by_end = await client.get(SESSIONS_URL, params={"end_after": now})
    by_start = await client.get(SESSIONS_URL, params={"start_after": now})

    assert by_end.status_code == 200
    assert _ids(by_end.json()) == [str(running.id)]
    assert by_start.status_code == 200
    assert _ids(by_start.json()) == []


async def test_get_sessions_source_filter(
    client: AsyncClient, db_session: AsyncSession, make_predicted_session: Callable[..., Session]
) -> None:
    manual = await _add_session(db_session, timedelta(hours=1))
    predicted = make_predicted_session(datetime.now(UTC) + timedelta(hours=2))
    db_session.add(predicted)
    await db_session.commit()

    manual_resp = await client.get(SESSIONS_URL, params={"source": "manual"})
    predicted_resp = await client.get(SESSIONS_URL, params={"source": "predicted"})

    assert _ids(manual_resp.json()) == [str(manual.id)]
    assert _ids(predicted_resp.json()) == [str(predicted.id)]


async def test_get_sessions_status_filter(client: AsyncClient, db_session: AsyncSession) -> None:
    await _add_session(db_session, timedelta(hours=1))
    scheduled = await _add_session(db_session, timedelta(hours=2), status=SessionStatus.SCHEDULED)

    response = await client.get(SESSIONS_URL, params={"status": "scheduled"})

    assert response.status_code == 200
    assert _ids(response.json()) == [str(scheduled.id)]


async def test_get_sessions_offset_and_limit(client: AsyncClient, db_session: AsyncSession) -> None:
    """offset=1&limit=1 returns only the second session by start_time."""
    await _add_session(db_session, timedelta(hours=1))
    second = await _add_session(db_session, timedelta(hours=2))
    await _add_session(db_session, timedelta(hours=3))

    response = await client.get(SESSIONS_URL, params={"offset": 1, "limit": 1})

    assert response.status_code == 200
    assert _ids(response.json()) == [str(second.id)]


async def test_get_sessions_invalid_params(client: AsyncClient) -> None:
    """Out-of-range pagination and unknown enum values are rejected with 422."""
    for params in (
        {"limit": MAX_PAGE_LIMIT + 1},
        {"limit": 0},
        {"offset": -1},
        {"source": "satellite"},
        {"status": "cancelled"},
        {"end_after": "not-a-date"},
    ):
        response = await client.get(SESSIONS_URL, params=params)
        assert response.status_code == 422, params


async def test_get_sessions_max_limit_accepted(client: AsyncClient) -> None:
    response = await client.get(SESSIONS_URL, params={"limit": MAX_PAGE_LIMIT})
    assert response.status_code == 200


async def test_get_sessions_predicted_json(
    client: AsyncClient,
    db_session: AsyncSession,
    make_predicted_session: Callable[..., Session],
    orbit_element: OrbitElement,
) -> None:
    """Predicted sessions have lowercase enums and all pass fields."""
    predicted = make_predicted_session(datetime.now(UTC) + timedelta(hours=1))
    db_session.add(predicted)
    await db_session.commit()

    response = await client.get(SESSIONS_URL)

    assert response.status_code == 200
    [item] = response.json()["data"]
    assert item["source"] == "predicted"
    assert item["status"] == "pending"
    assert item["min_elevation_deg"] == 15.0
    assert item["max_elevation_deg"] == 63.2
    assert item["rise_azimuth_deg"] == 215.0
    assert item["set_azimuth_deg"] == 40.5
    assert item["orbit_element_id"] == str(orbit_element.id)
    assert item["orphaned_at"] is None
    for field in ("rise_time", "peak_time", "set_time"):
        assert item[field] is not None


async def test_get_sessions_manual_json(client: AsyncClient, db_session: AsyncSession) -> None:
    """Manual sessions have source=manual and null pass fields."""
    await _add_session(db_session, timedelta(hours=1))

    [item] = (await client.get(SESSIONS_URL)).json()["data"]

    assert item["source"] == "manual"
    assert item["end_time"] is not None
    for field in (
        "rise_time",
        "peak_time",
        "set_time",
        "min_elevation_deg",
        "max_elevation_deg",
        "rise_azimuth_deg",
        "set_azimuth_deg",
        "orbit_element_id",
        "orphaned_at",
    ):
        assert item[field] is None, field


# ---------------------------------------------------GET /sessions/current--------------------------------------------------- #


async def test_get_current_session_running(client: AsyncClient, db_session: AsyncSession) -> None:
    running = await _add_session(db_session, timedelta(minutes=-2), minutes=7)
    await _add_session(db_session, timedelta(minutes=30))

    response = await client.get(f"{SESSIONS_URL}current")

    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(running.id)


async def test_get_current_session_upcoming(client: AsyncClient, db_session: AsyncSession) -> None:
    await _add_session(db_session, timedelta(hours=-1))
    upcoming = await _add_session(db_session, timedelta(minutes=30))

    response = await client.get(f"{SESSIONS_URL}current")

    assert response.status_code == 200
    assert response.json()["data"]["id"] == str(upcoming.id)


async def test_get_current_session_none(client: AsyncClient, db_session: AsyncSession) -> None:
    await _add_session(db_session, timedelta(hours=-1))

    response = await client.get(f"{SESSIONS_URL}current")

    assert response.status_code == 200
    assert response.json() == {"data": None}


# --------------------------------------------------GET /sessions/{session_id}-------------------------------------------------- #


async def test_get_session_by_id(client: AsyncClient, db_session: AsyncSession) -> None:
    session = await _add_session(db_session, timedelta(hours=1))

    response = await client.get(f"{SESSIONS_URL}{session.id}")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == str(session.id)
    assert data["source"] == "manual"


async def test_get_session_by_id_not_found(client: AsyncClient) -> None:
    response = await client.get(f"{SESSIONS_URL}{uuid4()}")
    assert response.status_code == 404


async def test_get_session_by_id_invalid_uuid(client: AsyncClient) -> None:
    response = await client.get(f"{SESSIONS_URL}not-a-uuid")
    assert response.status_code == 422


# --------------------------------------------------------------Auth-------------------------------------------------------------- #


def test_session_endpoints_require_auth() -> None:
    unauthenticated = TestClient(app)
    for path in ("", "current", str(uuid4())):
        response = unauthenticated.get(f"{SESSIONS_URL}{path}", follow_redirects=False)
        assert response.status_code == 401, path
