from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock
from uuid import uuid4

import jwt
import pytest
from fastapi import FastAPI, HTTPException
from httpx import ASGITransport, AsyncClient
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.aro.auth.aro_session import (
    get_user_by_token,
    issue_refresh_token,
    rotate_refresh_token,
)
from app.api.aro.routes.auth import router
from app.config.env_settings.backend_config import settings
from app.data.models.aro_user_models import AROUserAuthToken, AROUsers
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
    repo.get_by_id.assert_not_awaited()


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


async def test_get_current_user_rejects_unknown_user(
    auth_app: tuple[FastAPI, AsyncMock],
) -> None:
    app, repo = auth_app
    user_id = uuid4()
    repo.get_by_id.side_effect = ValueError("not found")

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/aro/auth/get_current_user",
            headers={"Authorization": f"Bearer {make_access_token(str(user_id))}"},
        )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "invalid_token"


async def test_get_current_user_rejects_inactive_user(
    auth_app: tuple[FastAPI, AsyncMock],
) -> None:
    app, repo = auth_app
    user = make_user(is_active=False)
    repo.get_by_id.return_value = user

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/aro/auth/get_current_user",
            headers={"Authorization": f"Bearer {make_access_token(str(user.id))}"},
        )

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "inactive_user"


async def _tokens_for_user(
    db_session: AsyncSession, user_id: object
) -> list[AROUserAuthToken]:
    result = await db_session.exec(
        select(AROUserAuthToken)
        .where(col(AROUserAuthToken.user_id) == user_id)
        .execution_options(populate_existing=True)
    )
    return list(result.all())


async def _logout(refresh_token: str) -> int:
    app = FastAPI()
    app.include_router(router, prefix="/api/aro")
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        cookies={"refresh_token": refresh_token},
    ) as client:
        response = await client.post("/api/aro/auth/logout")
    return response.status_code


async def test_logout_revokes_entire_token_family(db_session: AsyncSession) -> None:
    user = make_user()
    db_session.add(user)
    await db_session.commit()

    # One login, refreshed twice -> three tokens in the same family
    first = await issue_refresh_token(user.id)
    second, _ = await rotate_refresh_token(first)
    third, _ = await rotate_refresh_token(second)

    assert await _logout(third) == 200

    tokens = await _tokens_for_user(db_session, user.id)
    assert len(tokens) == 3
    assert len({t.family_id for t in tokens}) == 1
    assert all(t.revoked_at is not None for t in tokens)


async def test_logout_leaves_other_sessions_active(db_session: AsyncSession) -> None:
    user = make_user()
    db_session.add(user)
    await db_session.commit()

    # Two separate logins
    this_device = await issue_refresh_token(user.id)
    other_device = await issue_refresh_token(user.id)

    assert await _logout(this_device) == 200

    # The other login can still refresh
    new_token, refreshed_user = await rotate_refresh_token(other_device)
    assert new_token
    assert refreshed_user.id == user.id


async def test_token_cannot_rotate_after_logout(db_session: AsyncSession) -> None:
    user = make_user()
    db_session.add(user)
    await db_session.commit()

    first = await issue_refresh_token(user.id)
    second, _ = await rotate_refresh_token(first)

    # Log out with the older token; the newest one must die too
    assert await _logout(first) == 200

    with pytest.raises(HTTPException) as exc_info:
        await rotate_refresh_token(second)
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail["code"] == "refresh_token_invalid"
