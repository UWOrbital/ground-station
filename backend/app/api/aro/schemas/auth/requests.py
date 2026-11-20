from fastapi_users import schemas
from pydantic import BaseModel

from app.api.aro.schemas.types import AROEmailField, CallSign, FirstName, LastName, PhoneNumber

# -----------------------------------------------------------------
# Auth Requests
# -----------------------------------------------------------------


class UserCreate(schemas.BaseUserCreate):
    """Registration payload accepted by the built-in /register route."""

    first_name: FirstName
    last_name: LastName | None = None
    email: AROEmailField
    call_sign: CallSign
    phone_number: PhoneNumber | None = None


class CallsignRequest(BaseModel):
    """
    CallsignRequest

    Request containing callsign data of a user.

    :call_sign str
    :qual_level_a bool
    :qual_level_b bool
    :qual_level_c bool
    :qual_level_d bool
    :qual_level_e bool
    """

    call_sign: CallSign
    qual_level_a: bool
    qual_level_b: bool
    qual_level_c: bool
    qual_level_d: bool
    qual_level_e: bool
