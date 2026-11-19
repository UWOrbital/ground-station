from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.api.mcc.schemas.responses import CurrentSessionResponse, SessionResponse, SessionsResponse
from app.config.data_values import DEFAULT_PAGE_LIMIT, DEFAULT_PAGE_OFFSET, MAX_PAGE_LIMIT
from app.data.enums.transactional import SessionSource, SessionStatus
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import SessionRepository
from app.exceptions import NotFoundError
from app.mcc_keycloak.client import keycloak

sessions_router = APIRouter(tags=["MCC", "Sessions"])

SessionRepo = Annotated[SessionRepository, Depends(DAL.get_repo(DAL.sessions))]


@sessions_router.get("/", dependencies=[keycloak.require_auth])
async def get_sessions(
    sessions: SessionRepo,
    start_after: Annotated[datetime | None, Query()] = None,
    start_before: Annotated[datetime | None, Query()] = None,
    end_after: Annotated[datetime | None, Query()] = None,
    source: Annotated[SessionSource | None, Query()] = None,
    status: Annotated[SessionStatus | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_LIMIT)] = DEFAULT_PAGE_LIMIT,
    offset: Annotated[int, Query(ge=0)] = DEFAULT_PAGE_OFFSET,
) -> SessionsResponse:
    """
    Retrieve sessions, optionally filtered by time range, source, and status

    :param sessions: injected Session repository
    :param start_after: only return sessions starting at or after this time
    :param start_before: only return sessions starting before this time
    :param end_after: only return sessions ending after this time
    :param source: only return sessions with this source (predicted or manual)
    :param status: only return sessions with this status
    :param limit: maximum number of sessions to return
    :param offset: number of sessions to skip
    :return: matching session entries
    """
    items = await sessions.get_in_range(
        start_after, start_before, limit, offset, end_after=end_after, source=source, status=status
    )
    return SessionsResponse(data=items)


@sessions_router.get("/current", dependencies=[keycloak.require_auth])
async def get_current_session(sessions: SessionRepo) -> CurrentSessionResponse:
    """
    Retrieve the session in progress, or the next upcoming session

    :param sessions: injected Session repository
    :return: the current or next session, or null if there is none
    """
    return CurrentSessionResponse(data=await sessions.get_current_or_next())


@sessions_router.get("/{session_id}", dependencies=[keycloak.require_auth])
async def get_session_by_id(session_id: UUID, sessions: SessionRepo) -> CurrentSessionResponse:
    """
    Retrieve a single session by ID

    :param session_id: UUID of the session to retrieve
    :param sessions: injected Session repository
    :return: the matching session
    """
    try:
        session = await sessions.get_by_id(session_id)
    except ValueError as e:
        raise NotFoundError(str(e)) from e
    return SessionResponse(data=session)
