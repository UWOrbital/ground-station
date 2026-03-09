from urllib.parse import urlencode

from config.config import settings
from config.keycloak_config import KeycloakConfig


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
        return f"{self.config.url}/realms/{self.config.realm}/protocol/openid-connect/auth?{self._params}"


keycloak = KeycloakClient(settings.keycloak)
