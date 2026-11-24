from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.health import router


@pytest.fixture
def health_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


async def test_health_liveness_returns_healthy(health_app: FastAPI) -> None:
    async with AsyncClient(
        transport=ASGITransport(app=health_app), base_url="http://test"
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


async def test_health_ready_returns_200_when_all_dependencies_healthy(
    health_app: FastAPI,
) -> None:
    with (
        patch("app.api.health.check_database", new=AsyncMock(return_value=True)),
        patch("app.api.health.check_keycloak", new=AsyncMock(return_value=True)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=health_app), base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "database": "healthy",
        "keycloak": "healthy",
    }


async def test_health_ready_returns_503_when_database_unhealthy(
    health_app: FastAPI,
) -> None:
    with (
        patch("app.api.health.check_database", new=AsyncMock(return_value=False)),
        patch("app.api.health.check_keycloak", new=AsyncMock(return_value=True)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=health_app), base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "database": "unhealthy",
        "keycloak": "healthy",
    }


async def test_health_ready_returns_503_when_keycloak_unhealthy(
    health_app: FastAPI,
) -> None:
    with (
        patch("app.api.health.check_database", new=AsyncMock(return_value=True)),
        patch("app.api.health.check_keycloak", new=AsyncMock(return_value=False)),
    ):
        async with AsyncClient(
            transport=ASGITransport(app=health_app), base_url="http://test"
        ) as client:
            response = await client.get("/health/ready")

    assert response.status_code == 503
    assert response.json() == {
        "status": "unhealthy",
        "database": "healthy",
        "keycloak": "unhealthy",
    }
