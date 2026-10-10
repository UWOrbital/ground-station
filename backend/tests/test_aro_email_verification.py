from collections.abc import AsyncGenerator
from typing import Any

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import app.api.aro.auth.services.verification_email as verification_email_module
from app.data.repositories.dal import DAL
from main import app

EMAIL = "verify.me@test.com"
PASSWORD = "VerifyMe123!"


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def sent_emails(monkeypatch: pytest.MonkeyPatch) -> list[Any]:
    """Capture every Email handed to the mailer instead of sending it over SMTP."""
    sent: list[Any] = []

    async def capture(message: Any) -> None:
        sent.append(message)

    monkeypatch.setattr(verification_email_module, "send", capture)
    return sent


@pytest_asyncio.fixture
async def registered_user(client: AsyncClient) -> dict[str, str]:
    res = await client.post(
        "/api/aro/auth/register", json={"email": EMAIL, "password": PASSWORD, "first_name": "Verify"}
    )
    assert res.status_code == 201, res.text
    return res.json()


async def request_token(client: AsyncClient, email: str = EMAIL) -> None:
    res = await client.post("/api/aro/auth/request-verify-token", json={"email": email})
    assert res.status_code == 202, res.text


async def issued_token(sent_emails: list[Any]) -> str:
    """Pull the verification token back out of the email that was sent."""
    assert len(sent_emails) == 1, "expected exactly one verification email"
    message = sent_emails[0]
    assert message.recipients[0].email == EMAIL
    return str(message.text).split("\n\n")[2]


async def is_verified_in_db(user_id: str) -> bool:
    user = await DAL.aro_users().get_first_by(id=user_id)
    assert user is not None
    return user.is_verified


async def test_request_verify_token_emails_a_code(
    client: AsyncClient, registered_user: dict[str, str], sent_emails: list[Any]
) -> None:
    await request_token(client)

    assert await is_verified_in_db(registered_user["id"]) is False
    token = await issued_token(sent_emails)
    assert token


async def test_verification_email_links_to_the_aro_frontend(
    client: AsyncClient, registered_user: dict[str, str], sent_emails: list[Any]
) -> None:
    await request_token(client)

    token = await issued_token(sent_emails)
    link = verification_email_module.verification_link(token)
    assert link.startswith("http://localhost:5173/verify?token=")
    assert token in str(sent_emails[0].html)


async def test_verify_marks_the_user_verified(
    client: AsyncClient, registered_user: dict[str, str], sent_emails: list[Any]
) -> None:
    await request_token(client)
    token = await issued_token(sent_emails)

    res = await client.post("/api/aro/auth/verify", json={"token": token})

    assert res.status_code == 200, res.text
    assert res.json()["is_verified"] is True
    assert await is_verified_in_db(registered_user["id"]) is True


async def test_verified_user_can_log_in(
    client: AsyncClient, registered_user: dict[str, str], sent_emails: list[Any]
) -> None:
    await request_token(client)
    token = await issued_token(sent_emails)
    await client.post("/api/aro/auth/verify", json={"token": token})

    res = await client.post("/api/aro/auth/login", data={"username": EMAIL, "password": PASSWORD})

    assert res.status_code == 200, res.text


async def test_verify_rejects_a_bad_token(
    client: AsyncClient, registered_user: dict[str, str], sent_emails: list[Any]
) -> None:
    res = await client.post("/api/aro/auth/verify", json={"token": "not-a-jwt"})

    assert res.status_code == 400
    assert res.json()["detail"] == "VERIFY_USER_BAD_TOKEN"
    assert await is_verified_in_db(registered_user["id"]) is False


async def test_verify_token_is_single_use(
    client: AsyncClient, registered_user: dict[str, str], sent_emails: list[Any]
) -> None:
    await request_token(client)
    token = await issued_token(sent_emails)
    assert (await client.post("/api/aro/auth/verify", json={"token": token})).status_code == 200

    again = await client.post("/api/aro/auth/verify", json={"token": token})

    assert again.status_code == 400
    assert again.json()["detail"] == "VERIFY_USER_ALREADY_VERIFIED"


async def test_request_verify_token_unknown_email_is_silent(
    client: AsyncClient, sent_emails: list[Any]
) -> None:
    await request_token(client, "nobody@test.com")

    assert sent_emails == []


async def test_request_verify_token_skips_inactive_user(
    client: AsyncClient, registered_user: dict[str, str], sent_emails: list[Any]
) -> None:
    await DAL.aro_users().update(registered_user["id"], {"is_active": False})
    await request_token(client)

    assert sent_emails == []


async def test_request_verify_token_skips_verified_user(
    client: AsyncClient, registered_user: dict[str, str], sent_emails: list[Any]
) -> None:
    await request_token(client)
    token = await issued_token(sent_emails)
    await client.post("/api/aro/auth/verify", json={"token": token})
    sent_emails.clear()

    await request_token(client)

    assert sent_emails == []
