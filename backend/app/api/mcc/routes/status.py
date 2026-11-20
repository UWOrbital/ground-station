from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.mcc.schemas.responses import SatelliteStatusResponse, TelemetryDataResponse
from app.data.enums.transactional import SessionStatus
from app.data.repositories.dal import DAL
from app.data.repositories.repositories import SessionRepository, TelemetryRepository

status_router = APIRouter(tags=["MCC", "Status"])

SessionRepo = Annotated[SessionRepository, Depends(DAL.get_repo(DAL.sessions))]
TelemetryRepo = Annotated[TelemetryRepository, Depends(DAL.get_repo(DAL.telemetry))]

# TODO : Expand the states of the backend to have a status of pending,
# scheduled and completed instead of idle
STATUS_MAP = {
    SessionStatus.ONGOING: "online",
    SessionStatus.COMPLETED: "idle",
    SessionStatus.PENDING: "idle",
    SessionStatus.SCHEDULED: "idle",
}

# Shown when there is no session in progress to report a value from
NOT_AVAILABLE = "--"

# NOTE : This is fragile and might change with the change of IDS in the spreadsheet referenced below
TELEMETRY_IDS = {
    1: "CSP Packets Received",
    3: "OBC Temperature",
    6: "EPS Temperature",
    11: "Comms 5V Current",
    17: "Comms 5V Voltage",
}


@status_router.get("/status")
async def get_satellite_status(
    sessions: SessionRepo,
    telemetry_repo: TelemetryRepo,
) -> SatelliteStatusResponse:
    """

    Get the current satellite connection status and telemetry snapshot

    this endpoint references the telemetry IDs of the sensors in this spreadsheet : https://docs.google.com/spreadsheets/d/1XWXgp3--NHZ4XlxOyBYPS-M_LOU_ai-I6TcvotKhR1s/edit?gid=0#gid=0

    Status comes from the session in progress, or else the next upcoming one.
    While a session is in progress, the duration is the time elapsed so far.
    Before the next session starts, the last contact and session_duration appear as "--".

    :param sessions: injected Session repository.
    :param telemetry_repo: injected Telemetry repository.
    :return: SatelliteStatusResponse with status, last contact, session duration, and telemetry data
    """
    now = datetime.now(UTC)
    session = await sessions.get_current_or_next(now)

    if session is None:
        return SatelliteStatusResponse(
            status="offline",
            last_contact=NOT_AVAILABLE,
            session_duration=NOT_AVAILABLE,
            telemetry_data=[],
        )

    frontend_status = STATUS_MAP.get(session.status, "error")

    if session.start_time <= now:
        elapsed_minutes = int((now - session.start_time).total_seconds() // 60)
        last_contact = "Now"
        session_duration = "Less than a minute" if elapsed_minutes == 0 else f"{elapsed_minutes} min"
    else:
        last_contact = NOT_AVAILABLE
        session_duration = NOT_AVAILABLE

    telemetry_data = []
    for telemetry_id, label in TELEMETRY_IDS.items():
        result = await telemetry_repo.get_most_recent_by_type(telemetry_id)
        if result is not None:
            telemetry_data.append(
                TelemetryDataResponse(
                    label=label,
                    value=result.value if result.value is not None else "N/A",
                )
            )

    satellite_response = SatelliteStatusResponse(
        status=frontend_status,
        last_contact=last_contact,
        session_duration=session_duration,
        telemetry_data=telemetry_data,
    )

    return satellite_response
