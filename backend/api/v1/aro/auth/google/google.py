from api.v1.aro.auth.services.tokens import create_auth_token, create_oauth_user
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

    # Prefer matching on google_id
    user = users.get_user_by_google_id(request.google_id)

    if not user:
        user = users.get_user_by_email(request.email)

        # Link the existing account to this Google identity
        user = (
            users.update(
                user.id,
                {"google_id": request.google_id},
            )
            if user
            else create_oauth_user(request)
        )

    auth_token = create_auth_token(user.id, AROAuthToken.GOOGLE_OAUTH)

    return (auth_token, user)
