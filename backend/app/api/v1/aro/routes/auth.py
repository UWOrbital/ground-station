"""
router.py

Email & password authentication.

After initial authentication, the user can authorize with their callsign at signup, or later in the ARO user dashboard.
"""

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_users.router import get_register_router

from app.api.v1.aro.auth.aro_session import (
    create_access_token,
    get_user_by_token,
    issue_refresh_token,
    revoke_token,
    rotate_refresh_token,
)
from app.api.v1.aro.auth.manager import AROUserManager, get_user_manager
from app.api.v1.aro.auth.services.callsign_2fa import verify_user_callsign
from app.api.v1.aro.schemas.auth.requests import CallsignRequest, UserCreate
from app.api.v1.aro.schemas.auth.responses import AccessTokenResponse, UserRead
from app.config.env_settings.backend_config import settings
from app.data.models.aro_user_models import AROUsers

router = APIRouter(prefix="/auth", tags=["authentication"])

# --- Authentication Endpoints --------------------------------------------------

# POST /api/v1/aro/auth/register
router.include_router(get_register_router(get_user_manager, UserRead, UserCreate))


def _set_refresh_cookie(response: Response, raw_refresh_token: str) -> None:
    """
    Set the refresh-token cookie.

    :param response: the outgoing response
    :param raw_refresh_token: the unhashed refresh token value
    """
    response.set_cookie(
        "refresh_token",
        raw_refresh_token,
        httponly=True,
        secure=settings.auth.is_production,
        samesite="lax",
    )


@router.post("/login", response_model=AccessTokenResponse)
async def login(
    response: Response,
    request: OAuth2PasswordRequestForm = Depends(),
    *,
    user_manager: AROUserManager = Depends(get_user_manager),
) -> AccessTokenResponse:
    """
    POST /api/v1/aro/auth/login

    Validates credentials and returns an auth token.

    :param response: Response
    :param request: OAuth2PasswordRequestForm: depends on internal form fields
    :returns: AccessTokenResponse
    """
    user = await user_manager.authenticate(credentials=request)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid credentials.", "code": "invalid_credentials"},
        )

    access_token, expiry = create_access_token(user._user)
    raw_refresh_token = issue_refresh_token(user.id)

    _set_refresh_cookie(response, raw_refresh_token)

    return AccessTokenResponse(access_token=access_token, token_type="bearer", expires_at=expiry)


@router.post("/rotate_tokens", response_model=AccessTokenResponse)
async def rotate_tokens(response: Response, refresh_token: str | None = Cookie(default=None)) -> AccessTokenResponse:
    """
    POST /api/v1/aro/auth/rotate_tokens

    Rotates the refresh token and issues a new access token.

    :param response: Response
    :param refresh_token: str | None: refresh token extracted from the HTTP cookie
    :returns: AccessTokenResponse
    """
    if refresh_token is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Not authenticated.", "code": "missing_refresh_token"},
        )

    new_raw_refresh, user = rotate_refresh_token(refresh_token)
    access_token, expiry = create_access_token(user)

    _set_refresh_cookie(response, new_raw_refresh)

    return AccessTokenResponse(access_token=access_token, token_type="bearer", expires_at=expiry)


@router.post("/logout")
async def logout(response: Response, refresh_token: str | None = Cookie(default=None)) -> dict[str, str]:
    """
    POST /api/v1/aro/auth/logout

    Invalidate a refresh token (logout).

    :param response: Response
    :returns: dict[str, str]: Logout Message
    """
    revoke_token(refresh_token)
    response.delete_cookie(key="refresh_token")
    return {"message": "Logged out successfully."}


# --- Utility Endpoints ---------------------------------------------------------


@router.get("/get_current_user", response_model=UserRead)
async def get_current_user(user: AROUsers = Depends(get_user_by_token)) -> AROUsers:
    """
    GET /api/v1/aro/auth/get_current_user

    Retrive the current user by access token.

    :param user: AROUsers
    :returns: AROUsers
    """
    return user


@router.post("/callsign_callback", response_model=UserRead)
async def callsign_callback(request: CallsignRequest, user: AROUsers = Depends(get_user_by_token)) -> AROUsers:
    """
    POST /api/v1/aro/auth/callsign_callback

    Validates a user's callsign against the AROUserCallsigns table.

    :param user: AROUsers
    :returns: AROUsers
    """
    return verify_user_callsign(request, user)
