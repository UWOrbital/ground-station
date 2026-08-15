import re

from fastapi_users import schemas
from pydantic import BaseModel, field_validator

from app.api.v1.aro.schemas.types import CallSign, FirstName

# -----------------------------------------------------------------
# Auth Requests
# -----------------------------------------------------------------


class UserCreate(schemas.BaseUserCreate):
    """Registration payload accepted by the built-in /register route."""
    first_name: FirstName

    @field_validator("first_name", mode='after')
    @classmethod
    def validate_first_name(cls, v: str) -> str:
        """Restrict to letter-like characters and title-case the result."""
        if not re.match(r"^[A-Za-zÀ-ÿ'\s\-]+$", v):
            raise ValueError("First name can only contain letters, spaces, hyphens, or apostrophes.")
        return v.title()

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """EmailStr lowercases the domain but not the local part — do that too."""
        return v.lower()


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
