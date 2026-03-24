from api.v1.aro.endpoints.auth.services.tokens import create_auth_token
from api.v1.aro.models.auth_requests import GoogleRequest
from data.data_wrappers.wrappers import AROUsersWrapper
from data.enums.aro_auth_token import AROAuthToken
from data.tables.aro_user_tables import AROUserAuthToken, AROUsers


def google_auth(request: GoogleRequest) -> tuple[AROUserAuthToken, AROUsers]:
    """
    Authenticate a user via Google OAuth, creating a new account if necessary.

    :request GoogleRequest
    :returns [AROUserAuthToken, AROUsers]
    """
    users = AROUsersWrapper()
    all_users = users.get_all()

    # Prefer matching on google_id
    user = next((u for u in all_users if (u.google_id == request.google_id)), None)

    if not user:
        user = next((u for u in all_users if (u.email == request.email)), None)

        if user:
            # Link the existing account to this Google identity
            user = users.update(user.id, {"google_id": request.google_id})
        else:
            user = users.create(
                {
                    "email": request.email,
                    "first_name": request.first_name,
                    "last_name": request.last_name,
                    "google_id": request.google_id,
                    "phone_number": request.phone_number,
                    "is_callsign_verified": False,
                }
            )

    auth_token = create_auth_token(user.id, AROAuthToken.GOOGLE_OAUTH)

    return (auth_token, user)
