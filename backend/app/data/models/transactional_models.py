from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, Final
from uuid import UUID, uuid4

from sqlalchemy import Column, DateTime, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as DB_UUID
from sqlalchemy.schema import CheckConstraint, ForeignKey, ForeignKeyConstraint, Index, UniqueConstraint
from sqlmodel import Field

from app.config.data_values import (
    COORDINATE_DECIMAL_NUMBER,
    LATITUDE_MAX_DIGIT_NUMBER,
    LONGITUDE_MAX_DIGIT_NUMBER,
    PACKET_DATA_LENGTH,
    PACKET_RAW_LENGTH,
)
from app.data.database.utils import to_foreign_key_value
from app.data.enums.aro_requests import ARORequestStatus
from app.data.enums.transactional import (
    CommandStatus,
    MainPacketType,
    OrbitElementSource,
    SessionSource,
    SessionStatus,
)
from app.data.models.aro_user_models import AROUsers
from app.data.models.base_model import BaseSQLModel
from app.data.models.main_models import (
    MainCommand,
    MainTableID,
    MainTableIDDatabase,
    MainTelemetry,
)
from app.data.models.mcc_user_models import MCCUsers

# Transactional schema related items
TRANSACTIONAL_SCHEMA_NAME: Final[str] = "transactional"

# Table names in database
ARO_REQUESTS_TABLE_NAME: Final[str] = "aro_requests"
SESSIONS_TABLE_NAME: Final[str] = "sessions"
ORBIT_ELEMENTS_TABLE_NAME: Final[str] = "orbit_elements"
ORBIT_FETCH_ATTEMPTS_TABLE_NAME: Final[str] = "orbit_fetch_attempts"
PACKETS_TABLE_NAME: Final[str] = "packets"
TELEMETRY_TABLE_NAME: Final[str] = "telemetry"
COMMANDS_TABLE_NAME: Final[str] = "commands"
IMAGES_TABLE_NAME: Final[str] = "images"

# Transactional data tables


class ARORequest(BaseSQLModel, table=True):
    """
    Holds the data related to an ARO picture request
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    aro_id: UUID = Column(DB_UUID, ForeignKey(AROUsers.id))  # type: ignore
    latitude: Decimal = Field(max_digits=LATITUDE_MAX_DIGIT_NUMBER, decimal_places=COORDINATE_DECIMAL_NUMBER)
    longitude: Decimal = Field(max_digits=LONGITUDE_MAX_DIGIT_NUMBER, decimal_places=COORDINATE_DECIMAL_NUMBER)
    created_on: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    request_sent_to_obc_on: datetime | None = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    pic_taken_on: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    pic_transmitted_on: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    delete_deadline: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    packet_id: UUID | None = Field(
        default=None,
        foreign_key=to_foreign_key_value(TRANSACTIONAL_SCHEMA_NAME, PACKETS_TABLE_NAME),
        ondelete="CASCADE",
    )
    status: ARORequestStatus = Field(default=ARORequestStatus.PENDING)

    # table information
    __tablename__ = ARO_REQUESTS_TABLE_NAME
    __table_args__ = (
        ForeignKeyConstraint(
            ["aro_id"],
            [AROUsers.id],  # type: ignore
            onupdate="CASCADE",
            ondelete="SET NULL",  # We want to maintain the request
        ),
        {"schema": TRANSACTIONAL_SCHEMA_NAME},
    )  # Since the table is in a different schema sqlmodel can't find the table normally


class Command(BaseSQLModel, table=True):
    """
    An instance of a MainCommand.
    This table holds the data related to actual commands sent from the ground station up to the OBC.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID | None = Field(default=None, sa_column=Column("user_id", DB_UUID, nullable=True))
    session_id: UUID = Field(
        foreign_key=to_foreign_key_value(TRANSACTIONAL_SCHEMA_NAME, SESSIONS_TABLE_NAME),
        ondelete="CASCADE",
    )
    status: CommandStatus = Field(default=CommandStatus.PENDING)
    type_: MainTableID = Column(MainTableIDDatabase, ForeignKey(MainCommand.id))  # type: ignore
    params: str | None = None  # TODO: Make sure this matches the corresponding params in the main command table
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )
    packet_id: UUID | None = Field(
        default=None,
        foreign_key=to_foreign_key_value(TRANSACTIONAL_SCHEMA_NAME, PACKETS_TABLE_NAME),
        ondelete="SET NULL",
    )
    sequence_index: int | None = Field(default=None)  # Position of this command within its packet
    response: str | None = Field(default=None)  # Reply from the OBC, populated on downlink

    # table information
    __tablename__ = COMMANDS_TABLE_NAME
    __table_args__ = (
        ForeignKeyConstraint(
            ["type_"],
            [MainCommand.id],  # type: ignore
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["user_id"],
            [MCCUsers.id],  # type: ignore
            onupdate="CASCADE",
            ondelete="SET NULL",
        ),
        {"schema": TRANSACTIONAL_SCHEMA_NAME},
    )  # Since the table is in a different schema sqlmodel can't find the table normally


