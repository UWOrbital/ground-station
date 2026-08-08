from datetime import datetime, timedelta
from uuid import UUID, uuid4

from app.data.data_wrappers.wrappers import AROUserAuthTokenWrapper
from app.data.enums.aro_auth_token import AROAuthToken
from app.data.models.aro_user_models import AROUserAuthToken


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
