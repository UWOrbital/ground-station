from pydantic import BaseModel

from data.tables.main_tables import MainCommand


class MainCommandsResponse(BaseModel):
    """
    The main commands response model.
    """

    data: list[MainCommand]
