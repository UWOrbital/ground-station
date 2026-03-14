from datetime import datetime
from uuid import uuid4

from api.v1.aro.endpoints.auth.services.tokens import create_auth_token
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
from pydantic import EmailStr


def google_auth(
    google_id: str, email: EmailStr, phone_number: str | None, first_name: str, last_name: str
) -> tuple[AROUserAuthToken, AROUsers]:
    """Authenticate a user via Google OAuth, creating a new account if necessary."""
    users = AROUsersWrapper()
    logins = AROUserLoginWrapper()
    tokens = AROUserAuthTokenWrapper()

    # Try google ID
    all_users = users.get_all()
    user = next((u for u in all_users if u.google_id == google_id), None)

    # If not, try the email
    if not user:
        user = next((u for u in all_users if u.email == email), None)

        if user:
            # Link user account
            user = users.update(
                user.id,
                {"google_id": google_id},
            )
        else:
            # Create a new account
            user = users.create(
                {
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "google_id": google_id,
                    "phone_number": phone_number,
                    "is_callsign_verified": False,
                }
            )

            # 3. CRITICAL: Check if a login record exists before trying to create one
            # This prevents the UniqueViolation on 'user_login_email_key'
            pre_existing_login = next(login_record for login_record in logins.get_all() if login_record.email == email)
            if not pre_existing_login:
                logins.create(
                    {
                        "email": email,
                        "user_data_id": user.id,
                        "auth_type": "GOOGLE_OAUTH",
                        "password": "",
                        "password_salt": "",
                        "hashing_algorithm_name": "OAUTH",
                        "email_verification_token": str(uuid4()),
                    }
                )

    # Prevents multiple tokens pointing to the same user
    pre_existing_token = next(
        (t for t in tokens.get_all() if t.user_data_id == user.id and (t.expiry > datetime.now())), None
    )

    if pre_existing_token:
        return (pre_existing_token, user)

    # 3. Create auth token
    auth_token = create_auth_token(user.id, AROAuthToken.GOOGLE_OAUTH)

    return (auth_token, user)
