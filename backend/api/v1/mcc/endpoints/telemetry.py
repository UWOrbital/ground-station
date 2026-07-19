from fastapi import APIRouter

from backend.api.v1.mcc.models.responses import TelemetryListResponse
from backend.data.data_wrappers.wrappers import TelemetryWrapper

telemetry_router = APIRouter(tags=["MCC", "Telemetry"])


@telemetry_router.get("/")
async def get_telemetry() -> TelemetryListResponse:
    """
    Retrieves all telemetry.
    """
    telemetry = TelemetryWrapper().get_all()
    return TelemetryListResponse(data=telemetry)
