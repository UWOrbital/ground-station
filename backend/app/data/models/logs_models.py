from datetime import UTC, datetime
from typing import Any, Final
from uuid import UUID, uuid4

from sqlalchemy import JSON, Column, DateTime
from sqlmodel import Field

from app.config.data_values import DEFAULT_MAX_LENGTH
from app.data.models.base_model import BaseSQLModel

# Schema information
LOGS_SCHEMA_NAME: Final[str] = "logs"

# Table names in database
API_LOG_TABLE_NAME: Final[str] = "api"


class APILog(BaseSQLModel, table=True):
    """
    A single application log record emitted through loguru and persisted to the database.

    Columns mirror the useful fields of a loguru record so downstream tooling
    (Grafana, a future in-house monitoring surface) can query the ground station's
    own logs instead of scraping a file.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)  # primary key is already uniquely indexed
    time: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        # Indexed because the monitoring surface queries logs newest-first (see APILogRepository.get_recent).
        sa_column=Column(DateTime(timezone=True), nullable=False, index=True),
    )
    priority: str = Field(max_length=DEFAULT_MAX_LENGTH)  # loguru level name, e.g. INFO/ERROR/CRITICAL
    message: str  # the rendered log message
    module: str | None = Field(default=None, max_length=DEFAULT_MAX_LENGTH)  # loguru record "name" (module)
    function: str | None = Field(default=None, max_length=DEFAULT_MAX_LENGTH)
    line: int | None = Field(default=None)
    extra: dict[str, Any] | None = Field(
        default=None, sa_column=Column(JSON, nullable=True)
    )  # loguru "extra" bag (request_id, user_id, ...)

    # table information
    __tablename__ = API_LOG_TABLE_NAME
    __table_args__ = {"schema": LOGS_SCHEMA_NAME}
