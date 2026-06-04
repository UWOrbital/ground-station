"""
api.v1.aro.auth.oauth

Supports two authentication methods.

1. Google OAuth
2. Email & Password

After initial authentication, the user will need to additionally verify with their callsign.
"""

from typing import cast

from authlib.integrations.starlette_client import OAuth, OAuthError
from config.config import settings
from data.tables.aro_user_tables import AROUsers
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from starlette.requests import Request

from api.v1.aro.auth.dependencies import get_current_user
from api.v1.aro.auth.google.google import google_auth
from api.v1.aro.auth.manual.register import (
    login_user,
    logout_user,
    register_user,
)
from api.v1.aro.auth.services.callsign_2fa import verify_user_callsign
from api.v1.aro.models.auth_requests import (
    CallsignRequest,
    GoogleRequest,
    LoginRequest,
    RegisterRequest,
)
from api.v1.aro.models.auth_responses import (
    TokenResponse,
    UserResponse,
)

# -----------------------------------------------------------------------
# CONFIG
# -----------------------------------------------------------------------

router = APIRouter(prefix="/auth", tags=["authentication"])

# Auth Setup
oauth = OAuth()
oauth.register(
    name="google",
    client_id=settings.auth.google_client_id,
    client_secret=settings.auth.google_client_secret,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)

# -----------------------------------------------------------------------
# Google OAuth Endpoints
# -----------------------------------------------------------------------


@router.get("/google/login")
async def google_login(request: Request) -> RedirectResponse:
    """
    google_login

    Initiate Google OAuth flow.
    Redirect the user back to Google's consent screen.

    :param request
    :type request: Request
    :return: login redirect
    :rtype: RedirectResponse
    """
    # The callback URL must match what's configured on Google Cloud Console
    redirect_uri = request.url_for("google_callback")
    return cast(RedirectResponse, await oauth.google.authorize_redirect(request, redirect_uri))


@router.get("/google/callback")
async def google_callback(request: Request) -> TokenResponse:
    """
    google_callback

    Handle Google OAuth callback.

    Creates a new user if first login, otherwise finds existing user.
    Returns an auth token for the session.

    :param request
    :type request: Request
    :return: auth token
    :rtype TokenResponse
    """
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OAuth authentication failed: {e.error}",
        ) from e

    user_info = token.get("userinfo")
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not retrieve user data from Google.",
        )

    google_request = GoogleRequest(
        google_id=user_info.get("sub"),
        email=user_info.get("email"),
        first_name=user_info.get("given_name", ""),
        last_name=user_info.get("family_name"),
        phone_number=user_info.get("phone_number"),
    )

    auth_token, user = google_auth(google_request)

    return TokenResponse(
        token=str(auth_token.token),
        user_id=user.id,
        expires_at=auth_token.expiry,
    )


# -----------------------------------------------------------------------
# Email / Password Endpoints
# -----------------------------------------------------------------------


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
