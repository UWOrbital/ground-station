from typing import Any

from pydantic import BaseModel, EmailStr, model_validator


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