class Telemetry(BaseSQLModel, table=True):
    """
    An instance of a MainTelemetry.
    This table holds the data related to actual telemetry received from the OBC.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    type_: MainTableID = Column(MainTableIDDatabase, ForeignKey(MainTelemetry.id))  # type: ignore
    value: str | None = None  # TODO: Make sure this matches the corresponding params in the main command table
    packet_id: UUID | None = Field(
        default=None,
        foreign_key=to_foreign_key_value(TRANSACTIONAL_SCHEMA_NAME, PACKETS_TABLE_NAME),
        ondelete="SET NULL",
    )
    sequence_index: int | None = Field(default=None)  # Position of this telemetry within its packet
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        ),
    )

    # table information
    __tablename__ = TELEMETRY_TABLE_NAME
    __table_args__ = (
        ForeignKeyConstraint(
            ["type_"],
            [MainTelemetry.id],  # type: ignore
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
        {"schema": TRANSACTIONAL_SCHEMA_NAME},
    )  # Since the table is in a different schema sqlmodel can't find the table normally


class Session(BaseSQLModel, table=True):
    """
    Holds information regarding an uplink/downlink transmit cycle
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    # Padded start: rise_time minus padding for predicted sessions
    start_time: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    # Padded end: set_time plus padding for predicted sessions
    end_time: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False, index=True))
    status: SessionStatus = Field(default=SessionStatus.PENDING)
    source: SessionSource = Field(default=SessionSource.MANUAL)

    # Pass data from the pass predictor (null for manual sessions)
    rise_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    peak_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    set_time: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    min_elevation_deg: float | None = Field(default=None)
    max_elevation_deg: float | None = Field(default=None)
    rise_azimuth_deg: float | None = Field(default=None)
    set_azimuth_deg: float | None = Field(default=None)
    orbit_element_id: UUID | None = Field(
        default=None,
        foreign_key=to_foreign_key_value(TRANSACTIONAL_SCHEMA_NAME, ORBIT_ELEMENTS_TABLE_NAME),
        ondelete="RESTRICT",
    )
    # Set when a predicted pass disappeared and the session already had commands,
    # or it moved beyond the padding after the schedule freeze
    orphaned_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    __tablename__ = SESSIONS_TABLE_NAME
    __table_args__ = (
        CheckConstraint("start_time < end_time", name="ck_sessions_start_before_end"),
        CheckConstraint(
            "source <> 'PREDICTED' OR (rise_time IS NOT NULL AND peak_time IS NOT NULL AND set_time IS NOT NULL"
            " AND min_elevation_deg IS NOT NULL AND max_elevation_deg IS NOT NULL AND rise_azimuth_deg IS NOT NULL"
            " AND set_azimuth_deg IS NOT NULL AND orbit_element_id IS NOT NULL)",
            name="ck_sessions_predicted_fields",
        ),
        CheckConstraint("rise_time < peak_time AND peak_time < set_time", name="ck_sessions_pass_order"),
        CheckConstraint("start_time <= rise_time AND set_time <= end_time", name="ck_sessions_padding_outside_pass"),
        CheckConstraint("min_elevation_deg >= 0 AND min_elevation_deg <= 90", name="ck_sessions_min_elevation_range"),
        CheckConstraint("max_elevation_deg >= 0 AND max_elevation_deg <= 90", name="ck_sessions_max_elevation_range"),
        CheckConstraint("max_elevation_deg > min_elevation_deg", name="ck_sessions_peak_above_cutoff"),
        CheckConstraint(
            "rise_azimuth_deg >= 0 AND rise_azimuth_deg < 360 AND set_azimuth_deg >= 0 AND set_azimuth_deg < 360",
            name="ck_sessions_azimuth_range",
        ),
        {"schema": TRANSACTIONAL_SCHEMA_NAME},
    )


