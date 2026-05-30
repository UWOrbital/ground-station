from typing import Annotated

from data.enums.transactional import CommandStatus
from pydantic import BaseModel, Field


class CreateCommandRequest(BaseModel):
    """Request model for creating a new command entry."""

    type_: Annotated[int, Field(description="MainCommand ID identifying the command type")]
    params: Annotated[
        str | None, Field(description="Serialized command parameters matching the main command schema")
    ] = None


class UpdateCommandRequest(BaseModel):
    """
    Request model for partially updating an existing command entry.

    All fields are optional; only provided fields are written to the database.
    """

    status: Annotated[CommandStatus | None, Field(description="New command lifecycle status")] = None
    type_: Annotated[int | None, Field(description="Replacement MainCommand ID")] = None
    params: Annotated[str | None, Field(description="Replacement serialized command parameters")] = None
