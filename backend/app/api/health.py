import asyncio
from enum import StrEnum

from fastapi import APIRouter, Response, status
from fastapi.concurrency import run_in_threadpool
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import text

from app.data.database.engine import get_db_engine
from app.mcc_keycloak.client import keycloak

router = APIRouter(tags=["health"])

HEALTH_CHECK_TIMEOUT_SECONDS = 3.0


class HealthStatus(StrEnum):
    """Health state reported for the service and its dependencies."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Response model for the infrastructure health check endpoint."""

    status: HealthStatus
    database: HealthStatus
    keycloak: HealthStatus


async def check_database() -> bool:
    """Verify PostgreSQL connectivity by executing a lightweight query."""
    try:

        async def _ping() -> None:
            engine = get_db_engine()
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))

        await asyncio.wait_for(_ping(), timeout=HEALTH_CHECK_TIMEOUT_SECONDS)
        return True
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc!r}")
        return False


async def check_keycloak() -> bool:
    """Verify Keycloak connectivity by fetching its OpenID well-known config."""
    try:
        await asyncio.wait_for(
            run_in_threadpool(lambda: keycloak.internal_client.well_known()),
            timeout=HEALTH_CHECK_TIMEOUT_SECONDS,
        )
        return True
    except Exception as exc:
        logger.warning(f"Keycloak health check failed: {exc!r}")
        return False


@router.get("/health")
async def health_check() -> dict[str, HealthStatus]:
    """Liveness check endpoint confirming the API process is running."""
    return {"status": HealthStatus.HEALTHY}


@router.get("/health/ready", response_model=HealthResponse)
async def readiness_check(response: Response) -> HealthResponse:
    """Readiness check endpoint verifying database and Keycloak connectivity."""
    db_ok = await check_database()
    keycloak_ok = await check_keycloak()

    is_ready = db_ok and keycloak_ok
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=HealthStatus.HEALTHY if is_ready else HealthStatus.UNHEALTHY,
        database=HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY,
        keycloak=HealthStatus.HEALTHY if keycloak_ok else HealthStatus.UNHEALTHY,
    )
