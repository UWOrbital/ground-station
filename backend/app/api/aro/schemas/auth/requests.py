from fastapi_users import schemas
from pydantic import BaseModel, ConfigDict

from app.api.aro.schemas.types import (
    AddressField,
    AROEmailField,
    CallSign,
    ClubName,
    FirstName,
    GeneralLocationField,
    LastName,
    PostalCode,
    QualLevels,
)

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

    A user's claimed registry details, matched against AROUserCallsigns. Mirrors that table's columns.
    Optional fields may be omitted or null; blank strings are rejected.

    :call_sign CallSign
    :first_name FirstName | None
    :last_name LastName | None
    :personal_address AddressField | None
    :personal_city GeneralLocationField | None
    :personal_province GeneralLocationField | None
    :personal_postal_code PostalCode | None
    :qual_levels QualLevels: exactly 5, index 0..4 = levels A..E
    :club_name ClubName | None
    :second_club_name ClubName | None
    :club_address AddressField | None
    :club_city GeneralLocationField | None
    :club_province GeneralLocationField | None
    :club_postal_code PostalCode | None
    """

    # Unknown keys are an error, not silently dropped
    model_config = ConfigDict(extra="forbid")

    call_sign: CallSign
    first_name: FirstName | None = None
    last_name: LastName | None = None
    personal_address: AddressField | None = None
    personal_city: GeneralLocationField | None = None
    personal_province: GeneralLocationField | None = None
    personal_postal_code: PostalCode | None = None
    qual_levels: QualLevels
    club_name: ClubName | None = None
    second_club_name: ClubName | None = None
    club_address: AddressField | None = None
    club_city: GeneralLocationField | None = None
    club_province: GeneralLocationField | None = None
    club_postal_code: PostalCode | None = None
