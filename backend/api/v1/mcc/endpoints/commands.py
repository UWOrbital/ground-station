from typing import Annotated
from uuid import UUID

from data.data_wrappers.wrappers import CommandsWrapper
from data.tables.mcc_user_tables import MCCUsers
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from mcc_keycloak.client import keycloak

from api.v1.mcc.models.requests import CreateCommandRequest, UpdateCommandRequest
from api.v1.mcc.models.responses import CommandResponse, CommandsResponse, DeleteCommandResponse

commands_router = APIRouter(tags=["MCC", "Commands"])


@commands_router.get("/", dependencies=[keycloak.require_auth])
async def get_commands() -> CommandsResponse:
    """
    Retrieve all commands from the database.

    :return: All command entries.
    """
    return CommandsResponse(data=CommandsWrapper().get_all())


@commands_router.post("/")
async def create_command(
    request: CreateCommandRequest,
    current_user: Annotated[MCCUsers, Depends(keycloak.get_current_user)],
) -> CommandResponse:
    """
    Create a new command entry with status set to pending.

    :param request: Typed fields identifying the command type and optional parameters.
    :param current_user: Authenticated MCC user; their ID is recorded on the command.
    :return: The newly created command.
    """
    created_command = CommandsWrapper().create(
        {"type_": request.type_, "params": request.params, "user_id": current_user.id}
    )
    return CommandResponse(data=created_command)


@commands_router.get("/{command_id}", dependencies=[keycloak.require_auth])
async def get_command(command_id: UUID) -> CommandResponse:
    """
    Retrieve a single command by ID.

    :param command_id: UUID of the command to retrieve.
    :return: The matching command entry.
    """
    try:
        command = CommandsWrapper().get_by_id(command_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return CommandResponse(data=command)


@commands_router.patch("/{command_id}", dependencies=[keycloak.require_auth])
async def update_command(command_id: UUID, request: UpdateCommandRequest) -> CommandResponse:
    """
    Partially update a command's status, type, or parameters.

    :param command_id: UUID of the command to update.
    :param request: Fields to overwrite; omitted fields are left unchanged.
    :return: The updated command entry.
    """
    updates = request.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=422, detail="At least one field must be provided to update")
    try:
        updated_command = CommandsWrapper().update(command_id, updates)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return CommandResponse(data=updated_command)


@commands_router.delete("/{command_id}", dependencies=[keycloak.require_auth])
async def delete_command(command_id: UUID) -> DeleteCommandResponse:
    """
    Delete a command by ID.

    :param command_id: UUID of the command to delete.
    :return: Confirmation message with the deleted command ID.
    """
    try:
        CommandsWrapper().delete_by_id(command_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    return DeleteCommandResponse(message=f"Command {command_id} deleted successfully")
