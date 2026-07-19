from typing import Annotated
from uuid import UUID

from api.v1.mcc.schemas.requests import CreateCommandRequest, UpdateCommandRequest
from api.v1.mcc.schemas.responses import CommandResponse, CommandsResponse, DeleteCommandResponse
from api.v1.mcc.services.scheduling import assert_not_locked_out
from data.data_wrappers.wrappers import CommandsWrapper, CommsSessionWrapper
from data.models.mcc_user_models import MCCUsers
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from mcc_keycloak.client import keycloak

commands_router = APIRouter(tags=["MCC", "Commands"])


@commands_router.get("/", dependencies=[keycloak.require_auth])
async def get_commands() -> CommandsResponse:
    """
    Retrieve all commands from the database.

    :return: All command entries.
    """
    return CommandsResponse(data=CommandsWrapper().get_all())


@commands_router.get("/session/{session_id}", dependencies=[keycloak.require_auth])
async def get_commands_by_session(session_id: UUID) -> CommandsResponse:
    """
    Retrieve all commands associated with a given session.

    :param session_id: UUID of the target session.
    :return: All commands tied to that session.
    """
    return CommandsResponse(data=CommandsWrapper().get_by_session(session_id))


@commands_router.post("/", dependencies=[keycloak.require_auth])
async def create_command(
    request: CreateCommandRequest,
    current_user: Annotated[MCCUsers, Depends(keycloak.get_current_user)],
) -> CommandResponse:
    """
    Create a new command entry with status set to pending.

    :param request: Typed fields identifying the command type, session, and optional parameters.
    :param current_user: Authenticated MCC user; their ID is recorded on the command.
    :return: The newly created command.
    """
    try:
        session = CommsSessionWrapper().get_by_id(request.session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e

    try:
        assert_not_locked_out(session)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e

    created_command = CommandsWrapper().create(
        {
            "type_": request.type_,
            "params": request.params,
            "user_id": current_user.id,
            "session_id": request.session_id,
            "sequence_index": request.sequence_index,
        }
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
        existing_command = CommandsWrapper().get_by_id(command_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    try:
        session = CommsSessionWrapper().get_by_id(existing_command.session_id)
        assert_not_locked_out(session)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    updated_command = CommandsWrapper().update(command_id, updates)
    return CommandResponse(data=updated_command)


@commands_router.delete("/{command_id}", dependencies=[keycloak.require_auth])
async def delete_command(command_id: UUID) -> DeleteCommandResponse:
    """
    Delete a command by ID.

    :param command_id: UUID of the command to delete.
    :return: Confirmation message with the deleted command ID.
    """
    try:
        existing_command = CommandsWrapper().get_by_id(command_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    try:
        session = CommsSessionWrapper().get_by_id(existing_command.session_id)
        assert_not_locked_out(session)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e)) from e
    CommandsWrapper().delete_by_id(command_id)
    return DeleteCommandResponse(message=f"Command {command_id} deleted successfully")
