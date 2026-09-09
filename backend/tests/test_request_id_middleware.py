from uuid import UUID

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from loguru import logger

from app.config.request_id_middleware import REQUEST_ID_HEADER, RequestIDMiddleware


def _app_echoing_request_id() -> FastAPI:
    """Build a tiny app behind RequestIDMiddleware whose handler echoes the state id."""
    app = FastAPI()

    @app.get("/whoami")
    async def whoami(request: Request) -> dict[str, str]:
        # Reading request.state proves the id set in the outer middleware
        # propagated across the middleware boundary to the handler.
        return {"request_id": request.state.request_id}

    app.add_middleware(RequestIDMiddleware)
    return app


def _assert_is_uuid(value: str) -> None:
    """Assert a string is a canonical UUID (raises ValueError otherwise)."""
    assert str(UUID(value)) == value


async def test_request_id_on_state_header_and_valid_uuid():
    """The handler sees the id on state, it is a valid UUID, and it matches the response header."""
    app = _app_echoing_request_id()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/whoami")

    assert resp.status_code == 200
    body_id = resp.json()["request_id"]
    header_id = resp.headers[REQUEST_ID_HEADER]
    _assert_is_uuid(body_id)
    assert body_id == header_id


async def test_each_request_gets_a_distinct_id():
    """Two requests receive two different correlation ids."""
    app = _app_echoing_request_id()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        first = await client.get("/whoami")
        second = await client.get("/whoami")

    assert first.json()["request_id"] != second.json()["request_id"]


async def test_inbound_request_id_header_is_ignored():
    """An attacker-supplied X-Request-ID is not trusted; the server mints its own."""
    app = _app_echoing_request_id()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/whoami", headers={REQUEST_ID_HEADER: "spoofed-id"})

    assert resp.json()["request_id"] != "spoofed-id"
    _assert_is_uuid(resp.json()["request_id"])


async def test_request_id_is_bound_into_log_context():
    """Logs emitted while handling the request carry the id in loguru's extra."""
    captured: list[dict[str, object]] = []
    sink_id = logger.add(lambda m: captured.append(dict(m.record["extra"])), level="INFO")

    app = FastAPI()

    @app.get("/emit")
    async def emit() -> dict[str, str]:
        logger.info("handler ran")
        return {"ok": "yes"}

    app.add_middleware(RequestIDMiddleware)

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get("/emit")
    finally:
        logger.remove(sink_id)

    handler_extras = [extra for extra in captured if extra.get("request_id")]
    assert handler_extras, "expected at least one log record carrying request_id"
    _assert_is_uuid(str(handler_extras[0]["request_id"]))
    assert str(handler_extras[0]["request_id"]) == resp.headers[REQUEST_ID_HEADER]
