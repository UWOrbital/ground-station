from pydantic_settings import BaseSettings, SettingsConfigDict


class KeycloakConfig(BaseSettings):
    """
    Pydantic class for storing keycloak configuration settings
    """

    url: str
    realm: str
    client_id: str
    client_secret: str
    callback_url: str

    model_config = SettingsConfigDict(
        env_prefix="KEYCLOAK_",
        # env_file=os.path.join(os.path.dirname(__file__), "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )
