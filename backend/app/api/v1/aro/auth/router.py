"""
api.v1.aro.auth.oauth

Email & password authentication.

After initial authentication, the user will need to additionally verify with their callsign.
"""

from fastapi import APIRouter, Depends

from app.api.v1.aro.auth.dependencies import get_current_user
from app.api.v1.aro.auth.manual.register import (
    login_user,
    logout_user,
    register_user,
)
from app.api.v1.aro.auth.services.callsign_2fa import verify_user_callsign
from app.api.v1.aro.schemas.auth_requests import (
    CallsignRequest,
    LoginRequest,
    RegisterRequest,
)
from app.api.v1.aro.schemas.auth_responses import (
    TokenResponse,
    UserResponse,
)
from app.data.models.aro_user_models import AROUsers

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

router = APIRouter(prefix="/auth", tags=["authentication"])

# ------------------------------------------------------------
# Email / Password Endpoints
# ------------------------------------------------------------


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest) -> TokenResponse:
    """
    register

    Register a new user with email and password.
    Creates AROUsers and AROUserLogin records.
    Returns an auth token for immediate login.

    :param request
    :type RegisterRequest
    :returns: auth token
    :rtype TokenResponse
    """
    auth_token, user = register_user(request)

    return TokenResponse(
        token=str(auth_token.token),
        user_id=user.id,
        expires_at=auth_token.expiry,
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest) -> TokenResponse:
    """
    login

    Validates credentials and returns an auth token.
    If unsuccessful, gives appropriate errors.

    :param request
    :type LoginRequest
    :return: auth token
    :rtype TokenResponse
    """

    auth_token, user = login_user(request)

    return TokenResponse(
        token=str(auth_token.token),
        user_id=user.id,
        expires_at=auth_token.expiry,
    )


@router.post("/logout/{token}")
async def logout(token: str) -> dict[str, str]:
    """
    logout

    Invalidate an auth token (logout).
    Deletes the token from the database.

    :param token
    :type str
    :return: logout message
    :rtype dict[str,str]
    """
    logout_user(token)

    return {"message": "Logged out successfully."}


@router.post("/callsign_callback", response_model=UserResponse)
async def verify_callsign(request: CallsignRequest, user: AROUsers = Depends(get_current_user)) -> UserResponse:
    """
    verify_callsign

    The final step in authentication.
    Verifies a user's callsign and grants them admin access.

    :param request
    :type CallsignRequest
    :param user
    :type AROUsers
    :return: aro user
    :rtype UserResponse
    """
    if not user.is_callsign_verified:
        user = verify_user_callsign(request, user=user)

    return UserResponse(data=user)
