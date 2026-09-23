from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.data.enums.aro_requests import ARORequestStatus
from app.data.models.aro_user_models import AROUsers
from app.data.models.transactional_models import ARORequest
from app.data.repositories.dal import DAL
from app.mcc_keycloak.client import keycloak
from main import app

REQUESTS_URL = "/api/mcc/requests/"

BASE_TIME = datetime(2025, 1, 1, tzinfo=UTC)


async def _make_user(email: str) -> AROUsers:
    """Create an ARO user to own picture requests."""
    return await DAL.aro_users().create({"email": email, "first_name": "Test"})


async def _make_request(aro_id: object, created_on: datetime) -> ARORequest:
    """Create an ARO picture request owned by the given user at a fixed time."""
    return await DAL.aro_requests().create(
        {
            "aro_id": aro_id,
            "latitude": Decimal("12.345"),
            "longitude": Decimal("123.456"),
            "created_on": created_on,
        }
    )


@pytest_asyncio.fixture
async def admin_client():
    """AsyncClient authenticated as an MCC admin."""
    app.dependency_overrides[keycloak.get_current_admin] = lambda: None
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def test_list_aro_requests_empty(admin_client: AsyncClient) -> None:
    """Test that an empty database returns an empty data list."""
    response = await admin_client.get(REQUESTS_URL)

    assert response.status_code == 200
    assert response.json()["data"] == []


async def test_list_aro_requests_returns_all_users(admin_client: AsyncClient) -> None:
    """Test that requests from every ARO user are returned, newest first."""
    user_a = await _make_user("a@test.com")
    user_b = await _make_user("b@test.com")
    req_a = await _make_request(user_a.id, BASE_TIME)
    req_b = await _make_request(user_b.id, BASE_TIME + timedelta(hours=1))

    response = await admin_client.get(REQUESTS_URL)

    assert response.status_code == 200
    data = response.json()["data"]
    ids = [item["id"] for item in data]
    # Both users' requests present, newest (req_b) first.
    assert ids == [str(req_b.id), str(req_a.id)]
    assert data[0]["aro_id"] == str(user_b.id)
    assert data[0]["status"] == ARORequestStatus.PENDING


async def test_list_aro_requests_pagination(admin_client: AsyncClient) -> None:
    """Test that count and offset page through the requests newest first."""
    user = await _make_user("paged@test.com")
    requests = [await _make_request(user.id, BASE_TIME + timedelta(hours=i)) for i in range(3)]
    newest_first = [str(r.id) for r in reversed(requests)]

    page1 = await admin_client.get(REQUESTS_URL, params={"count": 2, "offset": 0})
    page2 = await admin_client.get(REQUESTS_URL, params={"count": 2, "offset": 2})

    assert page1.status_code == 200
    assert page2.status_code == 200
    assert [item["id"] for item in page1.json()["data"]] == newest_first[:2]
    assert [item["id"] for item in page2.json()["data"]] == newest_first[2:]


async def test_list_aro_requests_invalid_pagination(admin_client: AsyncClient) -> None:
    """Test that out-of-range pagination params are rejected by validation."""
    assert (await admin_client.get(REQUESTS_URL, params={"count": 0})).status_code == 422
    assert (await admin_client.get(REQUESTS_URL, params={"offset": -1})).status_code == 422


async def test_list_aro_requests_forbidden_without_admin_role() -> None:
    """Test that an authenticated non-admin user is forbidden from listing requests."""
    with patch.object(keycloak, "authenticate", new_callable=AsyncMock, return_value={"sub": str(uuid4())}):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(REQUESTS_URL)

    assert response.status_code == 403
