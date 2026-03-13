from pydantic_settings import BaseSettings, SettingsConfigDict

class AROAuthConfig(BaseSettings):
    google_client_id: str
    google_client_secret: str
    jwt_secret_key: str

    model_config = SettingsConfigDict(
        env_prefix="",  # no prefix, maps directly
    )