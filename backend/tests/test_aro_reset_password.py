from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import Request
from httpx import ASGITransport, AsyncClient

from app.api.aro.auth.adapter import AROUserRecord
from app.api.aro.auth.manager import AROUserManager
from app.data.repositories.dal import DAL
from main import app

EMAIL = "reset.me@test.com"
OLD_PASSWORD = "OldPassword123!"
NEW_PASSWORD = "NewPassword456!"


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sent_tokens(monkeypatch: pytest.MonkeyPatch) -> list[tuple[str, str]]:
    sent: list[tuple[str, str]] = []
    original = AROUserManager.on_after_forgot_password

    # Record the token, then still run the real stub so it's exercised too
    async def record(self: AROUserManager, user: AROUserRecord, token: str, request: Request | None = None) -> None:
        sent.append((user.email, token))
        await original(self, user, token, request)

    monkeypatch.setattr(AROUserManager, "on_after_forgot_password", record)
    return sent


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict[str, str]:
    res = await client.post(
        "/api/aro/auth/register", json={"email": EMAIL, "password": OLD_PASSWORD, "first_name": "Reset"}
    )
    assert res.status_code == 201, res.text
    return res.json()


async def login(client: AsyncClient, password: str) -> int:
    res = await client.post("/api/aro/auth/login", data={"username": EMAIL, "password": password})
    return res.status_code


async def forgot(client: AsyncClient, email: str) -> None:
    res = await client.post("/api/aro/auth/forgot-password", json={"email": email})
    assert res.status_code == 202, res.text


async def test_forgot_password_hands_token_to_hook(
    client: AsyncClient, registered_user: dict[str, str], sent_tokens: list[tuple[str, str]]
) -> None:
    await forgot(client, EMAIL)
    assert len(sent_tokens) == 1
    assert sent_tokens[0][0] == EMAIL
    assert sent_tokens[0][1]


async def test_reset_password_swaps_login_password(
    client: AsyncClient, registered_user: dict[str, str], sent_tokens: list[tuple[str, str]]
) -> None:
    await forgot(client, EMAIL)
    res = await client.post("/api/aro/auth/reset-password", json={"token": sent_tokens[0][1], "password": NEW_PASSWORD})
    assert res.status_code == 200, res.text
    assert await login(client, OLD_PASSWORD) == 401
    assert await login(client, NEW_PASSWORD) == 200


async def test_reset_token_is_single_use(
    client: AsyncClient, registered_user: dict[str, str], sent_tokens: list[tuple[str, str]]
) -> None:
    await forgot(client, EMAIL)
    token = sent_tokens[0][1]
    first = await client.post("/api/aro/auth/reset-password", json={"token": token, "password": NEW_PASSWORD})
    assert first.status_code == 200, first.text
    # Token carries a fingerprint of the old hash, so it dies once the password changes
    again = await client.post("/api/aro/auth/reset-password", json={"token": token, "password": "Another789!"})
    assert again.status_code == 400
    assert again.json()["detail"] == "RESET_PASSWORD_BAD_TOKEN"


async def test_forgot_password_unknown_email_is_silent(client: AsyncClient, sent_tokens: list[tuple[str, str]]) -> None:
    await forgot(client, "nobody@test.com")
    assert sent_tokens == []


async def test_forgot_password_inactive_user_gets_no_token(
    client: AsyncClient, registered_user: dict[str, str], sent_tokens: list[tuple[str, str]]
) -> None:
    await DAL.aro_users().update(registered_user["id"], {"is_active": False})
    await forgot(client, EMAIL)
    assert sent_tokens == []


async def test_reset_password_rejects_bad_token(client: AsyncClient, registered_user: dict[str, str]) -> None:
    res = await client.post("/api/aro/auth/reset-password", json={"token": "not-a-jwt", "password": NEW_PASSWORD})
    assert res.status_code == 400
    assert res.json()["detail"] == "RESET_PASSWORD_BAD_TOKEN"
    assert await login(client, OLD_PASSWORD) == 200
