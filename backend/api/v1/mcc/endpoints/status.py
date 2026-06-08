from datetime import datetime

from data.data_wrappers.wrappers import CommsSessionWrapper, TelemetryWrapper
from data.enums.transactional import SessionStatus
from fastapi import APIRouter

from api.v1.mcc.models.responses import SatelliteStatusResponse, TelemetryDataResponse

status_router = APIRouter(tags=["MCC", "Status"])

# TODO : Expand the states of the backend to have a status of pending,
# scheduled and completed instead of idle
STATUS_MAP = {
    SessionStatus.ONGOING: "online",
    SessionStatus.COMPLETED: "idle",
    SessionStatus.PENDING: "idle",
    SessionStatus.SCHEDULED: "idle",
}

# NOTE : This is fragile and might change with the change of IDS in the spreadsheet referenced below
TELEMETRY_IDS = {
    1: "CSP Packets Received",
    3: "OBC Temperature",
    6: "EPS Temperature",
    11: "Comms 5V Current",
    17: "Comms 5V Voltage",
}


@status_router.get("/status")
async def get_satellite_status() -> SatelliteStatusResponse:
    """

    Get the current satellite connection status and telemetry snapshot

    this endpoint references the telemetry IDs of the sensors in this spreadsheet : https://docs.google.com/spreadsheets/d/1XWXgp3--NHZ4XlxOyBYPS-M_LOU_ai-I6TcvotKhR1s/edit?gid=0#gid=0

    :return: SatelliteStatusResponse with status, last contact, session duration, and telemetry data
    """

    session = CommsSessionWrapper().get_most_recent_session()

    if session is None:
        return SatelliteStatusResponse(
            status="offline",
            last_contact="Never",
            session_duration="--",
            telemetry_data=[],
        )

    frontend_status = STATUS_MAP.get(session.status, "error")

    now = datetime.now()
    contact_time = session.end_time if session.end_time is not None else session.start_time
    diff = now - contact_time
    minutes = int(diff.total_seconds() / 60)

    end_or_now = session.end_time if session.end_time is not None else now
    duration = end_or_now - session.start_time
    minutes_duration = int(duration.total_seconds() / 60)

    telemetry_data = []
    for telemetry_id, label in TELEMETRY_IDS.items():
        result = TelemetryWrapper().get_most_recent_by_type(telemetry_id)
        if result is not None:
            telemetry_data.append(
                TelemetryDataResponse(
                    label=label,
                    value=result.value if result.value is not None else "N/A",
                )
            )

    satellite_response = SatelliteStatusResponse(
        status=frontend_status,
        last_contact="Less than a minute ago" if minutes == 0 else f"{minutes} min ago",
        session_duration=f"{minutes_duration} min",
        telemetry_data=telemetry_data,
    )

    return satellite_response
