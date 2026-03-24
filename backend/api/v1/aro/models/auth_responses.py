from datetime import datetime
from typing import Self
from uuid import UUID

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
        # Pydantic already enforces the field types — we only add checks
        # that go beyond what type validation can catch.
        if len(self.token) < 32:
            raise ValueError("Generated token is too short to be valid.")
        return self
