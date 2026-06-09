import pytest
import json
import backend.api.v1.mcc.endpoints.auth as mcc_auth
from unittest.mock import patch, PropertyMock
from mcc_keycloak.client import KeycloakClient
from fastapi.testclient import TestClient
from main import app
from config.config import settings

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
    with patch.object(mcc_auth.keycloak, "get_tokens", return_value=MOCK_TOKENS) as mock_get_tokens, \
         patch.object(mcc_auth.keycloak, "decode_token", return_value=MOCK_USER_INFO) as mock_decode_token, \
         patch.object(mcc_auth.MCCUsersWrapper, "create", return_value=None) as mock_create:

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
    with patch.object(mcc_auth.keycloak, "get_tokens", return_value=MOCK_TOKENS) as mock_get_tokens, \
         patch.object(mcc_auth.keycloak, "decode_token", return_value=MOCK_BAD_USER_INFO) as mock_decode_token:

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
