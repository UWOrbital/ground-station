import pytest
import json
import backend.api.v1.mcc.endpoints.users as mcc_users
from uuid import UUID
from unittest.mock import patch, PropertyMock, MagicMock
from mcc_keycloak.client import KeycloakClient
from fastapi.testclient import TestClient
from data.tables.mcc_user_tables import MCCUsers
from main import app
from config.config import settings

# MOCK_USER = MagicMock()
# MOCK_USER.id = UUID("E621E1F8-C36C-495A-93FC-0C247A3E6E5F")
# MOCK_USER.email = "test@uworbital.com"
# MOCK_USER.first_name = "first_name"
# MOCK_USER.last_name = "last_name"
# MOCK_USER.phone_number = ""

MOCK_USER = MCCUsers(
    id=UUID("E621E1F8-C36C-495A-93FC-0C247A3E6E5F"),
    email="test@uworbital.com",
    first_name="first_name",
    last_name="last_name",
    phone_number=""
)

MOCK_USER_GET_EXPECTED = {
    "id": "E621E1F8-C36C-495A-93FC-0C247A3E6E5F".lower(),
    "email": "test@uworbital.com",
    "first_name": "first_name",
    "last_name": "last_name",
    "phone_number": ""
}

USERS_PREFIX = "/api/v1/mcc/users"

@pytest.fixture
def client():
    app.dependency_overrides[mcc_users.keycloak.get_current_user] = lambda: MOCK_USER
    app.dependency_overrides[mcc_users.keycloak.authenticate] = lambda: {}
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_users_get_endpoint(client):
    """Test that get /me returns the expected user"""

    with patch.object(mcc_users.MCCUsersWrapper, "get_by_id", return_value=MOCK_USER):
        response = client.get(f"{USERS_PREFIX}/me", follow_redirects=False)

    assert response.status_code == 200
    assert response.json() == MOCK_USER_GET_EXPECTED


def test_users_get_endpoint_unauthenticated():
    """Test that get /me provides status code 401 when the user is not properly authenticated"""
    client = TestClient(app)
    with patch.object(mcc_users.MCCUsersWrapper, "get_by_id", return_value=MOCK_USER):
        response = client.get(f"{USERS_PREFIX}/me", follow_redirects=False)

    assert response.status_code == 401

def test_users_update_endpoint(client):
    """Test that patch /me updates and returns the user."""
    MOCK_USER.first_name = "updated_first_name"
    MOCK_USER.last_name = "updated_last_name"

    with patch.object(mcc_users.MCCUsersWrapper, "update", return_value=MOCK_USER) as mock_update:
        response = client.patch(f"{USERS_PREFIX}/me", json={"first_name": "updated_first_name", "last_name": "updated_last_name"})

    assert response.status_code == 200
    assert response.json()["first_name"] == "updated_first_name"
    assert response.json()["last_name"] == "updated_last_name"
    mock_update.assert_called_once_with(UUID("E621E1F8-C36C-495A-93FC-0C247A3E6E5F"), {"first_name": "updated_first_name", "last_name": "updated_last_name"})

    MOCK_USER.first_name = "first_name"
    MOCK_USER.last_name = "last_name"


def test_users_delete_endpoint(client):
    """Test that me endpoint can handle delete users by their id"""
    with patch.object(mcc_users.MCCUsersWrapper, "delete_by_id", return_value=MOCK_USER) as mock_delete_by_id:
        response = client.delete(f"{USERS_PREFIX}/me", follow_redirects=False)

    assert response.status_code == 200
    mock_delete_by_id.assert_called_once_with(MOCK_USER.id)
