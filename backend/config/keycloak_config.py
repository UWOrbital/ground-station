from pydantic_settings import BaseSettings, SettingsConfigDict


class KeycloakConfig(BaseSettings):
    """
    Pydantic class for storing keycloak configuration settings
    """

    admin_username: str = "admin"
    admin_password: str = "admin"
    realm: str = "mcc"
    host: str = "http://keycloak:8080"
    external_url: str = "http://localhost:8080"
    client_id: str = "ground-station"
    client_secret: str
    callback_url: str = "http://localhost:8000/api/v1/mcc/auth/callback"
    redirect_uri: str = "http://localhost:8000/docs"
    secure_cookies: bool = False

    model_config = SettingsConfigDict(
        env_prefix="KEYCLOAK_",
        env_file_encoding="utf-8",
        extra="ignore",
    )
