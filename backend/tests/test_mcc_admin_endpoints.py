from unittest.mock import AsyncMock, patch
from uuid import uuid4
import pytest
import pytest_asyncio
from app.api.mcc.routes.admin import REQUEST_ACCESS_CONFLICT_DETAILS
from app.data.enums.mcc_users import MCCAdminRequestStatus
from app.data.models.mcc_user_models import MCCUsers
from app.data.repositories.repositories import MCCUsersRepository
from app.mcc_keycloak.client import keycloak
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient
from main import app

ADMIN_PREFIX = "/api/mcc/admin"

@pytest_asyncio.fixture
async def mcc_user(db_session):
    user = MCCUsers(id=uuid4(), email="requester@uworbital.ca", phone_number=None)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest_asyncio.fixture
async def pending_user(db_session):
    user = MCCUsers(id=uuid4(), email="pending@uworbital.ca", phone_number=None, admin_request_status=MCCAdminRequestStatus.PENDING)
    db_session.add(user)
    await db_session.commit()
    return user

@pytest_asyncio.fixture
async def client(mcc_user):
    app.dependency_overrides[keycloak.get_current_user] = lambda: mcc_user
    app.dependency_overrides[keycloak.authenticate] = lambda: {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac: yield ac
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def admin_client():
    app.dependency_overrides[keycloak.get_current_admin] = lambda: None
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac: yield ac
    app.dependency_overrides.clear()

async def test_request_admin_access_success(client: AsyncClient) -> None:
    response = await client.post(f"{ADMIN_PREFIX}/request-access")
    assert response.status_code == 200
    assert response.json()["admin_request_status"] == MCCAdminRequestStatus.PENDING

async def test_request_admin_access_duplicate(client: AsyncClient) -> None:
    assert (await client.post(f"{ADMIN_PREFIX}/request-access")).status_code == 200
    assert (await client.post(f"{ADMIN_PREFIX}/request-access")).status_code == 409

@pytest.mark.parametrize("status", [s for s in MCCAdminRequestStatus if s != MCCAdminRequestStatus.NOT_REQUESTED])
async def test_request_admin_access_blocked_unless_not_requested(client: AsyncClient, mcc_user: MCCUsers, status: MCCAdminRequestStatus) -> None:
    mcc_user.admin_request_status = status
    response = await client.post(f"{ADMIN_PREFIX}/request-access")
    assert response.status_code == 409
    assert response.json()["detail"] == REQUEST_ACCESS_CONFLICT_DETAILS[status]

async def test_get_admin_applicants(admin_client: AsyncClient, pending_user: MCCUsers, mcc_user: MCCUsers) -> None:
    response = await admin_client.get(f"{ADMIN_PREFIX}/applicants")
    assert response.status_code == 200
    returned_ids = {u["id"] for u in response.json()["data"]}
    assert str(pending_user.id) in returned_ids
    assert str(mcc_user.id) not in returned_ids

async def test_get_admin_applicants_forbidden_without_admin_role() -> None:
    with patch.object(keycloak, "authenticate", new_callable=AsyncMock, return_value={"sub": str(uuid4())}):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac: response = await ac.get(f"{ADMIN_PREFIX}/applicants")
    assert response.status_code == 403

async def test_approve_admin_request_success(admin_client: AsyncClient, pending_user: MCCUsers) -> None:
    with patch.object(keycloak, "grant_mcc_admin", new_callable=AsyncMock) as mock_grant: response = await admin_client.patch(f"{ADMIN_PREFIX}/applicants/{pending_user.id}", json={"status": "approved"})
    assert response.status_code == 200
    assert response.json()["admin_request_status"] == MCCAdminRequestStatus.APPROVED
    mock_grant.assert_called_once_with(pending_user.id)

async def test_reject_admin_request_success(admin_client: AsyncClient, pending_user: MCCUsers) -> None:
    with patch.object(keycloak, "grant_mcc_admin", new_callable=AsyncMock) as mock_grant: response = await admin_client.patch(f"{ADMIN_PREFIX}/applicants/{pending_user.id}", json={"status": "rejected"})
    assert response.status_code == 200
    assert response.json()["admin_request_status"] == MCCAdminRequestStatus.REJECTED
    mock_grant.assert_not_called()

async def test_approve_admin_request_not_pending(admin_client: AsyncClient, mcc_user: MCCUsers) -> None:
    assert (await admin_client.patch(f"{ADMIN_PREFIX}/applicants/{mcc_user.id}", json={"status": "approved"})).status_code == 409

async def test_approve_admin_request_user_not_found(admin_client: AsyncClient) -> None:
    assert (await admin_client.patch(f"{ADMIN_PREFIX}/applicants/{uuid4()}", json={"status": "approved"})).status_code == 404

async def test_approve_admin_request_invalid_status(admin_client: AsyncClient, pending_user: MCCUsers) -> None:
    assert (await admin_client.patch(f"{ADMIN_PREFIX}/applicants/{pending_user.id}", json={"status": "pending"})).status_code == 422

async def test_approve_admin_request_keycloak_failure_keeps_pending(admin_client: AsyncClient, pending_user: MCCUsers) -> None:
    with patch.object(keycloak, "grant_mcc_admin", new_callable=AsyncMock, side_effect=HTTPException(502)): response = await admin_client.patch(f"{ADMIN_PREFIX}/applicants/{pending_user.id}", json={"status": "approved"})
    assert response.status_code == 502
    assert (await MCCUsersRepository().get_by_id(pending_user.id)).admin_request_status == MCCAdminRequestStatus.PENDING
