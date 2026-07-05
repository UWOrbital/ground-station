from fastapi import APIRouter

from api.v1.aro.models.auth_requests import GenerateKeyRequest, SyncKeysRequest
from api.v1.aro.models.auth_responses import (
    CurrentKeyResponse,
    GenerateKeyResponse,
    GetAllKeysResponse,
    SyncKeysResponse,
)

picture_requests_router = APIRouter(tags=["ARO", "Keys"])


@picture_requests_router.post("/generate")
async def generate_key(payload: GenerateKeyRequest) -> GenerateKeyResponse:
    """Generate a new ARO key"""
    # TODO: get user_id from authenticated session once auth middleware is wired
    raise NotImplementedError


@picture_requests_router.post("/current")
async def current_key() -> CurrentKeyResponse:
    """Get the current ARO key"""
    raise NotImplementedError


@picture_requests_router.post("/all")
async def get_all_keys() -> GetAllKeysResponse:
    """Get all ARO keys"""
    raise NotImplementedError


@picture_requests_router.post("/sync")
async def sync_keys(payload: SyncKeysRequest) -> SyncKeysResponse:
    """Sync ARO keys"""
    raise NotImplementedError
