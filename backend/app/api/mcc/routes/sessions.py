from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.mcc.schemas.responses import SessionsResponse
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import SessionRepository
from app.mcc_keycloak.client import keycloak

sessions_router = APIRouter(tags=["MCC", "Sessions"])

SessionRepo = Annotated[SessionRepository, Depends(DAL.get_repo(DAL.sessions))]


@sessions_router.get("/", dependencies=[keycloak.require_auth])
async def get_sessions(
    sessions: SessionRepo,
    start_after: Annotated[datetime | None, Query()] = None,
    start_before: Annotated[datetime | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> SessionsResponse:
    """
    Retrieve sessions, optionally filtered to a start_time range

    :param sessions: injected Session repository.
    :param start_after: only return sessions starting at or after this time
    :param start_before: only return sessions starting before this time
    :param limit: maximum number of sessions to return (1-500, default 100)
    :return: matching session entries
    """
    items = await sessions.get_in_range(start_after, start_before, limit)
    return SessionsResponse(data=items)
