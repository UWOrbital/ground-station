import os

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """
    Pydantic class for storing database configuration settings
    """

    user: str
    password: SecretStr
    location: str
    port: int
    name: str

    model_config = SettingsConfigDict(
        env_prefix="GS_DATABASE_",
        env_file=os.path.join(os.path.dirname(__file__), "../.env"),
        env_file_encoding="utf-8",
    )

    @property
    def connection_string(self) -> str:
        """
        Returns the database connection string
        """

        pwd = self.password.get_secret_value()
        return f"postgresql://{self.user}:{pwd}@{self.location}:{self.port}/{self.name}"
