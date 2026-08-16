from uuid import UUID

from fastapi import APIRouter

from app.api.v1.aro.schemas.admin.requests import UserRequest
from app.api.v1.aro.schemas.admin.responses import AllUsersResponse, UserResponse
from app.data.data_wrappers.wrappers import AROUserAuthTokenWrapper, AROUserLoginWrapper, AROUsersWrapper

aro_user_router = APIRouter(tags=["ARO", "User Information"])
users_wrapper = AROUsersWrapper()


@aro_user_router.get("/get_all_users", response_model=AllUsersResponse)
async def get_all_users() -> AllUsersResponse:
    """
    Gets all users

    :return: all users
    """
    users = users_wrapper.get_all()
    return AllUsersResponse(data=users)


@aro_user_router.get("/get_user/{userid}", response_model=UserResponse)
def get_user(userid: str) -> UserResponse:
    """
    Gets a user by ID

    :param userid: The unique identifier of the user
    :return: the user
    """
    user = users_wrapper.get_by_id(UUID(userid))
    return UserResponse(data=user)


@aro_user_router.post("/create_user", response_model=UserResponse)
def create_user(payload: UserRequest) -> UserResponse:
    """
    Creates a user with the given payload
    :param payload: The data used to create a user
    :return: returns the user created
    """

    user = users_wrapper.create(
        data={
            "call_sign": payload.call_sign,
            "email": payload.email,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "phone_number": payload.phone_number,
        }
    )

    return UserResponse(data=user)


@aro_user_router.delete("/delete_user/{userid}", response_model=UserResponse)
def delete_user(userid: str) -> UserResponse:
    """
    Deletes a user based on the user ID
    :param userid: The unique identifier of the user to be deleted
    :return: returns the deleted users
    """
    user_id = UUID(userid)

    # While `userId` is an FK, it's not `ON DELETE CASCADE`
    AROUserAuthTokenWrapper().delete_all_by_user_id(user_id)
    AROUserLoginWrapper().delete_all_by_user_id(user_id)

    deleted_user = users_wrapper.delete_by_id(user_id)

    return UserResponse(data=deleted_user)
