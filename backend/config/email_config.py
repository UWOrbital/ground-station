from pydantic_settings import BaseSettings, SettingsConfigDict


class EmailConfig(BaseSettings):
    """Configuration for sending emails via SMTP."""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    sender_email: str = ""

    model_config = SettingsConfigDict(env_prefix="EMAIL_")
