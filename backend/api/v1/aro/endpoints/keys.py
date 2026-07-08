from data.data_wrappers.wrappers import AROUserKeyWrapper
from data.tables.aro_user_tables import AROUsers
from fastapi import APIRouter, Depends, HTTPException, status

from api.v1.aro.auth.dependencies import get_current_user
from api.v1.aro.models.auth_requests import GenerateKeyRequest, SyncKeysRequest
from api.v1.aro.models.auth_responses import (
    CurrentKeyResponse,
    GenerateKeyResponse,
    GetAllKeysResponse,
    SyncKeysResponse,
)

aro_keys_router = APIRouter(tags=["ARO", "Keys"])


@aro_keys_router.post("/generate")
async def generate_key(
    payload: GenerateKeyRequest,
    user: AROUsers = Depends(get_current_user),
) -> GenerateKeyResponse:
    """
    Generate a new ARO key for the authenticated user.

    :param payload: Request body with optional key name
    :param user: Authenticated user, resolved from auth token
    :return: Newly created key
    """
    user_keys = AROUserKeyWrapper()

    return GenerateKeyResponse(data=user_keys.generate(user_id=user.id, name=payload.name))


@aro_keys_router.post("/current")
async def current_key(
    user: AROUsers = Depends(get_current_user),
) -> CurrentKeyResponse:
    """Get the current ARO key"""
    user_keys = AROUserKeyWrapper()

    return CurrentKeyResponse(data=user_keys.get_active(user_id=user.id))


@aro_keys_router.post("/all")
async def get_all_keys(
    user: AROUsers = Depends(get_current_user),
) -> GetAllKeysResponse:
    """
    Get all ARO keys for the authenticated user.

    :param user: Authenticated user, resolved from auth token
    :return: List of the user's keys
    """
    user_keys = AROUserKeyWrapper()

    return GetAllKeysResponse(
        data=user_keys.get_all_by(user_id=user.id),
    )


@aro_keys_router.post("/sync")
async def sync_keys(
    payload: SyncKeysRequest,
    user: AROUsers = Depends(get_current_user),
) -> SyncKeysResponse:
    """
    Mark an ARO key as synced to the OBC.

    Verifies the key belongs to the authenticated user before syncing.

    :param payload: Request body with the key UUID
    :param user: Authenticated user, resolved from auth token
    :return: Confirmation of the synced key
    """
    user_keys = AROUserKeyWrapper()

    # Verify the key belongs to the authenticated user
    keys = user_keys.get_all_by(user_id=user.id, id=payload.key_id)
    if not keys:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Key {payload.key_id} not found or does not belong to you.",
        )

    try:
        synced = user_keys.mark_synced(key_id=payload.key_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return SyncKeysResponse(
        message="Key synced successfully",
        key_id=synced.id,
    )
