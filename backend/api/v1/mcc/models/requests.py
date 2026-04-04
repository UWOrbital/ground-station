from typing import Annotated, Any
from uuid import UUID

from pydantic import BaseModel, Field


class DeleteCommandRequest(BaseModel):
    """
    Deletes a command from the commands table.
    """

    command_id: Annotated[UUID, Field(description="Command ID which is to be deleted")]


class CreateCommandRequest(BaseModel):
    """
    This creates a command and adds it to the database.
    """

    # TODO Refine this to figure out what the fk the actual params are
    payload: Annotated[dict[str, Any], Field(description="Params for to create a command")]
