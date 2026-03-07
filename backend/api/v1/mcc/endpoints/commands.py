from typing import Any

from data.data_wrappers.wrappers import CommandsWrapper
from data.resources.cli_commands import CLICommand
from data.resources.commands_pipeline import CommandsPipeline
from fastapi import APIRouter

from api.v1.mcc.models.requests import CreateCommandRequest, DeleteCommandRequest, QueueCommandRequest
from api.v1.mcc.models.responses import CommandsResponse, MainCommandsResponse

commands_router = APIRouter(tags=["MCC", "Commands"])
COMMANDS_PIPELINE = CommandsPipeline()


@commands_router.post("/create")
async def create_command(request: CreateCommandRequest) -> CommandsResponse:
    """
    Create a new command. Note that this does store the command in queue

    :param payload: The data used to create a command
    :return: returns a list containing the one created command.
    """
    created_command = CommandsWrapper().create(request.payload)
    return CommandsResponse(data=[created_command])


@commands_router.delete("/delete")
async def delete_command(request: DeleteCommandRequest) -> dict[str, Any]:
    """
    Delete a command by ID.

    :param request: The request containing the ID which is to be deleted.
    :return: A message confirming that command with id of command_id has been deleted.
    """
    CommandsWrapper().delete_by_id(request.command_id)
    return {"message": f"Command with id {request.command_id} deleted successfully"}


@commands_router.get("/get_command_queue")
async def get_command_queue() -> CommandsResponse:
    """
    :return: A list containing all current commands in the commands pipeline queue as a list of MainCommand objects.
    """
    commands_queue = COMMANDS_PIPELINE.commands_queue
    commands = [cli_command.command for cli_command in commands_queue]

    return CommandsResponse(data=commands)


@commands_router.post("/queue_command")
async def queue_command(request: QueueCommandRequest) -> MainCommandsResponse:
    """
    Creates a cli command and adds it to command queue. Also creates a command
    and stores it into the commands table.
    :request: payload
    :request.params: params for CLI Command
    :request.cmd_id: command id
    :request.prio: command priority
    :response: A list containing MainCommand objects.
    """
    cli_command = CLICommand(params=request.params, cmd_id=request.cmd_id, prio=request.prio)
    command = CommandsWrapper().create(
        {"type_": request.cmd_id, "params": ",".join(map(str, cli_command.factory_args))}
    )
    cli_command.command = command
    COMMANDS_PIPELINE.add_to_queue(cli_command)

    return await get_command_queue()


@commands_router.post("/clear_command_queue")
async def clear_command_queue() -> dict[str, Any]:
    """
    Clears the current queue
    """
    # TODO this should also set all of the command status in the thing to sent
    COMMANDS_PIPELINE.clear_queue()
    return {"message": "Command queue cleared successfully"}


@commands_router.post("/enable_queue_lockout")
async def enable_lockout() -> dict[str, Any]:
    """
    Prevents all commands from being added into the command queue.

    :return: A message confirming that lockout has been enabled.
    """
    COMMANDS_PIPELINE.enable_lockout()
    return {
        "message": "Lockout enabled, command insertion into queue will no longer be possible until lockout is disabled"
    }


@commands_router.post("/disable_queue_lockout")
async def disable_lockout() -> dict[str, Any]:
    """
    Allows for more commands to be added to the command queue.

    :return: A message confirming that lockout has been disabled.
    """
    COMMANDS_PIPELINE.disable_lockout()
    return {"message": "Lockout disabled, command insertion into queue now possible"}
