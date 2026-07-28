from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field

from data.enums.transactional import CommandStatus
from data.models.main_models import MainCommand, MainTelemetry
from data.models.transactional_models import CommsSession


class CommandItem(BaseModel):
    """Pydantic response model for a serialized Command (non-table)."""

    model_config = {"from_attributes": True}

    id: UUID
    user_id: UUID | None = None
    session_id: UUID
    status: CommandStatus
    type_: int
    params: str | None = None
    created_at: datetime
    packet_id: UUID | None = None
    sequence_index: int | None = None
    response: str | None = None


class MainCommandsResponse(BaseModel):
    """Response model wrapping a list of MainCommand reference entries."""

    data: Annotated[list[MainCommand], Field(description="A list containing MainCommand objects")]


class MainCommandResponse(BaseModel):
    """Response model wrapping a single MainCommand."""

    data: Annotated[MainCommand, Field(description="The retrieved MainCommand object")]


class CommandsResponse(BaseModel):
    """Response model wrapping a list of Commands."""

    data: Annotated[list[CommandItem], Field(description="A list containing Command objects")]


class CommandResponse(BaseModel):
    """Response model wrapping a single Command."""

    data: Annotated[CommandItem, Field(description="The created or retrieved Command object")]


class DeleteCommandResponse(BaseModel):
    """Response model confirming a command deletion."""

    message: Annotated[str, Field(description="Confirmation message including the deleted command ID")]


class CommsSessionsResponse(BaseModel):
    """Response model wrapping a list of CommsSessions."""

    data: Annotated[list[CommsSession], Field(description="A list containing CommsSession objects")]


class MainTelemetriesResponse(BaseModel):
    """Response model for wrapping a list of main telemetries"""

    data: Annotated[list[MainTelemetry], Field(description="A list containing MainTelemetry objects")]


class MainTelemetryResponse(BaseModel):
    """Response model for wrapping a single MainTelemetry"""

    data: Annotated[MainTelemetry, Field(description="The retrieved MainTelemetry object")]


class TelemetryDataResponse(BaseModel):
    """

    The Telemetry Data Response
    """

    label: str
    value: str
    unit: str | None = None


class SatelliteStatusResponse(BaseModel):
    """

    The Satellite Status Response model
    """

    status: str
    last_contact: str
    session_duration: str
    telemetry_data: list[TelemetryDataResponse]


class UserInformationResponse(BaseModel):
    """

    The User Personal Account Details Response model
    """

    id: UUID
    email: str
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None


class TelemetrySubrow(BaseModel):
    """

    The Telemetry Subrow Response model
    """

    packet: str
    session: str
    obc_state: str


class TelemetryEntry(BaseModel):
    """

    The Telemetry Entry Response model
    """

    id: UUID
    type: str
    value: str | None
    timestamp: datetime
    subrows: list[TelemetrySubrow] | None


class TelemetryListResponse(BaseModel):
    """

    The Telemetry List Response model
    """

    data: Annotated[list[TelemetryEntry], Field(description="A list containing Telemetry objects")]
