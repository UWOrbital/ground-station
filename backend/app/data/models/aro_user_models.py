from datetime import UTC, datetime
from typing import Final
from uuid import UUID, uuid4

from pydantic import EmailStr
from sqlalchemy import Column, DateTime
from sqlmodel import Field

from app.config.data_values import (
    CALL_SIGN_MAX_LENGTH,
    CALL_SIGN_MIN_LENGTH,
    DEFAULT_MAX_LENGTH,
    EMAIL_MIN_LENGTH,
)
from app.data.models.base_model import BaseSQLModel

# Schema information
ARO_USER_SCHEMA_NAME: Final[str] = "aro_users"

# Table names in database
ARO_USER_TABLE_NAME: Final[str] = "users_data"
ARO_USER_CALLSIGNS: Final[str] = "callsigns"
ARO_USER_LOGIN: Final[str] = "user_login"
ARO_AUTH_TOKEN: Final[str] = "auth_tokens"


class AROUsers(BaseSQLModel, table=True):
    """
    Stores all the information about an ARO user

    :param id: ARO User ID. Auto generated on insert
    :type id: UUID
    :param call_sign: ARO User's call sign that we will use to communicate with them
    :type call_sign: str
    :param is_active: bool
    :param is_callsign_verified: ARO User's callsign verification status
    :type is_callsign_verified: bool
    :param email: Valid email
    :type email: EmailStr
    :param first_name: First name of ARO user
    :type first_name: str
    :param last_name: Optional last name
    :type last_name: str, None
    :param phone_number: Valid phone number
    :type phone_number: str
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    call_sign: str | None = Field(
        min_length=CALL_SIGN_MIN_LENGTH, max_length=CALL_SIGN_MAX_LENGTH, default=None, nullable=True
    )
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_callsign_verified: bool = Field(default=False)
    email: EmailStr = Field(min_length=EMAIL_MIN_LENGTH, max_length=DEFAULT_MAX_LENGTH, unique=True)
    first_name: str = Field(max_length=DEFAULT_MAX_LENGTH)
    last_name: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)
    phone_number: str | None = Field(default=None)

    __tablename__ = ARO_USER_TABLE_NAME
    __table_args__ = {"schema": ARO_USER_SCHEMA_NAME}


class AROUserCallsigns(BaseSQLModel, table=True):
    """
    Stores all valid callsigns (as of Sept. 6, 2025)

    :param call_sign: a valid callsign
    :type call_sign: str
    """

    call_sign: str = Field(primary_key=True, min_length=CALL_SIGN_MIN_LENGTH, max_length=CALL_SIGN_MAX_LENGTH)
    first_name: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)
    last_name: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)
    personal_address: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)
    personal_city: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)
    personal_province: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)
    personal_postal_code: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)
    qual_level_a: bool = Field()
    qual_level_b: bool = Field()
    qual_level_c: bool = Field()
    qual_level_d: bool = Field()
    qual_level_e: bool = Field()
    club_name: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)
    second_club_name: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)
    club_address: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)
    club_city: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)
    club_province: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)
    club_postal_code: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)

    __tablename__ = ARO_USER_CALLSIGNS
    __table_args__ = {"schema": ARO_USER_SCHEMA_NAME}


class AROUserLogin(BaseSQLModel, table=True):
    """
    Stores all information on AROUserLogin

    :param id: AROUserLogin id
    :param email: AROUserLogin email for login
    :param password: AROUserLogin password hash
    :param created_on: datetime object of the time at which AROUserLogin was created
    :param user_id: id created by AROUsers
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)  # unique id for logins
    email: EmailStr = Field(min_length=EMAIL_MIN_LENGTH, max_length=DEFAULT_MAX_LENGTH, unique=True)
    password: str = Field(max_length=128)
    created_on: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    user_id: UUID = Field(foreign_key="aro_users.users_data.id", unique=True)

    __tablename__ = ARO_USER_LOGIN
    __table_args__ = {"schema": ARO_USER_SCHEMA_NAME}


class AROUserAuthToken(BaseSQLModel, table=True):
    """
    Stores all information for User Auth Refresh Tokens

    :param id: a unique identifier for the user auth token
    :param user_id: id created by AROUser
    :param token_hash: hashed UUID token
    :param family_id: shared id for all tokens descending from one login
    :param created_on: datetime object which tracks the date and time at which user auth token was created
    :param expiry: datetime object which represents the time at which the token expires
    :param rotated_at: when the refresh token was rotated
    :param revoked_at: when a compromised refresh token was revoked
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Field(foreign_key="aro_users.users_data.id")
    family_id: UUID = Field(index=True, nullable=False)
    token_hash: str = Field(index=True, unique=True)
    created_on: datetime = Field(
        default_factory=lambda: datetime.now(UTC), sa_column=Column(DateTime(timezone=True), nullable=False)
    )
    expiry: datetime = Field(sa_column=Column(DateTime(timezone=True), nullable=False))
    rotated_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))
    revoked_at: datetime | None = Field(default=None, sa_column=Column(DateTime(timezone=True), nullable=True))

    __tablename__ = ARO_AUTH_TOKEN
    __table_args__ = {"schema": ARO_USER_SCHEMA_NAME}
