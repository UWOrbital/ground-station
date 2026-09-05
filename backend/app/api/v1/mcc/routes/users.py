from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from app.api.v1.mcc.schemas.requests import UpdateUserRequest
from app.api.v1.mcc.schemas.responses import UserInformationResponse
from app.data.data_wrappers.wrappers import MCCUsersWrapper
from app.data.models.mcc_user_models import MCCUsers
from app.mcc_keycloak.client import keycloak

mcc_users_router = APIRouter(tags=["MCC", "Users"], dependencies=[keycloak.require_auth])


@mcc_users_router.get("/me")
async def get_me(user: MCCUsers = Depends(keycloak.get_current_user)) -> UserInformationResponse:
    """
    Login endpoint for redirecting to keycloak's login/registration page
    """
    return UserInformationResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=user.phone_number,
        admin_request_status=user.admin_request_status,
    )


@mcc_users_router.patch("/me")
async def update_me(
    request: UpdateUserRequest, user: MCCUsers = Depends(keycloak.get_current_user)
) -> UserInformationResponse:
    """
    Callback endpoint redirected to by keycloak for tokens
    """

    data = {
        "email": request.email,
        "first_name": request.first_name,
        "last_name": request.last_name,
        "phone_number": request.phone_number,
    }

    try:
        await MCCUsersWrapper().update(user.id, data)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="User not found or field unavailable") from e
    except TypeError as e:
        raise HTTPException(status_code=422, detail="Field type mismatch") from e
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail="Failed to update user") from e

    await keycloak.sync_user_changes(user.id, data)

    return await get_me(user)


@mcc_users_router.delete("/me")
async def delete_me(user: MCCUsers = Depends(keycloak.get_current_user)) -> dict[str, str]:
    """
    Endpoint for deleting user from keycloak service in use.
    """
    try:
        await MCCUsersWrapper().delete_by_id(user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="User not found") from e

    await keycloak.sync_user_deletion(user.id)
    return {"status": "success"}
