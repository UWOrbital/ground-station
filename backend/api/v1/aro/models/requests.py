from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserRequest(BaseModel):
    """
    Model representing the user to be created.
    """

    call_sign: str
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str


class PictureRequest(BaseModel):
    """
    Model representing the picture request to be created.
    """

    aro_id: UUID
    latitude: Decimal
    longitude: Decimal
