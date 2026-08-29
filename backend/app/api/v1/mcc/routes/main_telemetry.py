from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.exceptions import HTTPException

from app.api.v1.mcc.schemas.responses import MainTelemetriesResponse, MainTelemetryResponse
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import MainTelemetryRepository
from app.mcc_keycloak.client import keycloak

main_telemetry_router = APIRouter(tags=["MCC", "Main Telemetry"])

MainTelemetryRepo = Annotated[MainTelemetryRepository, Depends(DAL.get_repo(DAL.main_telemetries))]


@main_telemetry_router.get("/", dependencies=[keycloak.require_auth])
async def get_all_telemetries(
    main_telemetries: MainTelemetryRepo,
) -> MainTelemetriesResponse:
    """
    Gets the main telemetries that are available

    :param main_telemetries: injected MainTelemetry repository.
    :return: list of all telemetries
    """
    items = await main_telemetries.get_all()
    return MainTelemetriesResponse(data=items)


@main_telemetry_router.get("/{telemetry_id}", dependencies=[keycloak.require_auth])
async def get_telemetry_by_id(
    telemetry_id: int,
    main_telemetries: MainTelemetryRepo,
) -> MainTelemetryResponse:
    """
    Gets the main telemetry by the id provided

    :param telemetry_id: the ID of the telemetry to retrieve.
    :param main_telemetries: injected MainTelemetry repository.
    :return: the matching telemetry.
    """
    try:
        telemetry = await main_telemetries.get_by_id(telemetry_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail="Telemetry not found") from e
    return MainTelemetryResponse(data=telemetry)
