from os import urandom
from uuid import uuid4

from api.v1.aro.endpoints.auth.services.password import (
    hash_password,
    verify_password,
)
from api.v1.aro.endpoints.auth.services.tokens import create_auth_token
from api.v1.aro.models.auth_requests import LoginRequest, RegisterRequest
from data.data_wrappers.wrappers import (
    AROUserAuthTokenWrapper,
    AROUserLoginWrapper,
    AROUsersWrapper,
)
from data.enums.aro_auth_token import AROAuthToken
from data.tables.aro_user_tables import (
    AROUserAuthToken,
    AROUsers,
)
from fastapi import HTTPException, status

HASH_ALGORITHM = "sha256"


def register_user(request: RegisterRequest) -> tuple[AROUserAuthToken, AROUsers]:
    """
    Register a new user with email and password, creating login credentials and returning an auth token.

    :request RegisterRequest
    :returns [AROUserAuthToken, AROUsers]
    """
    users = AROUsersWrapper()
    logins = AROUserLoginWrapper()

    # check for existing email
    existing_user = next((u for u in users.get_all() if u.email == request.email), None)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email has already been taken.",
        )

    user = users.create(
        {
            "call_sign": None,
            "is_callsign_verified": False,
            "email": request.email,
            "first_name": request.first_name,
            "last_name": request.last_name,
            "phone_number": request.phone_number,
        }
    )

    salt = urandom(16)
    verification_token = str(uuid4())
    hashed_password = hash_password(request.password, salt)

    logins.create(
        {
            "email": request.email,
            "password": hashed_password,
            "password_salt": salt.hex(),
            "hashing_algorithm_name": HASH_ALGORITHM,
            "user_data_id": user.id,
            "email_verification_token": verification_token,
        }
    )

    auth_token = create_auth_token(user.id, AROAuthToken.EMAIL_PASSWORD)

    return (auth_token, user)


def login_user(request: LoginRequest) -> tuple[AROUserAuthToken, AROUsers]:
    """
    Verify login credentials and return an auth token for an authenticated user.

    :request LoginRequest
    :returns [AROUserAuthToken, AROUsers]
    """
    users = AROUsersWrapper()
    login = AROUserLoginWrapper()

    login_record = next((item for item in login.get_all() if item.email == request.email), None)
    if not login_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login credentials invalid.",
        )

    if not verify_password(request.password, login_record.password_salt, login_record.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    user = users.get_by_id(login_record.user_data_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User data not found.",
        )

    auth_token = create_auth_token(user.id, AROAuthToken.EMAIL_PASSWORD)

    return (auth_token, user)


def logout_user(token: str) -> None:
    """Invalidate an auth token by deleting it from the database."""
    auth_tokens = AROUserAuthTokenWrapper()
    auth_token = auth_tokens.get_by_token(token)

    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find your login credentials. How did you even log in?",
        )

    auth_tokens.delete_by_id(auth_token.id)
