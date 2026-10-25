from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.mcc.schemas.responses import TelemetryListResponse
from app.config.data_values import DEFAULT_PAGE_LIMIT, DEFAULT_PAGE_OFFSET, MAX_PAGE_LIMIT
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import TelemetryRepository

telemetry_router = APIRouter(tags=["MCC", "Telemetry"])

TelemetryRepo = Annotated[TelemetryRepository, Depends(DAL.get_repo(DAL.telemetry))]


@telemetry_router.get("/")
async def get_telemetry(
    telemetry_repo: TelemetryRepo,
    limit: int = Query(default=DEFAULT_PAGE_LIMIT, ge=1, le=MAX_PAGE_LIMIT),
    offset: int = Query(default=DEFAULT_PAGE_OFFSET, ge=0),
) -> TelemetryListResponse:
    """
    Retrieves all telemetry.

    :param telemetry_repo: injected Telemetry repository.
    :param limit: max rows to return
    :param offset: number of rows to skip
    :return: all telemetry entries.
    """
    telemetry = await telemetry_repo.get_all(limit=limit, offset=offset)
    return TelemetryListResponse(data=telemetry)
