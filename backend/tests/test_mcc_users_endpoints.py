import pytest
import app.api.v1.mcc.routes.users as mcc_users
from uuid import UUID
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from app.data.models.mcc_user_models import MCCUsers
from app.data.repositories.dal import DAL
from main import app

from app.api.v1.mcc.schemas.responses import UserInformationResponse

MOCK_USER = MCCUsers(
    id=UUID("E621E1F8-C36C-495A-93FC-0C247A3E6E5F"),
    email="test@uworbital.com",
    first_name="first_name",
    last_name="last_name",
    phone_number=""
)

MOCK_USER_EXPECTED_RESPONSE = UserInformationResponse(
    id=UUID("E621E1F8-C36C-495A-93FC-0C247A3E6E5F"),
    email="test@uworbital.com",
    first_name="first_name",
    last_name="last_name",
    phone_number=""
)

USERS_PREFIX = "/api/v1/mcc/users"

# The DI provider the users routes depend on; overriding this key swaps the repo.
MCC_USERS_PROVIDER = DAL.get_repo(DAL.mcc_users)


@pytest.fixture
def mock_mcc_users_repo():
    """A stand-in MCCUsersRepository whose DB methods are AsyncMocks."""
    repo = MagicMock()
    repo.update = AsyncMock(return_value=MOCK_USER)
    repo.delete_by_id = AsyncMock(return_value=MOCK_USER)
    return repo


@pytest.fixture
def client(mock_mcc_users_repo):
    app.dependency_overrides[mcc_users.keycloak.get_current_user] = lambda: MOCK_USER
    app.dependency_overrides[mcc_users.keycloak.authenticate] = lambda: {}
    app.dependency_overrides[MCC_USERS_PROVIDER] = lambda: mock_mcc_users_repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_users_get_endpoint(client):
    """Test that get /me returns the expected user"""
    response = client.get(f"{USERS_PREFIX}/me", follow_redirects=False)

    assert response.status_code == 200
    assert response.json() == MOCK_USER_EXPECTED_RESPONSE.model_dump(mode="json")


def test_users_get_endpoint_unauthenticated():
    """Test that get /me provides status code 401 when the user is not properly authenticated"""
    client = TestClient(app)
    response = client.get(f"{USERS_PREFIX}/me", follow_redirects=False)

    assert response.status_code == 401


def test_users_update_endpoint(client, mock_mcc_users_repo):
    """Test that patch /me updates and returns the user."""
    MOCK_USER.email = "updated_email@uworbital.com"
    MOCK_USER.first_name = "updated_first_name"
    MOCK_USER.last_name = "updated_last_name"
    MOCK_USER.phone_number = "1234"

    payload = {
        "email": "updated_email@uworbital.com",
        "first_name": "updated_first_name",
        "last_name": "updated_last_name",
        "phone_number": "1234",
    }

    with patch_keycloak("sync_user_changes") as mock_sync_changes:
        response = client.patch(f"{USERS_PREFIX}/me", json=payload)

    assert response.status_code == 200
    assert response.json()["first_name"] == payload["first_name"]
    assert response.json()["last_name"] == payload["last_name"]
    assert response.json()["phone_number"] == payload["phone_number"]
    mock_mcc_users_repo.update.assert_called_once_with(MOCK_USER.id, payload)
    mock_sync_changes.assert_called_once_with(MOCK_USER.id, payload)

    MOCK_USER.email = "test@uworbital.com"
    MOCK_USER.first_name = "first_name"
    MOCK_USER.last_name = "last_name"
    MOCK_USER.phone_number = ""


def test_users_update_endpoint_failure(client, mock_mcc_users_repo):
    """Test that patch /me does not call keycloak sync if DB fails to update."""
    MOCK_USER.first_name = "updated_first_name"
    MOCK_USER.last_name = "updated_last_name"

    payload = {
        "first_name": "updated_first_name",
        "last_name": "updated_last_name",
    }

    mock_mcc_users_repo.update.side_effect = RuntimeError()
    with patch_keycloak("sync_user_changes") as mock_sync_changes:
        response = client.patch(f"{USERS_PREFIX}/me", json=payload)

    assert response.status_code == 500
    mock_sync_changes.assert_not_called()

    MOCK_USER.first_name = "first_name"
    MOCK_USER.last_name = "last_name"


def test_users_delete_endpoint(client, mock_mcc_users_repo):
    """Test that delete /me can handle delete users by their id."""
    with patch_keycloak("sync_user_deletion") as mock_sync_deletion:
        response = client.delete(f"{USERS_PREFIX}/me", follow_redirects=False)

    assert response.status_code == 200
    mock_mcc_users_repo.delete_by_id.assert_called_once_with(MOCK_USER.id)
    mock_sync_deletion.assert_called_once_with(MOCK_USER.id)


def test_users_delete_endpoint_failure(client, mock_mcc_users_repo):
    """Test that delete /me does not call keycloak sync if DB fails to update."""
    mock_mcc_users_repo.delete_by_id.side_effect = ValueError()
    with patch_keycloak("sync_user_deletion") as mock_sync_deletion:
        response = client.delete(f"{USERS_PREFIX}/me", follow_redirects=False)

    assert response.status_code == 404
    mock_sync_deletion.assert_not_called()


def patch_keycloak(method_name):
    """Patch a keycloak sync method with an AsyncMock returning None.

    :param method_name: the KeycloakClient coroutine to replace.
    :return: the unittest.mock patcher context manager.
    """
    return patch.object(mcc_users.keycloak, method_name, new_callable=AsyncMock, return_value=None)
