from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.data.enums.mcc_users import MCCAdminRequestStatus
from app.data.enums.transactional import CommandStatus


class CreateCommandRequest(BaseModel):
    """Request model for creating a new command entry."""

    type_: Annotated[int, Field(description="MainCommand ID identifying the command type")]
    params: Annotated[
        str | None, Field(description="Serialized command parameters matching the main command schema")
    ] = None
    session_id: Annotated[UUID, Field(description="Session this command is scheduled for")]
    sequence_index: Annotated[int | None, Field(description="Rudimentary send-order hint before packetization")] = None


class UpdateCommandRequest(BaseModel):
    """
    Request model for partially updating an existing command entry.

    All fields are optional; only provided fields are written to the database.
    """

    status: Annotated[CommandStatus | None, Field(description="New command lifecycle status")] = None
    type_: Annotated[int | None, Field(description="Replacement MainCommand ID")] = None
    params: Annotated[str | None, Field(description="Replacement serialized command parameters")] = None


class UpdateUserRequest(BaseModel):
    """
    Request model for partially updating an existing user
    """

    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    phone_number: str | None = None


class UpdateAdminRequestStatusRequest(BaseModel):
    """
    Request model for an admin approving or rejecting a pending MCC admin access request
    """

    status: Annotated[
        Literal[MCCAdminRequestStatus.APPROVED, MCCAdminRequestStatus.REJECTED],
        Field(description="The decision to record for the pending request"),
    ]
