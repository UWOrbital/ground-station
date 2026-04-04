from typing import Any

from data.data_wrappers.wrappers import CommandsWrapper
from fastapi import APIRouter

from api.v1.mcc.models.requests import CreateCommandRequest, DeleteCommandRequest
from api.v1.mcc.models.responses import CommandsResponse

commands_router = APIRouter(tags=["MCC", "Commands"])


@commands_router.post("/create")
async def create_command(request: CreateCommandRequest) -> CommandsResponse:
    """
    Adds a command to the database. Status set to pending.

    :param payload: The data used to create a command
    :return: returns a list containing the one created command.
    """
    created_command = CommandsWrapper().create(request.payload)
    return CommandsResponse(data=[created_command])


# Should we even have a delete method? IMO we should only be able to set command status to "CANCELLED" or something
# since deleting commands means we lose potential debug data.
@commands_router.delete("/delete")
async def delete_command(request: DeleteCommandRequest) -> dict[str, Any]:
    """
    Delete a command by ID.

    :param request: The request containing the ID which is to be deleted.
    :return: A message confirming that command with id of command_id has been deleted.
    """
    CommandsWrapper().delete_by_id(request.command_id)
    return {"message": f"Command with id {request.command_id} deleted successfully"}
