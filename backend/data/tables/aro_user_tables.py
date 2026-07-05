from datetime import datetime
from typing import Final
from uuid import UUID, uuid4

from config.data_config import (
    CALL_SIGN_MAX_LENGTH,
    CALL_SIGN_MIN_LENGTH,
    DEFAULT_MAX_LENGTH,
    EMAIL_MIN_LENGTH,
)
from pydantic import EmailStr
from sqlalchemy import Enum
from sqlalchemy.dialects.postgresql import UUID as DB_UUID
from sqlalchemy.schema import Column, ForeignKey
from sqlmodel import Field

from data.enums.aro_auth_token import AROAuthToken
from data.tables.base_model import BaseSQLModel

# Schema information
ARO_USER_SCHEMA_NAME: Final[str] = "aro_users"

# Table names in database
ARO_USER_TABLE_NAME: Final[str] = "users_data"
ARO_USER_CALLSIGNS: Final[str] = "callsigns"
ARO_USER_LOGIN: Final[str] = "user_login"
ARO_AUTH_TOKEN: Final[str] = "auth_tokens"
ARO_USER_KEY: Final[str] = "aro_user_keys"


class AROUsers(BaseSQLModel, table=True):
    """
    Stores all the information about an ARO user

    :param id: ARO User ID. Auto generated on insert
    :type id: UUID
    :param call_sign: ARO User's call sign that we will use to communicate with them
    :type call_sign: str
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
        min_length=CALL_SIGN_MIN_LENGTH,
        max_length=CALL_SIGN_MAX_LENGTH,
        default=None,
        nullable=True,
    )

    # Critical 2FA variable
    google_id: str | None = Field(default=None, unique=True, index=True)
    is_callsign_verified: bool = Field(default=False)

    # We are currently verifying with email + pwd
    email: EmailStr = Field(min_length=EMAIL_MIN_LENGTH, max_length=DEFAULT_MAX_LENGTH, unique=True)
    first_name: str = Field(max_length=DEFAULT_MAX_LENGTH)
    last_name: str | None = Field(max_length=DEFAULT_MAX_LENGTH, nullable=True, default=None)
    phone_number: str | None = Field(default=None)

    # table information
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
    :param password: AROUserLogin password for login
    :param salt: 16 random bytes for password hashing
    :param created_on: datetime object of the time at which AROUserLogin was created
    :param hashing_algorithm_name: the name of the hashing algorithm for pwd hashing
    :param user_id: id created by AROUsers
    :param email_verification_token: given after user verifies
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)  # unique id for logins
    email: EmailStr = Field(min_length=EMAIL_MIN_LENGTH, max_length=DEFAULT_MAX_LENGTH, unique=True)
    password: str = Field(max_length=128)
    password_salt: str = Field(max_length=32)
    created_on: datetime = Field(default_factory=datetime.now)
    hashing_algorithm_name: str = Field(min_length=1, max_length=20)
    user_id: UUID = Column(DB_UUID, ForeignKey(AROUsers.id))  # type: ignore
    email_verification_token: str = Field(min_length=1, max_length=200)

    __tablename__ = ARO_USER_LOGIN
    __table_args__ = {"schema": ARO_USER_SCHEMA_NAME}


class AROUserAuthToken(BaseSQLModel, table=True):
    """
    Stores all information for User Auth Tokens

    :param id: a unique identifier for the user auth token
    :param user_id: id created by AROUser
    :param token: UUID token
    :param created_on: datetime object which tracks the date and time at which user auth token was created
    :param expiry: datetime object which represents the time at which the token expires
    :param type_: the type of the token
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Column(DB_UUID, ForeignKey(AROUsers.id))  # type: ignore
    token: UUID = Field(default_factory=uuid4)
    created_on: datetime = Field(default_factory=datetime.now)
    expiry: datetime = Field()
    type_: AROAuthToken = Field(sa_column=Column("type", Enum(AROAuthToken, name="auth_type"), nullable=False))

    __tablename__ = ARO_AUTH_TOKEN
    __table_args__ = {"schema": ARO_USER_SCHEMA_NAME}


class AROUserKey(BaseSQLModel, table=True):
    """
    ARO authentication keys for satellite direct communication.

    Each ARO user can have multiple keys, but only one active at a time.
    The active key is synced to the OBC before a pass so the satellite
    can authenticate the operator.

    :param id: Primary key
    :type id: UUID
    :param user_id: Foreign key to the ARO user who owns this key
    :type user_id: UUID
    :param key_data: Hex-encoded 32-byte AES-256 key (64 characters)
    :type key_data: str
    :param name: Optional friendly label
    :type name: str | None
    :param is_active: Whether this is the user's current active key
    :type is_active: bool
    :param created_at: When the key was generated
    :type created_at: datetime
    :param synced_to_obc_at: When the key was last uplinked to the satellite
    :type synced_to_obc_at: datetime | None
    """

    id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    user_id: UUID = Column(DB_UUID, ForeignKey(AROUsers.id))
    key_data: str = Field(max_length=64)
    name: str | None = Field(max_length=50, default=None)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.now)
    synced_to_obc_at: datetime | None = Field(default=None)

    __tablename__ = ARO_USER_KEY
    __table_args__ = {"schema": ARO_USER_SCHEMA_NAME}
