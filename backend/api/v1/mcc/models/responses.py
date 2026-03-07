from pydantic import BaseModel, Field
from typing import Annotated

from data.tables.transactional_tables import Commands
from data.tables.main_tables import MainCommand


class MainCommandsResponse(BaseModel):
    """
    The main commands response model.
    """

    data: Annotated[list[MainCommand], Field(description="A list comtaining MainCommand objects")]

class CommandsResponse(BaseModel):
    """
    The command response model
    """
    data: Annotated[list[Commands], Field(description="A list containing Command objects")]