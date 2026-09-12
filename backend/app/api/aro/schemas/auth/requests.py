from fastapi_users import schemas
from pydantic import BaseModel

from app.api.aro.schemas.types import AROEmailField, CallSign, FirstName

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

    Request containing the callsign a user wants verified.

    :call_sign str
    """

    call_sign: CallSign
