from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.mcc.schemas.responses import TelemetryListResponse
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import TelemetryRepository

telemetry_router = APIRouter(tags=["MCC", "Telemetry"])

TelemetryRepo = Annotated[TelemetryRepository, Depends(DAL.get_repo(DAL.telemetry))]


@telemetry_router.get("/")
async def get_telemetry(
    telemetry_repo: TelemetryRepo,
) -> TelemetryListResponse:
    """
    Retrieves all telemetry.

    :param telemetry_repo: injected Telemetry repository.
    :return: all telemetry entries.
    """
    telemetry = await telemetry_repo.get_all()
    return TelemetryListResponse(data=telemetry)
