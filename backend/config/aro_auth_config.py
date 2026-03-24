from pydantic_settings import BaseSettings, SettingsConfigDict


class AROAuthConfig(BaseSettings):
    """Configuration for ARO authentication credentials."""

    google_client_id: str
    google_client_secret: str
    jwt_secret_key: str

    model_config = SettingsConfigDict(
        env_prefix="ARO_AUTH_",
        env_file=".env",
        extra="ignore",
    )
