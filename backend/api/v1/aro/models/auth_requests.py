from typing import Any, Self
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, model_validator

# -----------------------------------------------------------------------
# Request & Responses
# -----------------------------------------------------------------------


class RegisterRequest(BaseModel):
    """
    RegisterRequest

    Request body for email/password registration.

    :param email Emailstr
    :param password str
    :param first_name str
    :param last_name str
    :param phone_number str
    """

    email: EmailStr
    password: str
    first_name: str
    last_name: str | None = None
    phone_number: str | None = None

    @model_validator(mode="before")
    @classmethod
    def sanitize_inputs(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Strip and normalize email, name, and password fields before validation."""
        # email: raw input is always a plain str, not EmailStr
        if isinstance(data.get("email"), str):
            data["email"] = data["email"].strip().lower()
        if isinstance(data.get("first_name"), str):
            data["first_name"] = data["first_name"].strip()
        # strip whitespace only, never lowercase
        if isinstance(data.get("last_name"), str):
            data["last_name"] = data["last_name"].strip()
        if isinstance(data.get("password"), str):
            data["password"] = data["password"].replace(" ", "")
        return data

    @model_validator(mode="after")
    def validate_password_strength(self) -> Self:
        """Enforce minimum password strength requirements."""
        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if not any(c.isdigit() for c in self.password):
            raise ValueError("Password must include at least one digit.")
        if not any((not c.isalnum() and not c.isspace()) for c in self.password):
            raise ValueError("Password must include at least one special character.")
        return self


class LoginRequest(BaseModel):
    """
    LoginRequest

    Request body for email/password login.

    :param email EmailStr
    :param password str
    """

    email: EmailStr
    password: str

    @model_validator(mode="before")
    @classmethod
    def sanitize_inputs(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize email to lowercase before validation."""
        if isinstance(data.get("email"), str):
            data["email"] = data["email"].strip().lower()
        return data

    @model_validator(mode="after")
    def validate_no_spaces_in_password(self) -> Self:
        """Reject passwords containing spaces."""
        if " " in self.password:
            raise ValueError("Password must not contain spaces.")
        return self


class UserRequest(BaseModel):
    """
    Model representing the user to be created.
    """

    call_sign: str
    email: EmailStr
    first_name: str
    last_name: str
    phone_number: str

    @model_validator(mode="before")
    @classmethod
    def sanitize_inputs(cls, data: dict[str, Any]) -> dict[str, Any]:
        """
        :cls Self@UserRequest
        :data dict[str, Any]
        """
        if isinstance(data.get("call_sign"), str):
            data["call_sign"] = data["call_sign"].strip()
        if isinstance(data.get("email"), str):
            data["email"] = data["email"].strip().lower()
        if isinstance(data.get("first_name"), str):
            data["first_name"] = data["first_name"].strip()
        if isinstance(data.get("last_name"), str):
            data["last_name"] = data["last_name"].strip()
        if isinstance(data.get("phone_number"), str):
            data["phone_number"] = data["phone_number"].strip()

        return data


class GoogleRequest(BaseModel):
    """
    GoogleRequest

    Data extracted from Google's OAuth userinfo token.

    :param google_id str  — Google's 'sub' claim, unique per Google account
    :param email EmailStr
    :param first_name str
    :param last_name str | None
    :param phone_number str | None
    """

    google_id: str
    email: EmailStr
    first_name: str
    last_name: str | None = None
    phone_number: str | None = None

    @model_validator(mode="before")
    @classmethod
    def sanitize_inputs(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Strip whitespace from all string fields and normalize email to lowercase."""
        if isinstance(data.get("google_id"), str):
            data["google_id"] = data["google_id"].strip()
        if isinstance(data.get("email"), str):
            data["email"] = data["email"].strip().lower()
        if isinstance(data.get("first_name"), str):
            data["first_name"] = data["first_name"].strip()
        if isinstance(data.get("last_name"), str):
            data["last_name"] = data["last_name"].strip()
        if isinstance(data.get("phone_number"), str):
            data["phone_number"] = data["phone_number"].strip()
        return data

    @model_validator(mode="after")
    def validate_google_id(self) -> Self:
        """Ensure google_id is not empty after sanitization."""
        if not self.google_id:
            raise ValueError("google_id cannot be empty.")
        return self


class GenerateKeyRequest(BaseModel):
    """
    GenerateKeyRequest

    Request body to generate a new ARO authentication key.

    :param name: Optional friendly label for the key (e.g. "My Primary Key")
    :type name: str | None
    """

    name: str | None = Field(default=None, max_length=50)

    @model_validator(mode="before")
    @classmethod
    def sanitize_name(cls, data: dict[str, str]) -> dict[str, str]:
        """Strip whitespace from the name if provided."""
        if isinstance(data.get("name"), str):
            data["name"] = data["name"].strip()
        return data


class SyncKeysRequest(BaseModel):
    """
    SyncKeysRequest

    Request body to mark an ARO authentication key as synced to the OBC.

    :param key_id: The UUID of the key to mark as synced
    :type key_id: UUID
    """

    key_id: UUID


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

    call_sign: str
    qual_level_a: bool
    qual_level_b: bool
    qual_level_c: bool
    qual_level_d: bool
    qual_level_e: bool

    @model_validator(mode="before")
    @classmethod
    def normalize_callsign(cls, data: dict[str, Any]) -> dict[str, Any]:
        """Normalize callsign to uppercase and strip surrounding whitespace."""
        if isinstance(data.get("call_sign"), str):
            data["call_sign"] = data["call_sign"].strip().upper()
        return data
