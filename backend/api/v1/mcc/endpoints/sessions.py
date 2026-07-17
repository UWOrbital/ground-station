from datetime import datetime
from typing import Annotated

from data.data_wrappers.wrappers import CommsSessionWrapper
from fastapi import APIRouter, Query
from mcc_keycloak.client import keycloak

from api.v1.mcc.models.responses import CommsSessionsResponse

comms_sessions_router = APIRouter(tags=["MCC", "Sessions"])


@comms_sessions_router.get("/", dependencies=[keycloak.require_auth])
async def get_comms_sessions(
    start_after: Annotated[datetime | None, Query()] = None,
    start_before: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> CommsSessionsResponse:
    """
    Retrieve sessions, optionally filtered to a start_time range

    :param start_after: only return sessions starting at or after this time
    :param start_before: only return sessions starting before this time
    :param limit: maximum number of sessions to return (1-500, default 100)
    :return: matching session entries
    """
    items = CommsSessionWrapper().get_in_range(start_after, start_before, limit)
    return CommsSessionsResponse(data=items)
