from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import jwt
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app.api.aro.auth.aro_session import get_user_by_token
from app.api.aro.routes.auth import router
from app.config.env_settings.backend_config import settings
from app.data.models.aro_user_models import AROUsers
from app.data.repositories.dal import DAL


def make_user(*, is_active: bool = True) -> AROUsers:
    return AROUsers(
        email="callable@test.com",
        first_name="Auth",
        is_active=is_active,
    )


def make_access_token(user_id: object, *, expires_at: datetime | None = None) -> str:
    payload = {
        "sub": user_id,
        "exp": expires_at or datetime.now(UTC) + timedelta(minutes=10),
    }
    return jwt.encode(payload, settings.auth.jwt_secret, algorithm="HS256")


@pytest.fixture
def auth_app() -> tuple[FastAPI, AsyncMock]:
    app = FastAPI()
    app.include_router(router, prefix="/api/aro")

    repo = AsyncMock()
    app.dependency_overrides[DAL.get_repo(DAL.aro_users)] = lambda: repo
    return app, repo


async def test_ping_returns_authenticated_for_valid_token(
    auth_app: tuple[FastAPI, AsyncMock],
) -> None:
    app, repo = auth_app
    user = make_user()
    repo.get_by_id.return_value = user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/aro/auth/ping",
            headers={"Authorization": f"Bearer {make_access_token(str(user.id))}"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "authenticated"}
    repo.get_by_id.assert_awaited_once_with(user.id)


async def test_ping_rejects_missing_token(auth_app: tuple[FastAPI, AsyncMock]) -> None:
    app, repo = auth_app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/aro/auth/ping")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "missing_token"
    repo.get_by_id.assert_not_awaited()


@pytest.mark.parametrize(
    ("payload", "expected_code"),
    [
        ({"sub": str(uuid4())}, "invalid_token"),
        (
            {"sub": 123, "exp": datetime.now(UTC) + timedelta(minutes=10)},
            "invalid_token",
        ),
        (
            {"sub": str(uuid4()), "exp": datetime.now(UTC) - timedelta(seconds=1)},
            "access_token_expired",
        ),
    ],
)
async def test_ping_rejects_invalid_claims(
    auth_app: tuple[FastAPI, AsyncMock], payload: dict[str, object], expected_code: str
) -> None:
    app, repo = auth_app
    token = jwt.encode(payload, settings.auth.jwt_secret, algorithm="HS256")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/aro/auth/ping",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == expected_code
    repo.get_by_id.assert_not_awaited()


async def test_ping_rejects_unknown_user(auth_app: tuple[FastAPI, AsyncMock]) -> None:
    app, repo = auth_app
    user_id = uuid4()
    repo.get_by_id.side_effect = ValueError("not found")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/aro/auth/ping",
            headers={"Authorization": f"Bearer {make_access_token(str(user_id))}"},
        )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_token"


async def test_ping_rejects_inactive_user(auth_app: tuple[FastAPI, AsyncMock]) -> None:
    app, repo = auth_app
    user = make_user(is_active=False)
    repo.get_by_id.return_value = user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/aro/auth/ping",
            headers={"Authorization": f"Bearer {make_access_token(str(user.id))}"},
        )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "inactive_user"
