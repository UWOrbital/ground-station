from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from app.api.mcc.routes.status import TELEMETRY_IDS
from app.data.enums.transactional import SessionStatus
from app.data.models.main_models import MainTelemetry
from app.data.models.transactional_models import Session, Telemetry
from httpx import ASGITransport, AsyncClient
from main import app
from sqlmodel.ext.asyncio.session import AsyncSession

STATUS_URL = "/api/mcc/status/status"


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """AsyncClient with no auth overrides.

    :return: an unauthenticated client.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _add_session(
    db_session: AsyncSession, start_offset: timedelta, minutes: int, status: SessionStatus
) -> Session:
    """Add a manual session starting relative to now.

    :param db_session: test database session
    :param start_offset: start time relative to the current time
    :param minutes: session length in minutes
    :param status: session status
    :return: the persisted session
    """
    start = datetime.now(UTC) + start_offset
    session = Session(start_time=start, end_time=start + timedelta(minutes=minutes), status=status)
    db_session.add(session)
    await db_session.commit()
    return session


async def test_status_no_sessions(client: AsyncClient) -> None:
    response = await client.get(STATUS_URL)

    assert response.status_code == 200
    assert response.json() == {
        "status": "offline",
        "last_contact": "--",
        "session_duration": "--",
        "telemetry_data": [],
    }


async def test_status_only_past_sessions(client: AsyncClient, db_session: AsyncSession) -> None:
    await _add_session(db_session, timedelta(hours=-2), 10, SessionStatus.COMPLETED)

    body = (await client.get(STATUS_URL)).json()

    assert body["status"] == "offline"
    assert body["last_contact"] == "--"
    assert body["session_duration"] == "--"


async def test_status_ongoing_session(client: AsyncClient, db_session: AsyncSession) -> None:
    await _add_session(db_session, timedelta(minutes=-5, seconds=-10), 10, SessionStatus.ONGOING)
    await _add_session(db_session, timedelta(hours=1), 10, SessionStatus.SCHEDULED)

    response = await client.get(STATUS_URL)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "online"
    assert body["last_contact"] == "Now"
    assert body["session_duration"] == "5 min"


async def test_status_session_just_started(client: AsyncClient, db_session: AsyncSession) -> None:
    """Under a minute into a session the duration is reported as less than a minute."""
    await _add_session(db_session, timedelta(seconds=-10), 10, SessionStatus.ONGOING)

    body = (await client.get(STATUS_URL)).json()

    assert body["session_duration"] == "Less than a minute"


@pytest.mark.parametrize("status", [SessionStatus.PENDING, SessionStatus.SCHEDULED])
async def test_status_upcoming_session(
    client: AsyncClient, db_session: AsyncSession, status: SessionStatus
) -> None:
    """Before the next session starts the satellite is idle.

    :param status: status of the upcoming session.
    """
    await _add_session(db_session, timedelta(hours=-2), 10, SessionStatus.COMPLETED)
    await _add_session(db_session, timedelta(minutes=30), 10, status)

    body = (await client.get(STATUS_URL)).json()

    assert body["status"] == "idle"
    assert body["last_contact"] == "--"
    assert body["session_duration"] == "--"


async def test_status_running_session_follows_db_status(client: AsyncClient, db_session: AsyncSession) -> None:
    """An active session that is still marked SCHEDULED should read as idle."""
    await _add_session(db_session, timedelta(minutes=-1), 10, SessionStatus.SCHEDULED)

    body = (await client.get(STATUS_URL)).json()

    assert body["status"] == "idle"
    assert body["last_contact"] == "Now"
    assert body["session_duration"] == "1 min"


async def test_status_telemetry_snapshot(client: AsyncClient, db_session: AsyncSession) -> None:
    """The newest telemetry per tracked type is returned. Untracked or missing types are skipped."""
    await _add_session(db_session, timedelta(minutes=30), 10, SessionStatus.SCHEDULED)
    tracked_with_data, tracked_without_data = list(TELEMETRY_IDS)[:2]
    untracked = max(TELEMETRY_IDS) + 1
    for main_id in (tracked_with_data, tracked_without_data, untracked):
        db_session.add(MainTelemetry(id=main_id, name=f"T{main_id}", format="int", data_size=1, total_size=1))
    await db_session.commit()

    base = datetime.now(UTC)
    db_session.add_all(
        [
            Telemetry(type_=tracked_with_data, value="old", timestamp=base - timedelta(minutes=5)),
            Telemetry(type_=tracked_with_data, value="new", timestamp=base),
            Telemetry(type_=untracked, value="ignored", timestamp=base),
        ]
    )
    await db_session.commit()

    body = (await client.get(STATUS_URL)).json()

    assert body["telemetry_data"] == [{"label": TELEMETRY_IDS[tracked_with_data], "value": "new", "unit": None}]


async def test_status_telemetry_null_value(client: AsyncClient, db_session: AsyncSession) -> None:
    """A reading without a decoded value is shown as N/A."""
    await _add_session(db_session, timedelta(minutes=30), 10, SessionStatus.SCHEDULED)
    telemetry_id = next(iter(TELEMETRY_IDS))
    db_session.add(MainTelemetry(id=telemetry_id, name="T", format="int", data_size=1, total_size=1))
    await db_session.commit()
    db_session.add(Telemetry(type_=telemetry_id, value=None))
    await db_session.commit()

    body = (await client.get(STATUS_URL)).json()

    assert body["telemetry_data"] == [{"label": TELEMETRY_IDS[telemetry_id], "value": "N/A", "unit": None}]
