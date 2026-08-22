from fastapi import APIRouter

from app.api.v1.mcc.schemas.responses import TelemetryListResponse
from app.data.data_wrappers.wrappers import TelemetryWrapper

telemetry_router = APIRouter(tags=["MCC", "Telemetry"])


@telemetry_router.get("/")
async def get_telemetry() -> TelemetryListResponse:
    """
    Retrieves all telemetry.
    """
    telemetry = await TelemetryWrapper().get_all()
    return TelemetryListResponse(data=telemetry)
