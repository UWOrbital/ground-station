from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.v1.aro.auth.aro_session import require_superuser
from app.api.v1.aro.schemas.admin.requests import UserRequest
from app.api.v1.aro.schemas.admin.responses import AllUsersResponse, UserResponse
from app.data.models.aro_user_models import AROUsers
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import (
    AROUserAuthTokenRepository,
    AROUserLoginRepository,
    AROUsersRepository,
)

aro_user_router = APIRouter(tags=["ARO", "User Information"])

AROUsersRepo = Annotated[AROUsersRepository, Depends(DAL.get_repo(DAL.aro_users))]
AROUserAuthTokensRepo = Annotated[AROUserAuthTokenRepository, Depends(DAL.get_repo(DAL.aro_user_auth_tokens))]
AROUserLoginsRepo = Annotated[AROUserLoginRepository, Depends(DAL.get_repo(DAL.aro_user_logins))]


@aro_user_router.get("/get_all_users", response_model=AllUsersResponse)
async def get_all_users(aro_users: AROUsersRepo, user: AROUsers = Depends(require_superuser)) -> AllUsersResponse:
    """
    Gets all users

    :param aro_users: injected AROUsers repository.
    :param user: the authenticated superuser (injected).
    :return: all users
    """
    users = await aro_users.get_all()
    return AllUsersResponse(data=users)


@aro_user_router.get("/get_user/{userid}", response_model=UserResponse)
async def get_user(userid: str, aro_users: AROUsersRepo, user: AROUsers = Depends(require_superuser)) -> UserResponse:
    """
    Gets a user by ID

    :param userid: The unique identifier of the user
    :param aro_users: injected AROUsers repository.
    :param user: the authenticated superuser (injected).
    :return: the user
    """
    found = await aro_users.get_by_id(UUID(userid))
    return UserResponse(data=found)


@aro_user_router.post("/create_user", response_model=UserResponse)
async def create_user(
    payload: UserRequest, aro_users: AROUsersRepo, user: AROUsers = Depends(require_superuser)
) -> UserResponse:
    """
    Creates a user with the given payload

    :param payload: The data used to create a user
    :param aro_users: injected AROUsers repository.
    :param user: the authenticated superuser (injected).
    :return: returns the user created
    """
    created = await aro_users.create(
        data={
            "call_sign": payload.call_sign,
            "email": payload.email,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "phone_number": payload.phone_number,
        }
    )

    return UserResponse(data=created)


@aro_user_router.delete("/delete_user/{userid}", response_model=UserResponse)
async def delete_user(
    userid: str,
    aro_users: AROUsersRepo,
    aro_user_auth_tokens: AROUserAuthTokensRepo,
    aro_user_logins: AROUserLoginsRepo,
    user: AROUsers = Depends(require_superuser),
) -> UserResponse:
    """
    Deletes a user based on the user ID

    :param userid: The unique identifier of the user to be deleted
    :param aro_users: injected AROUsers repository.
    :param aro_user_auth_tokens: injected AROUserAuthToken repository.
    :param aro_user_logins: injected AROUserLogin repository.
    :param user: the authenticated superuser (injected).
    :return: returns the deleted users
    """
    user_id = UUID(userid)

    # While `userId` is an FK, it's not `ON DELETE CASCADE`
    await aro_user_auth_tokens.delete_all_by_user_id(user_id)
    await aro_user_logins.delete_all_by_user_id(user_id)

    deleted_user = await aro_users.delete_by_id(user_id)

    return UserResponse(data=deleted_user)
