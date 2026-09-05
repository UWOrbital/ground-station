from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest_asyncio
from app.data.data_wrappers.wrappers import MCCUsersWrapper
from app.data.enums.mcc_users import MCCAdminRequestStatus
from app.data.models.mcc_user_models import MCCUsers
from app.mcc_keycloak.client import keycloak
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from main import app

ADMIN_PREFIX = "/api/v1/mcc/admin"


@pytest_asyncio.fixture
async def mcc_user(db_session):
    """Create a test MCC user with no admin access request."""
    user = MCCUsers(id=uuid4(), email="requester@uworbital.ca", phone_number=None)
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def pending_user(db_session):
    """Create a test MCC user with a pending admin access request."""
    user = MCCUsers(
        id=uuid4(), email="pending@uworbital.ca", phone_number=None, admin_request_status=MCCAdminRequestStatus.PENDING
    )
    db_session.add(user)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def client(mcc_user):
    """AsyncClient authenticated as a non-admin MCC user."""
    app.dependency_overrides[keycloak.get_current_user] = lambda: mcc_user
    app.dependency_overrides[keycloak.authenticate] = lambda: {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def admin_client():
    """AsyncClient authenticated as an MCC admin."""
    app.dependency_overrides[keycloak.get_current_admin] = lambda: None
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


async def test_request_admin_access_success(client: AsyncClient) -> None:
    """Test that a non-admin user can submit an admin access request."""
    response = await client.post(f"{ADMIN_PREFIX}/request")

    assert response.status_code == 200
    assert response.json()["admin_request_status"] == MCCAdminRequestStatus.PENDING


async def test_request_admin_access_duplicate(client: AsyncClient) -> None:
    """Test that a second request while already pending is rejected."""
    first = await client.post(f"{ADMIN_PREFIX}/request")
    assert first.status_code == 200

    second = await client.post(f"{ADMIN_PREFIX}/request")
    assert second.status_code == 409


async def test_request_admin_access_already_admin(client: AsyncClient, mcc_user: MCCUsers) -> None:
    """Test that a user already approved as admin cannot request access again."""
    mcc_user.admin_request_status = MCCAdminRequestStatus.APPROVED

    response = await client.post(f"{ADMIN_PREFIX}/request")

    assert response.status_code == 409


async def test_get_pending_admin_requests(admin_client: AsyncClient, pending_user: MCCUsers, mcc_user: MCCUsers) -> None:
    """Test that only users with a pending request are listed."""
    response = await admin_client.get(f"{ADMIN_PREFIX}/requests")

    assert response.status_code == 200
    returned_ids = {u["id"] for u in response.json()["data"]}
    assert str(pending_user.id) in returned_ids
    assert str(mcc_user.id) not in returned_ids


async def test_get_pending_admin_requests_forbidden_without_admin_role() -> None:
    """Test that a non-admin authenticated user is forbidden from listing requests."""
    with patch.object(keycloak, "authenticate", new_callable=AsyncMock, return_value={"sub": str(uuid4())}):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get(f"{ADMIN_PREFIX}/requests")

    assert response.status_code == 403


async def test_approve_admin_request_success(admin_client: AsyncClient, pending_user: MCCUsers) -> None:
    """Test that approving a pending request updates its status and grants the Keycloak role."""
    with patch.object(keycloak, "grant_mcc_admin", new_callable=AsyncMock, return_value=None) as mock_grant:
        response = await admin_client.patch(f"{ADMIN_PREFIX}/requests/{pending_user.id}", json={"status": "approved"})

    assert response.status_code == 200
    assert response.json()["admin_request_status"] == MCCAdminRequestStatus.APPROVED
    mock_grant.assert_called_once_with(pending_user.id)


async def test_reject_admin_request_success(admin_client: AsyncClient, pending_user: MCCUsers) -> None:
    """Test that rejecting a pending request updates its status without granting Keycloak access."""
    with patch.object(keycloak, "grant_mcc_admin", new_callable=AsyncMock, return_value=None) as mock_grant:
        response = await admin_client.patch(f"{ADMIN_PREFIX}/requests/{pending_user.id}", json={"status": "rejected"})

    assert response.status_code == 200
    assert response.json()["admin_request_status"] == MCCAdminRequestStatus.REJECTED
    mock_grant.assert_not_called()


async def test_approve_admin_request_not_pending(admin_client: AsyncClient, mcc_user: MCCUsers) -> None:
    """Test that deciding on a user without a pending request returns a conflict."""
    response = await admin_client.patch(f"{ADMIN_PREFIX}/requests/{mcc_user.id}", json={"status": "approved"})

    assert response.status_code == 409


async def test_approve_admin_request_user_not_found(admin_client: AsyncClient) -> None:
    """Test that deciding on a nonexistent user returns 404."""
    response = await admin_client.patch(f"{ADMIN_PREFIX}/requests/{uuid4()}", json={"status": "approved"})

    assert response.status_code == 404


async def test_approve_admin_request_invalid_status(admin_client: AsyncClient, pending_user: MCCUsers) -> None:
    """Test that submitting a non-decision status value is rejected by validation."""
    response = await admin_client.patch(f"{ADMIN_PREFIX}/requests/{pending_user.id}", json={"status": "pending"})

    assert response.status_code == 422


async def test_approve_admin_request_keycloak_failure_keeps_pending(
    admin_client: AsyncClient, pending_user: MCCUsers
) -> None:
    """Test that a Keycloak grant failure surfaces 502 and leaves the request pending."""
    keycloak_error = HTTPException(status_code=502, detail="MCC admin group not configured in Keycloak")
    with patch.object(keycloak, "grant_mcc_admin", new_callable=AsyncMock, side_effect=keycloak_error):
        response = await admin_client.patch(f"{ADMIN_PREFIX}/requests/{pending_user.id}", json={"status": "approved"})

    assert response.status_code == 502

    refreshed = await MCCUsersWrapper().get_by_id(pending_user.id)
    assert refreshed.admin_request_status == MCCAdminRequestStatus.PENDING
