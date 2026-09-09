import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from loguru import logger
from starlette.datastructures import Headers

import re

from app.config.logger_middleware import LoggerMiddleware, _content_length
from app.config.request_id_middleware import REQUEST_ID_HEADER, RequestIDMiddleware

_REQUEST_ID_RE = re.compile(r"Request ID: ([0-9a-fA-F-]{36})")


@pytest.fixture
def captured_logs():
    """Capture the raw message of every loguru record emitted during a test."""
    messages: list[str] = []
    sink_id = logger.add(lambda m: messages.append(m.record["message"]), level="INFO")  # INFO+ only: excludes VERBOSE SQLAlchemy param echo (a separate, console-only vector)
    try:
        yield messages
    finally:
        logger.remove(sink_id)


def _app_with_marker_response() -> FastAPI:
    """Build a tiny app behind LoggerMiddleware whose response body carries a marker."""
    app = FastAPI()

    @app.post("/thing")
    async def thing() -> dict[str, str]:
        return {"leak_marker": "RESP-SECRET-XYZ"}

    app.add_middleware(LoggerMiddleware)
    return app


def test_content_length_helper():
    """The helper returns the header value, or 'unknown' when it is absent."""
    assert _content_length(Headers({"content-length": "42"})) == "42"
    assert _content_length(Headers({})) == "unknown"


async def test_middleware_logs_metadata_only(captured_logs):
    """The middleware logs method/path/status/param-keys but never bodies, param values, or secrets."""
    app = _app_with_marker_response()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/thing",
            params={"code": "PARAM-SECRET-CODE"},
            json={"password": "BODY-SECRET-PW"},
        )
    assert resp.status_code == 200

    joined = "\n".join(captured_logs)
    # Metadata is present.
    assert "REQUEST | Method: POST" in joined
    assert "/thing" in joined
    assert "Status: 200" in joined
    assert "Param keys: ['code']" in joined  # the key, so we know a param was sent
    # Nothing sensitive is present: not the request body, the param value, or the response body.
    assert "BODY-SECRET-PW" not in joined
    assert "PARAM-SECRET-CODE" not in joined
    assert "RESP-SECRET-XYZ" not in joined


async def test_binary_request_body_does_not_crash(captured_logs):
    """A non-UTF-8 request body is fine now that the body is never read/decoded (was a 500 before)."""
    app = _app_with_marker_response()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/thing", content=b"\xff\xfe\x00\x01 binary body")

    assert resp.status_code == 200


async def test_response_body_passes_through_intact(captured_logs):
    """The middleware no longer drains/rebuilds the body, so responses stream through unchanged."""
    app = FastAPI()

    @app.get("/data")
    async def data() -> dict[str, str]:
        return {"value": "X" * 1000}

    app.add_middleware(LoggerMiddleware)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/data")

    assert resp.status_code == 200
    assert resp.json() == {"value": "X" * 1000}


async def test_logger_falls_back_to_own_id_when_mounted_alone(captured_logs):
    """Without RequestIDMiddleware upstream, LoggerMiddleware still logs a valid Request ID."""
    app = _app_with_marker_response()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/thing")

    assert resp.status_code == 200
    ids = _REQUEST_ID_RE.findall("\n".join(captured_logs))
    assert ids, "expected the logger to emit a Request ID"


async def test_logger_uses_shared_request_id_when_chained(captured_logs):
    """Chained with RequestIDMiddleware, the REQUEST and RESPONSE lines share the state id."""
    app = FastAPI()

    @app.post("/thing")
    async def thing() -> dict[str, str]:
        return {"ok": "yes"}

    # Mirror production order: RequestIDMiddleware runs first (added last).
    app.add_middleware(LoggerMiddleware)
    app.add_middleware(RequestIDMiddleware)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/thing")

    assert resp.status_code == 200
    logged_ids = _REQUEST_ID_RE.findall("\n".join(captured_logs))
    # Both the REQUEST and RESPONSE lines were logged with the same id...
    assert len(logged_ids) == 2
    assert logged_ids[0] == logged_ids[1]
    # ...and it matches the id handed back to the caller.
    assert logged_ids[0] == resp.headers[REQUEST_ID_HEADER]


async def test_error_responses_log_at_error_level(captured_logs):
    """A 4xx still logs a RESPONSE line (at error severity) with only metadata."""
    app = FastAPI()

    @app.get("/ok")
    async def ok() -> dict[str, str]:
        return {"ok": "yes"}

    app.add_middleware(LoggerMiddleware)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/missing")

    assert resp.status_code == 404
    joined = "\n".join(captured_logs)
    assert "RESPONSE | Status: 404" in joined
