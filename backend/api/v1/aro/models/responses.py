from typing import Any

from data.tables.aro_user_tables import AROUsers
from data.tables.transactional_tables import ARORequest, PacketCommands
from pydantic import BaseModel


class AllUsersResponse(BaseModel):
    """
    The users response model.
    """

    data: list[AROUsers]


class UserResponse(BaseModel):
    """
    Single user response model.
    """

    data: AROUsers


class AllPictureResponse(BaseModel):
    """
    The picture request response model.
    """

    data: list[ARORequest]
    operations: list[dict[str, Any]]


class PictureResponse(BaseModel):
    """
    Single picture request response model.
    """

    data: ARORequest
    operations: dict[str, Any]


class PacketCommandResponse(BaseModel):
    """
    Single command packet response model.
    """

    data: PacketCommands
    operations: dict[str, Any]
