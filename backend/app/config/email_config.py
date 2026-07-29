from pydantic_settings import BaseSettings, SettingsConfigDict


class EmailConfig(BaseSettings):
    """
    Pydantic class for storing email configuration settings
    """

    mail_username: str
    mail_password: str
    mail_server: str
    mail_from: str
    mail_from_name: str
    mail_port: int

    model_config = SettingsConfigDict(
        env_prefix="EMAIL_",
        env_file_encoding="utf-8",
    )
