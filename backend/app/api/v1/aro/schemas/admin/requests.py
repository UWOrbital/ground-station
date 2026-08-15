from pydantic import BaseModel, EmailStr, field_validator

from app.api.v1.aro.schemas.types import CallSign, FirstName, LastName, PhoneNumber

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
        """EmailStr lowercases the domain but not the local part — do that too."""
        return v.lower()
