from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from app.api.v1.mcc.schemas.responses import MainCommandResponse, MainCommandsResponse
from app.data.data_wrappers.wrappers import MainCommandWrapper
from app.mcc_keycloak.client import keycloak

main_commands_router = APIRouter(tags=["MCC", "Main Commands"])


@main_commands_router.get("/", dependencies=[keycloak.require_auth])
async def get_all_commands() -> MainCommandsResponse:
    """
    Gets the main commands that are available for the MCC

    :return: the list of all commands.
    """
    items = await MainCommandWrapper().get_all()
    return MainCommandsResponse(data=items)


@main_commands_router.get("/{command_id}", dependencies=[keycloak.require_auth])
async def get_command_by_id(command_id: int) -> MainCommandResponse:
    """
    Gets the main command by the id provided

    :param command_id: the ID of the command to retrieve.
    :return: the matching command.
    """
    try:
        command = await MainCommandWrapper().get_by_id(command_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Command not found") from e
    return MainCommandResponse(data=command)
