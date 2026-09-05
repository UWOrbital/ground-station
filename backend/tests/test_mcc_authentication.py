import pytest
import json
from uuid import uuid4
import app.api.v1.mcc.routes.auth as mcc_auth
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from app.data.data_wrappers.wrappers import MCCUsersWrapper
from app.data.models.mcc_user_models import MCCUsers
from app.mcc_keycloak.client import KeycloakClient, keycloak
from app.config.env_settings.keycloak_config import KeycloakConfig
from fastapi import HTTPException
from fastapi.testclient import TestClient
from keycloak.exceptions import KeycloakGetError
from main import app
from app.config.env_settings.backend_config import settings

MOCK_TOKENS = {
    "access_token": "mock_access_token",
    "id_token": "mock_id_token",
    "refresh_token": "mock_refresh_token"
}

MOCK_USER_INFO = {
    "sub": "E621E1F8-C36C-495A-93FC-0C247A3E6E5F",
    "email": "test@uworbital.com",
    "preferred_username": "mcc-admin"
}

MOCK_BAD_USER_INFO = {
    "sub": "bad_id",
    "email": "bad_email",
}

AUTH_PREFIX = "/api/v1/mcc/auth"

@pytest.fixture
def client():
    return TestClient(app)


def test_login_endpoint(client):
    """Test that login endpoint sends a redirect response with status code 303"""
    mock_url = f"http://mock-keycloak/auth/openid-connect/auth?client_id={settings.keycloak.client_id}"

    with patch.object(KeycloakClient, "login_url", new_callable=PropertyMock) as mock_login:
        mock_login.return_value = mock_url
        response = client.get(f"{AUTH_PREFIX}/login", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == mock_url


def test_callback_endpoint(client):
    """Test callback endpoint keycloak functions called properly"""
    with patch.object(mcc_auth.keycloak, "get_tokens", new_callable=AsyncMock, return_value=MOCK_TOKENS) as mock_get_tokens, \
         patch.object(mcc_auth.keycloak, "decode_token", new_callable=AsyncMock, return_value=MOCK_USER_INFO) as mock_decode_token, \
         patch.object(mcc_auth.MCCUsersWrapper, "create", new_callable=AsyncMock, return_value=None) as mock_create:

        response = client.get(f"{AUTH_PREFIX}/callback?code=temp_code", follow_redirects=False)

    mock_get_tokens.assert_called_once_with("temp_code")
    mock_decode_token.assert_called_once_with("mock_id_token")

    mock_create.assert_called_once_with({
        "id": MOCK_USER_INFO["sub"],
        "email": MOCK_USER_INFO["email"],
        "phone_number": "",
    })
    assert response.status_code == 302
    assert response.cookies["id_token"] == "mock_id_token"
    assert response.cookies["access_token"] == "mock_access_token"


def test_callback_endpoint_exceptions(client):
    """Test that callback endpoint can handle bad input (500 status code)"""
    with patch.object(mcc_auth.keycloak, "get_tokens", new_callable=AsyncMock, return_value=MOCK_TOKENS) as mock_get_tokens, \
         patch.object(mcc_auth.keycloak, "decode_token", new_callable=AsyncMock, return_value=MOCK_BAD_USER_INFO) as mock_decode_token:

        response = client.get(f"{AUTH_PREFIX}/callback?code=temp_code", follow_redirects=False)

    mock_get_tokens.assert_called_once_with("temp_code")
    mock_decode_token.assert_called_once_with("mock_id_token")

    assert response.status_code == 500
    assert json.loads(response.text)["detail"] == "User provisioning failed"


def test_logout_endpoint(client):
    """Test that logout endpoint sends a redirect reponse and clears cookies"""

    client.cookies.set("id_token", "mock_id_token")
    client.cookies.set("access_token", "mock_access_token")

    response = client.get(f"{AUTH_PREFIX}/logout", follow_redirects=False)

    assert response.status_code == 307
    assert "openid-connect/logout" in response.headers["location"]
    assert response.cookies.get("access_token") == None and response.cookies.get("id_token") == None


SINGLE_URL = "http://keycloak.example:8080"


def test_logout_url_uses_single_url():
    """Test that logout_url is built from the single configured Keycloak URL (no internal/public split)."""
    config = KeycloakConfig(url=SINGLE_URL, client_secret="dummy")
    client = KeycloakClient(config)

    logout_url = client.logout_url("mock_id_token")

    assert logout_url.startswith(f"{SINGLE_URL}/realms/{config.realm}/protocol/openid-connect/logout")
    assert "id_token_hint=mock_id_token" in logout_url


async def test_get_current_admin_allows_role_holder():
    """Test that get_current_admin returns the user when the token carries the mcc-admin role."""
    mock_user = MCCUsers(id=uuid4(), email="admin@uworbital.com", phone_number=None)
    request = MagicMock()

    with (
        patch.object(
            keycloak,
            "authenticate",
            new_callable=AsyncMock,
            return_value={"sub": str(mock_user.id), "realm_access": {"roles": ["mcc-admin"]}},
        ),
        patch.object(MCCUsersWrapper, "get_by_id", new_callable=AsyncMock, return_value=mock_user),
    ):
        result = await keycloak.get_current_admin(request)

    assert result == mock_user


async def test_get_current_admin_rejects_without_role():
    """Test that get_current_admin raises 403 when the token carries no mcc-admin role."""
    request = MagicMock()

    with patch.object(keycloak, "authenticate", new_callable=AsyncMock, return_value={"sub": str(uuid4())}):
        with pytest.raises(HTTPException) as exc_info:
            await keycloak.get_current_admin(request)

    assert exc_info.value.status_code == 403


async def test_grant_mcc_admin_adds_user_to_group():
    """Test that grant_mcc_admin resolves the admin group path and adds the user to it."""
    user_id = uuid4()

    with (
        patch.object(keycloak.admin_client, "get_group_by_path", return_value={"id": "group-id"}) as mock_get_group,
        patch.object(keycloak.admin_client, "group_user_add", return_value=None) as mock_add,
    ):
        await keycloak.grant_mcc_admin(user_id)

    mock_get_group.assert_called_once_with(keycloak.config.admin_group_path)
    mock_add.assert_called_once_with(user_id=str(user_id), group_id="group-id")


async def test_grant_mcc_admin_surfaces_missing_group():
    """Test that grant_mcc_admin raises 502 when the admin group can't be resolved in Keycloak."""
    with patch.object(
        keycloak.admin_client, "get_group_by_path", side_effect=KeycloakGetError(error_message="not found")
    ):
        with pytest.raises(HTTPException) as exc_info:
            await keycloak.grant_mcc_admin(uuid4())

    assert exc_info.value.status_code == 502
