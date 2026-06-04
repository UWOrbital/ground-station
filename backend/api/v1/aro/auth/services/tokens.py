from datetime import datetime, timedelta
from uuid import UUID, uuid4

from api.v1.aro.models.auth_requests import GoogleRequest
from data.data_wrappers.wrappers import (
    AROUserAuthTokenWrapper,
    AROUsersWrapper,
)
from data.enums.aro_auth_token import AROAuthToken
from data.tables.aro_user_tables import (
    AROUserAuthToken,
    AROUsers,
)


def create_auth_token(user_id: UUID, auth_type: AROAuthToken) -> AROUserAuthToken:
    """Return an existing valid token for the user, or create and persist a new one."""
    token_wrapper = AROUserAuthTokenWrapper()

    existing = token_wrapper.get_token_by_user_id(user_id)

    if existing:
        return existing

    token_value = uuid4()
    created_time = datetime.now()
    expiry = created_time + timedelta(hours=6.7)

    auth_token = token_wrapper.create(
        {
            "user_id": user_id,
            "token": token_value,
            "created_on": created_time,
            "expiry": expiry,
            "type_": auth_type,
        }
    )

    return auth_token


def create_oauth_user(user_request: GoogleRequest) -> AROUsers:
    """Create a new user from Google OAuth data."""
    users = AROUsersWrapper()
    user = users.create(
        {
            "google_id": user_request.google_id,
            "email": user_request.email,
            "first_name": user_request.first_name,
            "last_name": user_request.last_name,
            "call_sign": None,
            "is_callsign_verified": False,
        }
    )

    return user
