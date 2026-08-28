from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.v1.mcc.schemas.responses import CommsSessionsResponse
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import CommsSessionRepository
from app.mcc_keycloak.client import keycloak

comms_sessions_router = APIRouter(tags=["MCC", "Sessions"])


@comms_sessions_router.get("/", dependencies=[keycloak.require_auth])
async def get_comms_sessions(
    comms_sessions: Annotated[CommsSessionRepository, Depends(DAL.get_repo(DAL.comms_sessions))],
    start_after: Annotated[datetime | None, Query()] = None,
    start_before: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> CommsSessionsResponse:
    """
    Retrieve sessions, optionally filtered to a start_time range

    :param comms_sessions: injected CommsSession repository.
    :param start_after: only return sessions starting at or after this time
    :param start_before: only return sessions starting before this time
    :param limit: maximum number of sessions to return (1-500, default 100)
    :return: matching session entries
    """
    items = await comms_sessions.get_in_range(start_after, start_before, limit)
    return CommsSessionsResponse(data=items)
