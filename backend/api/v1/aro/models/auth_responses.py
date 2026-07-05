from datetime import datetime
from typing import Self
from uuid import UUID

from data.tables.aro_user_tables import AROUserKey, AROUsers
from pydantic import BaseModel, model_validator


class TokenResponse(BaseModel):
    """
    TokenResponse

    Response body for the authentication token for both google and email/password flows.

    :param token str
    :param user_id UUID
    :param expires_at datetime
    """

    token: str
    user_id: UUID
    expires_at: datetime

    @model_validator(mode="after")
    def validate_token(self) -> Self:
        """Ensure the token meets minimum length requirements."""
        # Pydantic already enforces the field types — we only add checks
        # that go beyond what type validation can catch.
        if len(self.token) < 32:
            raise ValueError("Generated token is too short to be valid.")
        return self


class AllUsersResponse(BaseModel):
    """
    The users response model.
    """

    data: list[AROUsers]


class UserResponse(BaseModel):
    """
    Single user response model.
    """

    data: AROUsers


class GenerateKeyResponse(BaseModel):
    """
    GenerateKeyResponse

    Response returned after successfully generating a new ARO key.

    :param data: The newly created key
    :type data: AROUserKey
    """

    data: AROUserKey


class CurrentKeyResponse(BaseModel):
    """
    CurrentKeyResponse

    Response containing the ARO user's currently active key, if one exists.

    :param data: The active key, or None if no keys exist
    :type data: AROUserKey | None
    """

    data: AROUserKey | None


class GetAllKeysResponse(BaseModel):
    """
    GetAllKeysResponse

    Response containing all keys belonging to the authenticated ARO user.

    :param data: List of the user's keys
    :type data: list[AROUserKey]
    """

    data: list[AROUserKey]


class SyncKeysResponse(BaseModel):
    """
    SyncKeysResponse

    Response returned after marking a key as synced to the OBC.

    :param message: Confirmation message
    :type message: str
    :param key_id: UUID of the synced key
    :type key_id: UUID
    """

    message: str
    key_id: UUID
