from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.aro.auth.aro_session import create_access_token
from app.data.repositories.dal import DAL
from app.data.enums.aro_requests import ARORequestStatus
from app.data.enums.transactional import MainPacketType
from app.data.models.aro_user_models import AROUsers
from main import app

REQUESTS_URL = "/api/aro/requests/"


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


async def _make_user(email: str) -> AROUsers:
    """Create an ARO user to own picture requests."""
    return await DAL.aro_users().create({"email": email, "first_name": "Test"})


def _headers(user: AROUsers) -> dict[str, str]:
    """Bearer auth headers for the given ARO user."""
    token, _ = create_access_token(user)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def user_a() -> AROUsers:
    return await _make_user("a@test.com")


@pytest_asyncio.fixture
async def user_b() -> AROUsers:
    return await _make_user("b@test.com")


@pytest.fixture
def payload() -> dict[str, str]:
    return {"latitude": "12.345", "longitude": "123.456"}


# --------------------------------------------------------------------------- #
# POST /
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_create_returns_data_and_delete_operation(client, user_a, payload):
    response = await client.post(REQUESTS_URL, json=payload, headers=_headers(user_a))

    assert response.status_code == 200
    body = response.json()["data"]
    assert body["status"] == ARORequestStatus.PENDING
    assert Decimal(body["latitude"]) == Decimal(payload["latitude"])

    operations = body["operations"]
    assert "delete" in operations
    assert operations["delete"]["url"].endswith(f"/api/aro/requests/{body['id']}")
    assert operations["delete"]["deletable_until"] is not None
    # No packet yet -> no download operation.
    assert "download" not in operations


@pytest.mark.asyncio
async def test_create_requires_auth(client, payload):
    response = await client.post(REQUESTS_URL, json=payload)
    assert response.status_code == 401


# --------------------------------------------------------------------------- #
# GET /
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_list_returns_newest_first_and_paginates(client, user_a, payload):
    headers = _headers(user_a)
    for _ in range(3):
        assert (await client.post(REQUESTS_URL, json=payload, headers=headers)).status_code == 200

    # First page of 2 -> newest first, a `next` link, no `previous`.
    page1 = (await client.get(REQUESTS_URL, params={"count": 2, "offset": 0}, headers=headers)).json()
    assert len(page1["data"]) == 2
    created = [datetime.fromisoformat(item["created_on"]) for item in page1["data"]]
    assert created == sorted(created, reverse=True)
    assert "next" in page1["operations"]
    assert "previous" not in page1["operations"]

    # Second page -> remaining item, a `previous` link, no `next`.
    page2 = (await client.get(REQUESTS_URL, params={"count": 2, "offset": 2}, headers=headers)).json()
    assert len(page2["data"]) == 1
    assert "previous" in page2["operations"]
    assert "next" not in page2["operations"]


@pytest.mark.asyncio
async def test_list_is_scoped_to_current_user(client, user_a, user_b, payload):
    assert (await client.post(REQUESTS_URL, json=payload, headers=_headers(user_a))).status_code == 200

    body = (await client.get(REQUESTS_URL, headers=_headers(user_b))).json()
    assert body["data"] == []


# --------------------------------------------------------------------------- #
# GET /{id}/packet
# --------------------------------------------------------------------------- #


async def _seed_request_with_packet(aro_id) -> tuple[str, bytes]:
    """Create a request whose packet is populated, returning (request_id, raw bytes)."""
    session = await DAL.comms_sessions().create(
        {
            "start_time": datetime.now(UTC),
            "end_time": datetime.now(UTC) + timedelta(minutes=5),
        }
    )
    raw = b"\x01\x02\x03\x04"
    packet = await DAL.packets().create(
        {
            "session_id": session.id,
            "raw_data": raw,
            "type_": MainPacketType.UPLINK,
            "payload_data": raw,
            "offset": 0,
        }
    )
    request = await DAL.aro_requests().create(
        {
            "aro_id": aro_id,
            "latitude": Decimal("12.345"),
            "longitude": Decimal("123.456"),
            "delete_deadline": datetime.now(UTC) + timedelta(hours=24),
            "packet_id": packet.id,
        }
    )
    return str(request.id), raw


@pytest.mark.asyncio
async def test_download_packet_returns_bytes(client, user_a):
    request_id, raw = await _seed_request_with_packet(user_a.id)

    response = await client.get(f"/api/aro/requests/{request_id}/packet", headers=_headers(user_a))

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/octet-stream"
    assert response.content == raw

    # The list response now advertises the download operation.
    body = (await client.get(REQUESTS_URL, headers=_headers(user_a))).json()
    assert "download" in body["data"][0]["operations"]


@pytest.mark.asyncio
async def test_download_packet_404_when_no_packet(client, user_a, payload):
    created = (await client.post(REQUESTS_URL, json=payload, headers=_headers(user_a))).json()["data"]

    response = await client.get(f"/api/aro/requests/{created['id']}/packet", headers=_headers(user_a))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_download_packet_404_for_other_user(client, user_a, user_b):
    request_id, _ = await _seed_request_with_packet(user_a.id)

    response = await client.get(f"/api/aro/requests/{request_id}/packet", headers=_headers(user_b))
    assert response.status_code == 404


# --------------------------------------------------------------------------- #
# DELETE /{id}
# --------------------------------------------------------------------------- #


@pytest.mark.asyncio
async def test_delete_pending_request(client, user_a, payload):
    created = (await client.post(REQUESTS_URL, json=payload, headers=_headers(user_a))).json()["data"]

    response = await client.delete(f"/api/aro/requests/{created['id']}", headers=_headers(user_a))
    assert response.status_code == 200
    assert response.json()["data"]["id"] == created["id"]

    # It is gone from the list.
    body = (await client.get(REQUESTS_URL, headers=_headers(user_a))).json()
    assert body["data"] == []


@pytest.mark.asyncio
async def test_delete_non_deletable_request_conflicts(client, user_a, payload):
    created = (await client.post(REQUESTS_URL, json=payload, headers=_headers(user_a))).json()["data"]
    # Move it out of the deletable PENDING state.
    from uuid import UUID

    await DAL.aro_requests().update(UUID(created["id"]), {"status": ARORequestStatus.SCHEDULED})

    response = await client.delete(f"/api/aro/requests/{created['id']}", headers=_headers(user_a))
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_unknown_request_404(client, user_a):
    unknown = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"/api/aro/requests/{unknown}", headers=_headers(user_a))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_other_users_request_404(client, user_a, user_b, payload):
    created = (await client.post(REQUESTS_URL, json=payload, headers=_headers(user_a))).json()["data"]

    response = await client.delete(f"/api/aro/requests/{created['id']}", headers=_headers(user_b))
    assert response.status_code == 404
