from pydantic_settings import BaseSettings, SettingsConfigDict


class AROAuthConfig(BaseSettings):
    """Configuration for ARO authentication credentials."""

    jwt_secret: str
    session_secret: str
    is_production: bool = True

    model_config = SettingsConfigDict(
        env_prefix="ARO_AUTH_",
        env_file=".env",
        extra="ignore",
    )
