from app.api.v1.mcc.schemas.responses import MainTelemetriesResponse, MainTelemetryResponse
from fastapi import APIRouter
from fastapi.exceptions import HTTPException

from app.data.data_wrappers.wrappers import MainTelemetryWrapper
from app.mcc_keycloak.client import keycloak

main_telemetry_router = APIRouter(tags=["MCC", "Main Telemetry"])


@main_telemetry_router.get("/", dependencies=[keycloak.require_auth])
async def get_all_telemetries() -> MainTelemetriesResponse:
    """
    Gets the main telemetries that are available

    :return: list of all telemetries
    """
    items = MainTelemetryWrapper().get_all()
    return MainTelemetriesResponse(data=items)


@main_telemetry_router.get("/{telemetry_id}", dependencies=[keycloak.require_auth])
async def get_telemetry_by_id(telemetry_id: int) -> MainTelemetryResponse:
    """
    Gets the main telemetry by the id provided

    :param telemetry_id: the ID of the telemetry to retrieve.
    :return: the matching telemetry.
    """
    try:
        telemetry = MainTelemetryWrapper().get_by_id(telemetry_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Telemetry not found") from e
    return MainTelemetryResponse(data=telemetry)
