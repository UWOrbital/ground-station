from collections.abc import Sequence

from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggerConfig(BaseSettings):
    """
    Pydantic class for storing logger middleware configuration settings
    """

    model_config = SettingsConfigDict(env_prefix="LOGGER_")

    excluded_endpoints: Sequence[str] = []

    # Database log sink (see app/config/db_log_sink.py). Logs are persisted to logs.api
    # in addition to the console sink so a DB outage never loses log output.
    db_sink_enabled: bool = True
    db_sink_min_level: str = "INFO"  # must stay above VERBOSE (15) to avoid recursion via SQLAlchemy logs
    db_sink_batch_size: int = 50  # max rows written per INSERT batch
    db_sink_queue_maxsize: int = 10000  # bound the in-memory buffer; excess logs are dropped, not blocked
