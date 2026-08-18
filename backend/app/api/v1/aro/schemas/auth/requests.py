from fastapi_users import schemas
from pydantic import BaseModel, field_validator

from app.api.v1.aro.schemas.types import CallSign, AROEmailField, FirstName
from app.config.data_values import EMAIL_MIN_LENGTH

# -----------------------------------------------------------------
# Auth Requests
# -----------------------------------------------------------------


class UserCreate(schemas.BaseUserCreate):
    """Registration payload accepted by the built-in /register route."""

    first_name: FirstName
    email: AROEmailField


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
