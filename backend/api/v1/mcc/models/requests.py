from uuid import UUID
from typing import Annotated, Any
from pydantic import BaseModel, Field

class QueueCommandRequest(BaseModel):
    """
    The request params to queue a command into the commands queue.
    """
    params: Annotated[dict[str, int | bool], Field(description="Params for commands.")]
    cmd_id: Annotated[int, Field(description="Command ID, references obc_gs_command_id.h")]
    prio: Annotated[int, Field(description="The priority of the command")]

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