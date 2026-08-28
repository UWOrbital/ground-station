from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.v1.mcc.schemas.responses import TelemetryListResponse
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import TelemetryRepository

telemetry_router = APIRouter(tags=["MCC", "Telemetry"])


@telemetry_router.get("/")
async def get_telemetry(
    telemetry_repo: Annotated[TelemetryRepository, Depends(DAL.get_repo(DAL.telemetry))],
) -> TelemetryListResponse:
    """
    Retrieves all telemetry.

    :param telemetry_repo: injected Telemetry repository.
    :return: all telemetry entries.
    """
    telemetry = await telemetry_repo.get_all()
    return TelemetryListResponse(data=telemetry)
