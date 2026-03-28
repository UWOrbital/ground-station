from datetime import datetime

from data.data_wrappers.wrappers import (
    AROUserAuthTokenWrapper,
    AROUsersWrapper,
)
from data.tables.aro_user_tables import AROUsers
from fastapi import APIRouter, Depends, HTTPException, status

from api.v1.aro.models.auth_responses import UserResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


async def get_current_user(token: str) -> AROUsers:
    """
    Dependency: resolve a token string to the authenticated AROUsers record.
    Raises HTTP 401/404 on invalid or expired tokens.
    """
    token_wrapper = AROUserAuthTokenWrapper()
    user_wrapper = AROUsersWrapper()

    auth_token = token_wrapper.get_token_by_token(token)

    if not auth_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Couldn't find your login credentials. How did you even log in?",
        )

    if auth_token.expiry < datetime.now():
        token_wrapper.delete_by_id(auth_token.id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Your login expired.",
        )

    try:
        user = user_wrapper.get_by_id(auth_token.user_data_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Couldn't find the user from ID.") from e

    return user


@router.get("/current_user")
async def current_user_endpoint(user: AROUsers = Depends(get_current_user)) -> UserResponse:
    """Get the current user's information from their auth token."""
    return UserResponse(data=user)


@router.post("/verify_callsign")
def require_verified_user(user: AROUsers = Depends(get_current_user)) -> AROUsers:
    """Check if the user's callsign is verified, otherwise raise an error."""
    if not user.is_callsign_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Callsign verification required")
    return user
