from typing import Any

from data.data_wrappers.wrappers import MCCUsersWrapper
from data.tables.mcc_user_tables import MCCUsers
from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException
from mcc_keycloak.client import keycloak

mcc_users_router = APIRouter(tags=["MCC", "Users"], dependencies=[keycloak.require_auth])


@mcc_users_router.get("/me")
def get_me(user: MCCUsers = Depends(keycloak.get_current_user)) -> dict:
    """
    Login endpoint for redirecting to keycloak's login/registration page
    """
    return {
        "id": str(user.id),
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "phone_number": user.phone_number,
    }


@mcc_users_router.patch("/me")
def update_me(data: dict[str, Any], user: MCCUsers = Depends(keycloak.get_current_user)) -> dict:
    """
    Callback endpoint redirected to by keycloak for tokens
    """
    try:
        MCCUsersWrapper().update(user.id, data)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found or field unavailable")
    except TypeError:
        raise HTTPException(status_code=422, detail="Field type mismatch")
    except RuntimeError:
        raise HTTPException(status_code=500, detail="Failed to update user")

    return get_me(user)


@mcc_users_router.delete("/me")
def delete_me(user: MCCUsers = Depends(keycloak.get_current_user)) -> dict[str, str]:
    """
    Endpoint for deleting user from .
    """
    try:
        MCCUsersWrapper().delete_by_id(user.id)
    except ValueError:
        raise HTTPException(status_code=404, detail="User not found")

    return {"status": "success"}
