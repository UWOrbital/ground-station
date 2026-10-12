import jwt
import pytest
from app.config.env_settings.backend_config import settings
from app.config.user_id_middleware import UserIdMiddleware
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient

JWT_SECRET = "test-secret"


def _app_echoing_user_id() -> FastAPI:
    """
    Build a tiny app behind UserIdMiddleware whose handler reads request.state.
    """
    app = FastAPI()

    @app.get("/whoami")
    async def whoami(request: Request) -> dict[str, str | None]:
        return {"user_id": getattr(request.state, "user_id", None)}

    app.add_middleware(UserIdMiddleware)
    return app


def mint_token(**payload: object) -> str:
    """
    Create a test JWT using the same algorithm as the middleware.
    """
    return jwt.encode(payload, JWT_SECRET, algorithm="HS256")


@pytest.fixture(autouse=True)
def jwt_secret(monkeypatch):
    """
    Patch the application JWT secret for the duration of the test.
    """

    monkeypatch.setattr(settings.auth, "jwt_secret", JWT_SECRET)



def test_extract_user_id_from_valid_bearer_token():
    """
    A valid Bearer JWT with a sub claim returns the user id.
    """
    middleware = UserIdMiddleware(app=FastAPI())
    token = mint_token(
        sub="user-123"
    )

    assert middleware.extract_user_id(f"Bearer {token}") == "user-123"


def test_extract_user_id_is_case_insensitive_for_bearer_scheme():
    """
    The Bearer authentication scheme is case-insensitive.
    """
    middleware = UserIdMiddleware(app=FastAPI())
    token = mint_token(
        sub="user-123"
    )

    assert middleware.extract_user_id(f"bearer {token}") == "user-123"
    assert middleware.extract_user_id(f"BEARER {token}") == "user-123"


@pytest.mark.parametrize(
    "auth_header",
    [
        "",
        "Basic abc",
        "Token abc",
        "Bearer",
        "Bearer ",
        "bearer",
        "bearer ",
        "not-a-valid-header",
    ],
)
def test_extract_user_id_rejects_invalid_authorization_header(auth_header):
    """
    Malformed or non-Bearer Authorization headers are unauthenticated.
    """
    middleware = UserIdMiddleware(app=FastAPI())

    assert middleware.extract_user_id(auth_header) is None


def test_extract_user_id_rejects_invalid_jwt():
    """
    An invalid JWT is treated as an unauthenticated request.
    """
    middleware = UserIdMiddleware(app=FastAPI())

    assert middleware.extract_user_id("Bearer definitely-not-a-jwt") is None


def test_extract_user_id_rejects_token_signed_with_wrong_secret():
    """
    A JWT signed with a different secret is rejected.
    """
    middleware = UserIdMiddleware(app=FastAPI())
    token = jwt.encode(
        {"sub": "user-123"},
        "wrong-secret",
        algorithm="HS256",
    )

    assert middleware.extract_user_id(f"Bearer {token}") is None


def test_extract_user_id_rejects_token_using_wrong_algorithm():
    """
    Only HS256 tokens are accepted.
    """
    middleware = UserIdMiddleware(app=FastAPI())

    # HS384 is intentionally not one of the middleware's allowed algorithms.
    token = jwt.encode(
        {"sub": "user-123"},
        JWT_SECRET,
        algorithm="HS384",
    )

    assert middleware.extract_user_id(f"Bearer {token}") is None


def test_extract_user_id_returns_none_when_sub_is_missing(jwt_secret):
    """
    A valid JWT without a sub claim is treated as unauthenticated.
    """
    middleware = UserIdMiddleware(app=FastAPI())
    token = mint_token(
        email="user@example.com"
    )

    assert middleware.extract_user_id(f"Bearer {token}") is None


async def test_dispatch_sets_user_id_on_request_state():
    """
    An authenticated request exposes the JWT subject through request.state.
    """
    app = _app_echoing_user_id()
    token = mint_token(
        sub="user-123"
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/whoami",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {"user_id": "user-123"}


async def test_dispatch_does_not_set_user_id_without_authorization_header():
    """
    Requests without Authorization remain unauthenticated.
    """
    app = _app_echoing_user_id()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/whoami")

    assert response.status_code == 200
    assert response.json() == {"user_id": None}


async def test_dispatch_does_not_set_user_id_for_invalid_token():
    """
    Requests with an invalid JWT remain unauthenticated.
    """
    app = _app_echoing_user_id()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/whoami",
            headers={"Authorization": "Bearer invalid-token"},
        )

    assert response.status_code == 200
    assert response.json() == {"user_id": None}


async def test_dispatch_does_not_set_user_id_for_non_bearer_auth():
    """
    Non-Bearer authentication schemes are ignored.
    """
    app = _app_echoing_user_id()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get(
            "/whoami",
            headers={"Authorization": "Basic abc123"},
        )

    assert response.status_code == 200
    assert response.json() == {"user_id": None}


async def test_dispatch_still_calls_handler_for_unauthenticated_request():
    """
    Missing or invalid authentication does not prevent the request from reaching the handler.
    """
    app = _app_echoing_user_id()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/whoami")

    assert response.status_code == 200
    assert response.json()["user_id"] is None
