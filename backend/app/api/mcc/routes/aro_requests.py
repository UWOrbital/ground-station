from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.mcc.schemas.responses import ARORequestsResponse
from app.config.data_values import DEFAULT_PAGE_LIMIT, DEFAULT_PAGE_OFFSET, MAX_PAGE_LIMIT
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import ARORequestRepository
from app.mcc_keycloak.client import keycloak

aro_requests_router = APIRouter(tags=["MCC", "ARO Requests"], dependencies=[keycloak.require_admin])

ARORequestsRepo = Annotated[ARORequestRepository, Depends(DAL.get_repo(DAL.aro_requests))]


@aro_requests_router.get("/", name="mcc_list_aro_requests")
async def list_aro_requests(
    aro_requests: ARORequestsRepo,
    limit: int = Query(default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(default=DEFAULT_PAGE_OFFSET, ge=0),
) -> ARORequestsResponse:
    """
    List the most recent ARO picture requests across all ARO users.

    This endpoint backs the MCC AROAdmin page and is restricted to MCC admins.

    :param aro_requests: injected ARORequest repository.
    :param limit: maximum number of most recent requests to return.
    :param offset: number of most recent requests to skip, for paging.
    :return: a page of ARO requests from all users, newest first.
    """
    requests = await aro_requests.get_recent(limit, offset)
    return ARORequestsResponse(data=requests)
