from datetime import datetime

from data.tables.transactional_tables import Commands
from interfaces.obc_gs_interface.commands.python import CmdCallbackId
from interfaces.obc_gs_interface.commands.python.command_factories import COMMAND_FACTORIES


class CLICommand:
    """
    An abstraction of the CLI commands so that adapting the commns pipeline packet logic
    into GS will be easier.
    """

    def __init__(self, params: dict[str, str | int | bool | float], cmd_id: int, prio: int) -> None:
        """
        This abstracts the CLI commands in a way which makes it accessable for GS.
        The reason this is created is so that we are able to have a 1:1 clone of the
        CLI commands which allow for easier adoption of prexisting pipelines built for CLI.

        :name: name which matches the CLI command name
        :id: id which matches the id in the satelite
        :params: list of command as a string, matches CLI command param options
        :prio: command priority. integer which goes from 1 to n where n is the number of
               priorities we have. 1 is the highest priority
        :time: tracks the time at which a command has been created
        """
        self.command: Commands | None = None
        self.command_id: CmdCallbackId | None = None
        self.factory_args: list[str | int | bool | float] = []

        try:
            self.command_id = CmdCallbackId(cmd_id)
        except KeyError:
            # TODO: Find a better way of logging this
            print("Invalid Command Id", cmd_id)

        # We need to ensure that these are given in the right order
        # TODO: these are dummy param names, they need to be updated
        for param_name, param in params.items():
            if param_name == "time_of_execution":
                self.factory_args.append(param)
            if param_name == "log_level" or param_name == "rtc_time":
                self.factory_args.insert(0, param)

        if self.command_id is not None:
            self.cmd_msg = COMMAND_FACTORIES[self.command_id](*self.factory_args)
        else:
            # TODO: Better error handling
            print("Command ID unbound")

        self.prio = prio
        self.time = datetime.now()
