from datetime import datetime
from decimal import Decimal
from typing import Final
from uuid import UUID, uuid4

from config.data_config import (
    COORDINATE_DECIMAL_NUMBER,
    LATITUDE_MAX_DIGIT_NUMBER,
    LONGITUDE_MAX_DIGIT_NUMBER,
    PACKET_DATA_LENGTH,
    PACKET_RAW_LENGTH,
)
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import UUID as DB_UUID
from sqlalchemy.schema import Column, ForeignKey, ForeignKeyConstraint
from sqlmodel import Field

from data.database.utils import to_foreign_key_value
from data.enums.aro_requests import ARORequestStatus
from data.enums.transactional import (
    CommandStatus,
    MainPacketType,
    SessionStatus,
)
from data.tables.aro_user_tables import AROUsers
from data.tables.base_model import BaseSQLModel
from data.tables.main_tables import (
    MainCommand,
    MainTableID,
    MainTableIDDatabase,
    MainTelemetry,
)
from data.tables.mcc_user_tables import MCCUsers

# Transactional schema related items
TRANSACTIONAL_SCHEMA_NAME: Final[str] = "transactional"

# Table names in database
ARO_REQUEST_TABLE_NAME: Final[str] = "aro_requests"
SESSIONS_TABLE_NAME: Final[str] = "sessions"
PACKET_TABLE_NAME: Final[str] = "packets"
TELEMETRY_TABLE_NAME: Final[str] = "telemetry"
COMMANDS_TABLE_NAME: Final[str] = "commands"

# Transactional data tables


class ARORequest(BaseSQLModel, table=True):
    """
    Holds the data related to an ARO picture request
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    aro_id: UUID = Column(DB_UUID, ForeignKey(AROUsers.id))  # type: ignore
    latitude: Decimal = Field(max_digits=LATITUDE_MAX_DIGIT_NUMBER, decimal_places=COORDINATE_DECIMAL_NUMBER)
    longitude: Decimal = Field(max_digits=LONGITUDE_MAX_DIGIT_NUMBER, decimal_places=COORDINATE_DECIMAL_NUMBER)
    created_on: datetime = Field(default_factory=datetime.now)
    request_sent_to_obc_on: datetime | None = Field(default=None)
    pic_taken_on: datetime | None = Field(default=None)
    pic_transmitted_on: datetime | None = Field(default=None)
    packet_id: UUID | None = Field(
        default=None,
        foreign_key=to_foreign_key_value(TRANSACTIONAL_SCHEMA_NAME, PACKET_TABLE_NAME),
        ondelete="CASCADE",
    )
    status: ARORequestStatus = Field(default=ARORequestStatus.PENDING)

    # table information
    __tablename__ = ARO_REQUEST_TABLE_NAME
    __table_args__ = (
        ForeignKeyConstraint(
            ["aro_id"],
            [AROUsers.id],  # type: ignore
            onupdate="CASCADE",
            ondelete="SET NULL",  # We want to maintain the request
        ),
        {"schema": TRANSACTIONAL_SCHEMA_NAME},
    )  # Since the table is in a different schema sqlmodel can't find the table normally


class Commands(BaseSQLModel, table=True):
    """
    An instance of a MainCommand.
    This table holds the data related to actual commands sent from the ground station up to the OBC.
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID | None = Field(default=None, sa_column=Column("user_id", DB_UUID, nullable=True))
    status: CommandStatus = Field(default=CommandStatus.PENDING)
    type_: MainTableID = Column(MainTableIDDatabase, ForeignKey(MainCommand.id))  # type: ignore
    params: str | None = None  # TODO: Make sure this matches the corresponding params in the main command table
    created_at: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"server_default": func.now()})
    packet_id: UUID | None = Field(
        default=None,
        foreign_key=to_foreign_key_value(TRANSACTIONAL_SCHEMA_NAME, PACKET_TABLE_NAME),
        ondelete="SET NULL",
    )
    sequence_index: int | None = Field(default=None)  # Position of this command within its packet

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
        foreign_key=to_foreign_key_value(TRANSACTIONAL_SCHEMA_NAME, PACKET_TABLE_NAME),
        ondelete="SET NULL",
    )
    sequence_index: int | None = Field(default=None)  # Position of this telemetry within its packet
    timestamp: datetime = Field(default_factory=datetime.now, sa_column_kwargs={"server_default": func.now()})

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


# Communcation session information


class CommsSession(BaseSQLModel, table=True):
    """
    Holds basic information related to a downlink/uplink transmit cycle
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    start_time: datetime = Field(unique=True)
    end_time: datetime | None = Field(unique=True, default=None)
    status: SessionStatus = Field(default=SessionStatus.PENDING)

    # table information
    __tablename__ = SESSIONS_TABLE_NAME
    __table_args__ = {"schema": TRANSACTIONAL_SCHEMA_NAME}


# Raw packet data


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
    created_on: datetime = Field(default_factory=datetime.now)
    offset: int

    # table information
    __tablename__ = PACKET_TABLE_NAME
    __table_args__ = {"schema": TRANSACTIONAL_SCHEMA_NAME}
