from typing import Annotated

from data.tables.main_tables import MainCommand
from data.tables.transactional_tables import Commands
from pydantic import BaseModel, Field


class MainCommandsResponse(BaseModel):
    """Response model wrapping a list of MainCommand reference entries."""

    data: Annotated[list[MainCommand], Field(description="A list containing MainCommand objects")]


class CommandsResponse(BaseModel):
    """Response model wrapping a list of Commands."""

    data: Annotated[list[Commands], Field(description="A list containing Command objects")]


class CommandResponse(BaseModel):
    """Response model wrapping a single Command."""

    data: Annotated[Commands, Field(description="The created or retrieved Command object")]


class DeleteCommandResponse(BaseModel):
    """Response model confirming a command deletion."""

    message: Annotated[str, Field(description="Confirmation message including the deleted command ID")]
