from config.keycloak_config import KeycloakConfig


class KeycloakClient:
    """
    Encapsulating class for MCC authentication/authorization variables and
    functions.
    """

    def __init__(self, config: KeycloakConfig) -> None:
        self.config = config
