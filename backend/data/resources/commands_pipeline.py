import contextlib
import warnings

from data.data_wrappers.wrappers import CommandsWrapper, MainCommandWrapper
from data.enums.transactional import CommandStatus
from data.resources.cli_commands import CLICommand
from data.tables.transactional_tables import Commands
from interfaces import PADDING_REQUIRED
from interfaces.obc_gs_interface.commands.python import CmdMsg
from interfaces.obc_gs_interface.commands.python.command_framing import command_multi_pack
from obc_utils.command_packaging import CommandPackaging


class CommandsPipeline:
    """
    Recieves, sorts, and packets commands such that they may be sent to the
    satellite.

    This is basically another abstraction layer for the database.
    """

    def __init__(self) -> None:
        """
        Lockout should be set at some arbitrary time before session begins.
        Once lockout is True, commands will no longer be recieved
        """
        self.lockout: bool = False
        self.commands_queue: list[CLICommand] = []
        self.packet_list: list[bytes] = []

    def queue_to_packet(self) -> list[bytes]:
        """
        Converts all commands in the queue into packets.
        """

        if len(self.commands_queue) == 0:
            warnings.warn("No commands in queue. Packeting will succeed but have no effect.", stacklevel=1)
            return [b"\x00"]

        command_messages: list[CmdMsg] = []
        command_bytes: list[bytes] = []
        comms = CommandPackaging()

        for command in self.commands_queue:
            command_messages.append(command.cmd_msg)

        command_bytes = command_multi_pack(command_messages)

        for byte_string in command_bytes:
            self.packet_list.append(comms.encode_frame(byte_string).ljust(PADDING_REQUIRED, b"\x00"))

        for cli_command in self.commands_queue:
            if cli_command.command is not None:
                update_req = {"status": CommandStatus.PACKETED}
                CommandsWrapper().update(cli_command.command.id, update_req)

        return self.packet_list

    def build_queue(self) -> list[Commands]:
        """
        Builds the queue from the database based on status.
        """

        commands = CommandsWrapper().get_all_by(status=CommandStatus.PENDING)

        for command in commands:
            param_list = command.params.split(",") if command.params else []
            processed_param: dict[str, str | int | bool | float] = {}

            for i in range(0, len(param_list) - 1, 2):
                val_str = param_list[i + 1]
                val: str | int | bool | float = val_str

                if val_str.lower() in ["true", "false"]:
                    val = val_str.lower() == "true"
                else:
                    with contextlib.suppress(ValueError):
                        val = int(val_str)

                    if isinstance(val, str):
                        with contextlib.suppress(ValueError):
                            val = float(val_str)

                processed_param[param_list[i]] = val

            main_cmd = MainCommandWrapper().get_by_id(command.type_)
            priority = main_cmd.priority if main_cmd else 0

            cli_command = CLICommand(params=processed_param, cmd_id=command.type_, prio=priority)
            cli_command.command = command
            cli_command.time = command.created_at
            self.commands_queue.append(cli_command)

            update_req = {"status": CommandStatus.SCHEDULED}
            CommandsWrapper().update(cli_command.command.id, update_req)

        self.sort_queue()
        return commands

    def sort_queue(self) -> list[CLICommand]:
        """
        This function sorts the queue 2 times. We first sort by time to ensure time descending,
        then we sort by priority to ensure that the highest priority is at the top of the
        queue.
        """
        self.commands_queue.sort(key=lambda x: x.time)
        self.commands_queue.sort(key=lambda x: x.prio)
        return self.commands_queue

    def clear_queue(self) -> None:
        """
        Sets all command status to completed and clears queue (please note that we should have a seperate
        enum for aborted)
        """
        for cli_command in self.commands_queue:
            if cli_command.command is not None:
                update_req = {"status": CommandStatus.COMPLETED}
                CommandsWrapper().update(cli_command.command.id, update_req)

        self.commands_queue = []

    def clear_packets(self) -> None:
        """
        Clears the packet list so that a new set of commands can be queued.
        """
        self.packet_list = []
