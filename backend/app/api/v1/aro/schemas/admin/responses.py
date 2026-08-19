from pydantic import BaseModel

from app.data.models.aro_user_models import AROUsers

# -----------------------------------------------------------------
# Admin Responses
# -----------------------------------------------------------------


class AllUsersResponse(BaseModel):
    """
    The users response model.
    """

    data: list[AROUsers]


class UserResponse(BaseModel):
    """
    Single user response model.
    """

    data: AROUsers
