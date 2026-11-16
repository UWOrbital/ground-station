import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient
from loguru import logger
from starlette.datastructures import Headers

from app.config.logger_middleware import LoggerMiddleware, _content_length
from app.config.request_id_middleware import REQUEST_ID_HEADER, RequestIDMiddleware


@pytest.fixture
def captured_logs():
    """Capture the message, level and extra of every loguru record emitted during a test."""
    records: list[dict[str, object]] = []
    sink_id = logger.add(
        lambda m: records.append(
            {"message": m.record["message"], "level": m.record["level"].name, "extra": dict(m.record["extra"])}
        ),
        level="INFO",  # INFO+ only: excludes VERBOSE SQLAlchemy param echo (a separate, console-only vector)
    )
    try:
        yield records
    finally:
        logger.remove(sink_id)


def _middleware_records(records: list[dict[str, object]], message: str) -> list[dict[str, object]]:
    """Return the LoggerMiddleware records with the given message ("Request" or "Response")."""
    return [r for r in records if r["message"] == message]


def _all_text(records: list[dict[str, object]]) -> str:
    """Join every record's message and extra into one string for PII negative checks."""
    return "\n".join(f"{r['message']} {r['extra']!r}" for r in records)


def _response_extra_without_duration(record: dict[str, object]) -> dict[str, object]:
    """Return a Response record's extra minus duration_ms (timing is not deterministic), after checking it."""
    extra = dict(record["extra"])
    duration_ms = extra.pop("duration_ms")
    assert isinstance(duration_ms, float)
    assert duration_ms >= 0
    return extra


def _app_with_marker_response() -> FastAPI:
    """Build a tiny app behind LoggerMiddleware whose response body carries a marker."""
    app = FastAPI()

    @app.post("/thing")
    async def thing() -> dict[str, str]:
        return {"leak_marker": "RESP-SECRET-XYZ"}

    app.add_middleware(LoggerMiddleware)
    return app


def _app_with_status_routes(excluded_endpoints: tuple[str, ...] = ()) -> FastAPI:
    """Build a tiny app behind LoggerMiddleware with a 2xx route and a 5xx route."""
    app = FastAPI()

    @app.get("/ok")
    async def ok() -> dict[str, str]:
        return {"ok": "yes"}

    @app.get("/boom")
    async def boom() -> JSONResponse:
        return JSONResponse({"error": "down"}, status_code=503)

    app.add_middleware(LoggerMiddleware, excluded_endpoints=excluded_endpoints)
    return app


def test_content_length_helper():
    """The helper returns the header value as an int, or None when it is absent or not an integer."""
    assert _content_length(Headers({"content-length": "42"})) == 42
    assert _content_length(Headers({})) is None
    assert _content_length(Headers({"content-length": "abc"})) is None


async def test_middleware_logs_metadata_only(captured_logs):
    """The middleware logs method/path/status/param-keys but never bodies, param values, or secrets."""
    app = _app_with_marker_response()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/thing",
            params={"state": "PARAM-SECRET-STATE", "code": "PARAM-SECRET-CODE"},
            content=b'{"password":"BODY-SECRET-PW"}',
            headers={"content-type": "application/json"},
        )
    assert resp.status_code == 200

    # Metadata is present, as exact bound fields. No RequestIDMiddleware here, so no request_id in extra.
    requests = _middleware_records(captured_logs, "Request")
    assert requests == [
        {
            "message": "Request",
            "level": "INFO",
            "extra": {
                "method": "POST",
                "path": "/thing",
                "user_id": None,  # no UserIdMiddleware, so request.state.user_id is unset
                "param_keys": "code,state",
                # 29 = len(b'{"password":"BODY-SECRET-PW"}')
                "request_content_length": 29,
            },
        }
    ]

    responses = _middleware_records(captured_logs, "Response")
    assert len(responses) == 1
    assert responses[0]["level"] == "INFO"  # 2xx
    assert _response_extra_without_duration(responses[0]) == {
        "status": 200,
        # 33 = len('{"leak_marker":"RESP-SECRET-XYZ"}'),
        # FastAPI's compact JSON rendering of the handler's return value
        "response_content_length": 33,
    }

    # Nothing sensitive is present in any message or bound field:
    # not the request body, the param values, or the response body.
    joined = _all_text(captured_logs)
    assert "BODY-SECRET-PW" not in joined
    assert "PARAM-SECRET-CODE" not in joined
    assert "PARAM-SECRET-STATE" not in joined
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


async def test_logger_uses_shared_request_id_when_chained(captured_logs):
    """Chained with RequestIDMiddleware, the Request and Response records share the state id."""
    app = FastAPI()

    @app.get("/thing")
    async def thing() -> dict[str, str]:
        return {"ok": "yes"}

    # Mirror production order: RequestIDMiddleware runs first (added last).
    app.add_middleware(LoggerMiddleware)
    app.add_middleware(RequestIDMiddleware)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/thing")
    assert resp.status_code == 200

    # request_id reaches extra through RequestIDMiddleware's logger.contextualize, and must
    # match the id handed back to the caller.
    request_id = resp.headers[REQUEST_ID_HEADER]

    requests = _middleware_records(captured_logs, "Request")
    assert len(requests) == 1
    assert requests[0]["extra"] == {
        "request_id": request_id,
        "method": "GET",
        "path": "/thing",
        "user_id": None,
        "param_keys": "",
        "request_content_length": None,  # None when the header is absent (a GET has none)
    }

    responses = _middleware_records(captured_logs, "Response")
    assert len(responses) == 1
    assert _response_extra_without_duration(responses[0]) == {
        "request_id": request_id,  # same id as the Request record
        "status": 200,
        "response_content_length": 12,  # 12 = len('{"ok":"yes"}')
    }


async def test_error_responses_log_at_error_level(captured_logs):
    """A 4xx still logs a Response record (at ERROR) with only metadata."""
    app = _app_with_status_routes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/missing")
    assert resp.status_code == 404

    responses = _middleware_records(captured_logs, "Response")
    assert len(responses) == 1
    assert responses[0]["level"] == "ERROR"
    assert _response_extra_without_duration(responses[0]) == {
        "status": 404,
        "response_content_length": 22,  # 22 = len('{"detail":"Not Found"}')
    }


async def test_server_error_responses_log_at_critical_level(captured_logs):
    """A 5xx logs a Response record at CRITICAL."""
    app = _app_with_status_routes()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/boom")
    assert resp.status_code == 503

    responses = _middleware_records(captured_logs, "Response")
    assert len(responses) == 1
    assert responses[0]["level"] == "CRITICAL"
    assert _response_extra_without_duration(responses[0]) == {
        "status": 503,
        "response_content_length": 16,  # 16 = len('{"error":"down"}')
    }


async def test_excluded_endpoint_logs_request_but_not_response(captured_logs):
    """An excluded endpoint still logs its Request record, but its Response record is skipped."""
    app = _app_with_status_routes(excluded_endpoints=("/ok",))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        excluded = await client.get("/ok")
        included = await client.get("/boom")
    assert excluded.status_code == 200
    assert included.status_code == 503

    # Both requests are logged; the exclusion only applies to the response line.
    assert [r["extra"]["path"] for r in _middleware_records(captured_logs, "Request")] == ["/ok", "/boom"]
    # Only the non-excluded endpoint's response is logged.
    assert [r["extra"]["status"] for r in _middleware_records(captured_logs, "Response")] == [503]