class OrbitElement(BaseSQLModel, table=True):
    """
    Holds one set of orbit elements (CCSDS OMM record) for a satellite
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    norad_cat_id: int
    epoch: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    omm: dict[str, Any] = Field(sa_column=Column(JSONB, nullable=False))  # Raw CelesTrak JSON OMM record
    source: OrbitElementSource = Field(default=OrbitElementSource.CELESTRAK)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )

    __tablename__ = ORBIT_ELEMENTS_TABLE_NAME
    __table_args__ = (
        UniqueConstraint("norad_cat_id", "epoch", name="uq_orbit_elements_norad_cat_id_epoch"),
        {"schema": TRANSACTIONAL_SCHEMA_NAME},
    )


class OrbitFetchAttempt(BaseSQLModel, table=True):
    """
    Records each attempt to download orbit elements (successful or not).

    Used to rate-limit requests to CelesTrak and check when orbit data has stopped arriving.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    norad_cat_id: int
    attempted_at: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    http_status: int | None = Field(default=None)  # None when no response received
    error: str | None = Field(default=None)  # None when the attempt succeeded
    inserted: bool = Field(default=False)  # Whether a new orbit element was stored

    __tablename__ = ORBIT_FETCH_ATTEMPTS_TABLE_NAME
    __table_args__ = (
        Index("ix_orbit_fetch_attempts_norad_cat_id_attempted_at", "norad_cat_id", "attempted_at"),
        {"schema": TRANSACTIONAL_SCHEMA_NAME},
    )


class Packet(BaseSQLModel, table=True):
    """
    Holds the information about a raw packet
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    session_id: UUID = Field(
        foreign_key=to_foreign_key_value(TRANSACTIONAL_SCHEMA_NAME, SESSIONS_TABLE_NAME), ondelete="CASCADE"
    )
    raw_data: bytes = Field(max_length=PACKET_RAW_LENGTH)
    type_: MainPacketType
    subtype: str | None = Field(default=None)  # CSDC requirement. TODO: Promote to an enum once subtypes are defined
    payload_data: bytes = Field(max_length=PACKET_DATA_LENGTH)
    created_on: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    offset: int

    # table information
    __tablename__ = PACKETS_TABLE_NAME
    __table_args__ = {"schema": TRANSACTIONAL_SCHEMA_NAME}


class Image(BaseSQLModel, table=True):
    """
    Holds the information about an image downlinked from the OBC
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    data: str
    packet_id: UUID | None = Field(
        default=None,
        foreign_key=to_foreign_key_value(TRANSACTIONAL_SCHEMA_NAME, PACKETS_TABLE_NAME),
        ondelete="SET NULL",
    )
    aro_id: UUID | None = Field(
        default=None,
        foreign_key=to_foreign_key_value(TRANSACTIONAL_SCHEMA_NAME, ARO_REQUESTS_TABLE_NAME),
        ondelete="SET NULL",
    )

    __tablename__ = IMAGES_TABLE_NAME
    __table_args__ = {"schema": TRANSACTIONAL_SCHEMA_NAME}
