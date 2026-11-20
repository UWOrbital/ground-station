from fastapi import APIRouter, Response, status
from fastapi.concurrency import run_in_threadpool
from loguru import logger
from sqlalchemy import text

from app.api.schemas.health import HealthResponse, HealthStatus
from app.data.database.engine import get_db_engine
from app.mcc_keycloak.client import keycloak

router = APIRouter(tags=["health"])


async def check_database() -> bool:
    """Verify PostgreSQL connectivity by executing a lightweight query."""
    try:
        engine = get_db_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc!r}")
        return False


async def check_keycloak() -> bool:
    """Verify Keycloak connectivity by fetching its OpenID well-known config."""
    try:
        await run_in_threadpool(lambda: keycloak.internal_client.well_known())
        return True
    except Exception as exc:
        logger.warning(f"Keycloak health check failed: {exc!r}")
        return False


@router.get("/health", response_model=HealthResponse)
async def health_check(response: Response) -> HealthResponse:
    """Infrastructure health check endpoint."""
    db_ok = await check_database()
    keycloak_ok = await check_keycloak()

    is_healthy = db_ok and keycloak_ok
    if not is_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status=HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY,
        database=HealthStatus.HEALTHY if db_ok else HealthStatus.UNHEALTHY,
        keycloak=HealthStatus.HEALTHY if keycloak_ok else HealthStatus.UNHEALTHY,
    )
