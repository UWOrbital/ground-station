from datetime import datetime
from typing import Literal
from uuid import UUID

from fastapi_users import schemas
from pydantic import BaseModel

from app.api.v1.aro.schemas.types import AccessToken

# -----------------------------------------------------------------
# Auth Responses
# -----------------------------------------------------------------


class UserRead(schemas.BaseUser[UUID]):
    """
    User data returned by /register and other user reads.
    """

    is_callsign_verified: bool = False


class AccessTokenResponse(BaseModel):
    """
    Response body for POST /login and POST /refresh.
    """

    access_token: AccessToken
    token_type: Literal["bearer"] = "bearer"
    expires_at: datetime
