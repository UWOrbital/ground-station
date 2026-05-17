from typing import Any
from urllib.parse import urlencode

import httpx
from config.config import settings
from config.keycloak_config import KeycloakConfig
from jose import jwt


class KeycloakClient:
    """
    Encapsulating class for MCC authentication/authorization variables and functions.
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
        return f"{self.config.external_url}/realms/{self.config.realm}/protocol/openid-connect/auth?{self._params}"

    def logout_url(self, id_token: str) -> str:
        """
        Returns keycloak logout URL, requiring the user's id token for hinting purposes
        """
        params = urlencode(
            {
                "client_id": self.config.client_id,
                "post_logout_redirect_uri": self.config.redirect_uri,
                "id_token_hint": id_token,
            }
        )
        return f"{self.config.external_url}/realms/{self.config.realm}/protocol/openid-connect/logout?{params}"

    def get_tokens(self, code: str) -> dict[str, Any]:
        """
        Makes API call to keycloak service to get user tokens
        """
        with httpx.Client() as client:
            response = client.post(
                f"{self.config.host}/realms/{self.config.realm}/protocol/openid-connect/token",
                data={
                    "grant_type": "authorization_code",
                    "client_id": self.config.client_id,
                    "client_secret": self.config.client_secret,
                    "code": code,
                    "redirect_uri": self.config.callback_url,
                },
            )

        response.raise_for_status()

        tokens: dict[str, Any] = response.json()

        if "error" in tokens:
            raise ValueError("Keycloak token exchange failed")

        return tokens

    def decode_id_token(self, id_token: str) -> dict[str, Any]:
        """
        Decodes and verifies user id token via JWKS signature verification.
        """
        with httpx.Client() as client:
            response = client.get(f"{self.config.host}/realms/{self.config.realm}/protocol/openid-connect/certs")
        response.raise_for_status()
        jwks = response.json()

        return jwt.decode(
            id_token,
            jwks,
            algorithms=["RS256"],
            audience=self.config.client_id,
        )


keycloak = KeycloakClient(settings.keycloak)
