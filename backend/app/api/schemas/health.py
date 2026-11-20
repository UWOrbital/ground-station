from enum import StrEnum

from pydantic import BaseModel


class HealthStatus(StrEnum):
    """Health state reported for the service and its dependencies."""

    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"


class HealthResponse(BaseModel):
    """Response model for the infrastructure health check endpoint."""

    status: HealthStatus
    database: HealthStatus
    keycloak: HealthStatus
