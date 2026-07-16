from data.data_wrappers.wrappers import CommsSessionWrapper
from fastapi import APIRouter
from mcc_keycloak.client import keycloak

from api.v1.mcc.models.responses import CommsSessionsResponse

comms_sessions_router = APIRouter(tags=["MCC", "Sessions"])


@comms_sessions_router.get("/", dependencies=[keycloak.require_auth])
async def get_all_comms_sessions() -> CommsSessionsResponse:
    """
    Retrieve all sessions.

    :return: The list of all sessions.
    """
    items = CommsSessionWrapper().get_all()
    return CommsSessionsResponse(data=items)
