# TODO:(335) Improve loading the configuration

from dotenv import load_dotenv

from config.aro_auth_config import AROAuthConfig
from config.cors_config import CORSConfig
from config.database_config import DatabaseConfig
from config.logger_config import LoggerConfig

load_dotenv()


class BackendConfiguration:
    """
    Class for storing backend configuration settings
    """

    def __init__(self) -> None:
        self.cors = CORSConfig()
        self.logger = LoggerConfig()
        self.db = DatabaseConfig()
        self.auth = AROAuthConfig()


settings = BackendConfiguration()
