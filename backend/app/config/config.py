# TODO:(335) Improve loading the configuration

from dotenv import load_dotenv

from app.config.aro_auth_config import AROAuthConfig
from app.config.cors_config import CORSConfig
from app.config.database_config import DatabaseConfig
from app.config.email_config import EmailConfig
from app.config.keycloak_config import KeycloakConfig
from app.config.logger_config import LoggerConfig

load_dotenv()


class BackendConfiguration:
    """
    Class for storing backend configuration settings
    """

    def __init__(self) -> None:
        self.cors = CORSConfig()
        self.logger = LoggerConfig()
        self.db = DatabaseConfig()
        self.keycloak = KeycloakConfig()
        self.auth = AROAuthConfig()
        self.email = EmailConfig()


settings = BackendConfiguration()
