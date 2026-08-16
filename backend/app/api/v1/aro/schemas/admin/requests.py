from pydantic import BaseModel, EmailStr, field_validator

from app.api.v1.aro.schemas.types import CallSign, FirstName, LastName, PhoneNumber
from app.config.data_values import EMAIL_MIN_LENGTH

# -----------------------------------------------------------------
# Admin Requests
# -----------------------------------------------------------------


class UserRequest(BaseModel):
    """
    Model representing the user to be created directly by an operator.
    """

    call_sign: CallSign
    email: EmailStr
    first_name: FirstName
    last_name: LastName
    phone_number: PhoneNumber

    @field_validator("email", mode="after")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        """Enforce email length and lowercase the local part."""
        if len(v) < EMAIL_MIN_LENGTH:
            raise ValueError(f"First name cannot be shorter than {EMAIL_MIN_LENGTH} characters.")
        return v.lower()
