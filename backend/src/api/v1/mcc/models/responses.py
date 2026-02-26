from data.tables.main_tables import MainCommand
from pydantic import BaseModel


class MainCommandsResponse(BaseModel):
    """
    The main commands response model.
    """

    data: list[MainCommand]
