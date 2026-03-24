from typing import Annotated

from data.tables.main_tables import MainCommand
from data.tables.transactional_tables import Commands
from pydantic import BaseModel, Field


class MainCommandsResponse(BaseModel):
    """
    The main command response model
    """

    data: Annotated[list[MainCommand], Field(description="A list containing MainCommand objects")]


class CommandsResponse(BaseModel):
    """
    The command response model
    """

    data: Annotated[list[Commands], Field(description="A list containing Command objects")]
