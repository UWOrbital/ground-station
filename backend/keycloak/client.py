from typing import Any
from urllib.parse import urlencode

import httpx
from config.config import settings
from config.keycloak_config import KeycloakConfig
from jose import jwt


class KeycloakClient:
    """
    Encapsulating class for MCC authentication/authorization variables andfunctions.
    """

    def __init__(self, config: KeycloakConfig) -> None:
        self.config = config

    @property
    def _params(self) -> str:
        """
        Protected property for creating login params.
        """
        return urlencode(
            {
                "client_id": self.config.client_id,
                "response_type": "code",
                "scope": "openid profile email",
                "redirect_uri": self.config.callback_url,
            }
        )

    @property
    def login_url(self) -> str:
        """
        Returns keycloak login URL.
        """
        return f"http://localhost:8080/realms/{self.config.realm}/protocol/openid-connect/auth?{self._params}"

    def get_tokens(self, code: str) -> dict[str, Any]:
        """
        Makes API call to keycloak service to get user tokens
        """
        with httpx.Client() as client:
            response = client.post(
                f"{self.config.url}/realms/{self.config.realm}/protocol/openid-connect/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "code": code,
                    "redirect_uri": self.config.callback_url,
                },
            )
            return response.json()  # type: ignore[no-any-return]

    def decode_id_token(self, id_token: str) -> dict[str, Any]:
        """
        Decodes user id token to get user information
        """
        return jwt.decode(  # type: ignore[no-any-return]
            id_token,
            key="",
            options={
                "verify_signature": False,
                "verify_aud": False,
                "verify_at_hash": False,
            },
        )


keycloak = KeycloakClient(settings.keycloak)
