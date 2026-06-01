from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from config.config import settings
from config.keycloak_config import KeycloakConfig
from data.data_wrappers.wrappers import MCCUsersWrapper
from data.tables.mcc_user_tables import MCCUsers
from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from jwcrypto.jwt import JWTExpired
from keycloak import KeycloakError, KeycloakOpenID


class KeycloakClient:
    """Encapsulating class for MCC authentication/authorization variables and functions."""

    def __init__(self, config: KeycloakConfig) -> None:
        self.config = config
        self.internal_client = KeycloakOpenID(
            server_url=config.host,
            realm_name=config.realm,
            client_id=config.client_id,
            client_secret_key=config.client_secret,
        )
        self.external_client = KeycloakOpenID(
            server_url=config.external_url,
            realm_name=config.realm,
            client_id=config.client_id,
            client_secret_key=config.client_secret,
        )
        self.require_auth = Depends(self.authenticate)

    @property
    def login_url(self) -> str:
        """Returns keycloak login URL."""
        return self.external_client.auth_url(
            redirect_uri=self.config.callback_url,
            scope="openid profile email",
        )

    def logout_url(self, id_token: str) -> str:
        """Returns keycloak logout URL."""
        params = urlencode(
            {
                "client_id": self.config.client_id,
                "post_logout_redirect_uri": self.config.redirect_uri,
                "id_token_hint": id_token,
            }
        )
        return f"{self.config.external_url}/realms/{self.config.realm}/protocol/openid-connect/logout?{params}"

    def get_tokens(self, code: str) -> dict[str, Any]:
        """Makes API call to keycloak service to get user tokens."""
        return self.internal_client.token(
            grant_type="authorization_code",
            code=code,
            redirect_uri=self.config.callback_url,
        )

    def decode_token(self, token: str) -> dict[str, Any]:
        """Decodes and verifies keycloak tokens via JWKS signature verification."""
        try:
            claims: dict[str, Any] = self.internal_client.decode_token(token)
        except JWTExpired as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired") from e
        except KeycloakError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e
        aud = claims.get("aud")
        if isinstance(aud, str):
            aud = [aud]
        if self.config.client_id not in (aud or []):
            raise ValueError("Invalid token audience")
        return claims

    def authenticate(self, request: Request) -> dict[str, Any]:
        """Authenticates user tokens."""
        access_token = request.cookies.get("access_token")
        if not access_token:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        try:
            return self.decode_token(access_token)
        except KeycloakError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from e

    def get_current_user(self, request: Request) -> MCCUsers:
        """Authenticates user tokens and yields their corresponding MCCUsers objects."""
        user_info = self.authenticate(request)
        try:
            return MCCUsersWrapper().get_by_id(UUID(user_info["sub"]))
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found") from e


keycloak = KeycloakClient(settings.keycloak)
