from datetime import datetime, timedelta
from uuid import UUID, uuid4

from data.data_wrappers.wrappers import (
    AROUserAuthTokenWrapper,
    AROUsersWrapper,
)
from data.enums.aro_auth_token import AROAuthToken
from data.tables.aro_user_tables import (
    AROUserAuthToken,
    AROUsers,
)
from pydantic import EmailStr

TOKEN_EXPIRY_HOURS = 6.7


def create_auth_token(user_id: UUID, auth_type: AROAuthToken) -> AROUserAuthToken:
    """Return an existing valid token for the user, or create and persist a new one."""
    token_wrapper = AROUserAuthTokenWrapper()

    existing = next(
        (t for t in token_wrapper.get_all() if t.user_data_id == user_id and t.expiry > datetime.now()),
        None,
    )
    if existing:
        return existing

    created_time = datetime.now()
    expiry = created_time + timedelta(hours=TOKEN_EXPIRY_HOURS)
    token_value = str(uuid4())

    auth_token = token_wrapper.create(
        {
            "user_data_id": user_id,
            "token": token_value,
            "created_on": created_time,
            "expiry": expiry,
            "auth_type": auth_type,
        }
    )

    return auth_token


def create_oauth_user(google_id: str, email: EmailStr, first_name: str, last_name: str | None) -> AROUsers:
    """Create a new user from Google OAuth data."""
    # Create a new user from Google OAuth data.
    users = AROUsersWrapper()
    user = users.create(
        {
            "google_id": google_id,
            "email": email,
            "first_name": first_name,
            "last_name": last_name,
            "call_sign": None,
            "is_callsign_verified": False,
        }
    )

    return user
