# TODO:(335) Improve loading the configuration
import contextlib
from os import environ
from typing import Final

from dotenv import load_dotenv

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


settings = BackendConfiguration()


def get_required_env(config: str) -> str:
    """
    Validates whether or not database env values exist in .env. If not, throws a value error.

    :param config: Variable in .env
    :type config: str
    :return: Value of variable in .env
    :rtype: str
    """
    value = environ.get(config)
    if not value:
        raise ValueError(f"{config} is missing from .env.")
    return value


contextlib.suppress(ValueError)
GOOGLE_CLIENT_ID = get_required_env("GOOGLE_CLIENT_ID")

GOOGLE_CLIENT_SECRET = get_required_env("GOOGLE_CLIENT_SECRET")
JWT_SECRET_KEY = get_required_env("JWT_SECRET_KEY")

GS_DATABASE_USER = get_required_env("GS_DATABASE_USER")
GS_DATABASE_PASSWORD = get_required_env("GS_DATABASE_PASSWORD")
GS_DATABASE_LOCATION = get_required_env("GS_DATABASE_LOCATION")
GS_DATABASE_PORT = get_required_env("GS_DATABASE_PORT")
GS_DATABASE_NAME = get_required_env("GS_DATABASE_NAME")

DATABASE_CONNECTION_STRING: Final[
    str
] = f"postgresql+psycopg2://{GS_DATABASE_USER}:{GS_DATABASE_PASSWORD}@{GS_DATABASE_LOCATION}:{GS_DATABASE_PORT}/{GS_DATABASE_NAME}"
