from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from app.data.enums.satellite import SatelliteStatus
from app.data.enums.transactional import SessionStatus
from app.data.models.transactional_models import CommsSession
from httpx import ASGITransport, AsyncClient
from main import app
from sqlmodel.ext.asyncio.session import AsyncSession


STATUS_URL = "/api/mcc/status/status"


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """AsyncClient with no auth overrides (status endpoint is unauthenticated)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def create_session(db_session: AsyncSession, status: SessionStatus, started_minutes_ago: int = 30) -> CommsSession:
    """
    Insert a 5 minute comms session with the given status.

    :param db_session: test database session.
    :param status: status to give the session.
    :param started_minutes_ago: how long ago the session started.
    :return: the created session.
    """
    start = datetime.now(UTC) - timedelta(minutes=started_minutes_ago)
    session = CommsSession(id=uuid4(), start_time=start, end_time=start + timedelta(minutes=5), status=status)
    db_session.add(session)
    await db_session.commit()
    return session


async def test_status_offline_when_no_session(client: AsyncClient) -> None:
    """Test that the status is offline when no session has been recorded."""
    response = await client.get(STATUS_URL)

    assert response.status_code == 200
    response_body = response.json()
    assert response_body["status"] == SatelliteStatus.OFFLINE
    assert response_body["last_contact"] == "Never"
    assert response_body["session_duration"] == "--"
    assert response_body["telemetry_data"] == []


@pytest.mark.parametrize(
    ("session_status", "expected"),
    [
        (SessionStatus.PENDING, SatelliteStatus.PENDING),
        (SessionStatus.SCHEDULED, SatelliteStatus.SCHEDULED),
        (SessionStatus.ONGOING, SatelliteStatus.ONLINE),
        (SessionStatus.COMPLETED, SatelliteStatus.COMPLETED),
    ],
)
async def test_status_maps_to_each_session_status(
    client: AsyncClient, db_session: AsyncSession, session_status: SessionStatus, expected: SatelliteStatus
) -> None:
    """Test that every session status is mapped to its matching satellite status."""
    await create_session(db_session, session_status)

    response = await client.get(STATUS_URL)
    assert response.status_code == 200
    assert response.json()["status"] == expected


async def test_status_uses_most_recent_session(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test that the status comes from the session with the most recent start time."""
    await create_session(db_session, SessionStatus.PENDING, started_minutes_ago=30)
    await create_session(db_session, SessionStatus.ONGOING, started_minutes_ago=10)

    response = await client.get(STATUS_URL)
    assert response.json()["status"] == SatelliteStatus.ONLINE


async def test_status_reports_contact_and_duration(client: AsyncClient, db_session: AsyncSession) -> None:
    """Test that last contact and session duration are computed from the session times."""
    await create_session(db_session, SessionStatus.COMPLETED, started_minutes_ago=30)

    response = await client.get(STATUS_URL)
    response_body = response.json()

    assert response_body["last_contact"] == "25 min ago"
    assert response_body["session_duration"] == "5 min"
