"""End-to-end tests for the database log sink.

These exercise the *whole* logging-to-DB pipeline against the real
testcontainers Postgres: a log emitted through the real loguru ``logger`` flows
through the registered sink, the cross-thread hand-off, the batching background
consumer, and a real asyncpg ``INSERT`` into ``logs.api`` — then we read the row
straight back out of the database.

The only substitution is the sink's session factory: the production engine
(``engine.get_db_session``) is built from import-time settings and is not wired
to the throwaway container, so ``sink_on_container`` redirects just that factory
to the test ``db_engine``. Everything else is the production code path.

Because the sink commits on its own connection (outside the ``db_session``
rollback fixture), each test tags its logs with a unique marker and deletes them
on teardown so nothing leaks into the shared session-scoped container.
"""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import uuid4

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from loguru import logger
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import db_log_sink
from app.config.backend_setup import setup_middlewares
from app.config.db_log_sink import start_db_log_sink, stop_db_log_sink
from app.config.env_settings.logger_config import LoggerConfig
from app.config.request_id_middleware import REQUEST_ID_HEADER
from app.data.models.logs_models import APILog


@pytest_asyncio.fixture
async def sink_on_container(monkeypatch, db_engine: AsyncEngine):
    """Redirect the DB log sink at the testcontainers Postgres; guarantee teardown.

    Yields nothing; the test drives ``start_db_log_sink`` / ``stop_db_log_sink``
    itself so it can flush deterministically before asserting. The teardown is a
    safety net that removes the global loguru handler if a test fails mid-flight.
    """

    @asynccontextmanager
    async def _session():
        session = AsyncSession(db_engine, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()

    monkeypatch.setattr(db_log_sink, "get_db_session", _session, raising=True)
    yield
    if db_log_sink._sink_id is not None:
        await stop_db_log_sink()


async def _logs_matching(db_engine: AsyncEngine, needle: str) -> list[APILog]:
    """Return every persisted APILog whose message contains ``needle``, oldest first."""
    async with AsyncSession(db_engine, expire_on_commit=False) as session:
        result = await session.exec(
            select(APILog).where(col(APILog.message).contains(needle)).order_by(col(APILog.time))
        )
        return list(result.all())


async def _delete_logs_matching(db_engine: AsyncEngine, needle: str) -> None:
    """Delete the rows a test created so the shared container stays clean."""
    async with AsyncSession(db_engine, expire_on_commit=False) as session:
        await session.exec(delete(APILog).where(col(APILog.message).contains(needle)))
        await session.commit()


async def test_log_line_persists_end_to_end(sink_on_container, db_engine: AsyncEngine):
    """A single logger.info call lands as one row in logs.api with its fields intact."""
    marker = f"e2e-direct-{uuid4().hex}"
    start_db_log_sink(asyncio.get_running_loop(), LoggerConfig(db_sink_enabled=True))
    try:
        logger.bind(request_id=marker).info(f"hello from {marker}")
        # The sink hands off via loop.call_soon_threadsafe; yield once so that enqueue
        # runs and the row is on the queue before stop() drops the flush sentinel in
        # behind it (see the shutdown-race note in stop_db_log_sink).
        await asyncio.sleep(0)
        await stop_db_log_sink()  # deterministically flush the queue before asserting

        rows = await _logs_matching(db_engine, marker)
        assert len(rows) == 1
        row = rows[0]
        assert row.priority == "INFO"
        assert marker in row.message
        assert row.extra == {"request_id": marker}
        assert row.time is not None
    finally:
        await _delete_logs_matching(db_engine, marker)


async def test_message_with_nul_bytes_persists_sanitized(sink_on_container, db_engine: AsyncEngine):
    """A message carrying NUL bytes (as a decoded binary body would) still lands in Postgres.

    This is the concrete regression: Postgres text columns reject the NUL byte, and a
    binary response body decoded with errors="ignore" keeps NUL. Without sanitizing, the
    real asyncpg INSERT would fail and the row would be dropped — so a persisted, NUL-free
    row proves the fix against a real database.
    """
    marker = uuid4().hex
    start_db_log_sink(asyncio.get_running_loop(), LoggerConfig(db_sink_enabled=True))
    try:
        logger.info(f"RESPONSE body {marker} \x00\x00 binary\x00tail")
        await asyncio.sleep(0)
        await stop_db_log_sink()

        rows = await _logs_matching(db_engine, marker)
        assert len(rows) == 1
        assert "\x00" not in rows[0].message
        assert marker in rows[0].message
    finally:
        await _delete_logs_matching(db_engine, marker)


async def _logs_with_extra(db_engine: AsyncEngine, key: str, value: str) -> list[APILog]:
    """Return every persisted APILog whose ``extra[key]`` equals ``value``, oldest first."""
    async with AsyncSession(db_engine, expire_on_commit=False) as session:
        result = await session.exec(
            select(APILog).where(col(APILog.extra)[key].as_string() == value).order_by(col(APILog.time))
        )
        return list(result.all())


async def _delete_logs_with_extra(db_engine: AsyncEngine, key: str, value: str) -> None:
    """Delete the rows whose ``extra[key]`` equals ``value`` so the shared container stays clean."""
    async with AsyncSession(db_engine, expire_on_commit=False) as session:
        await session.exec(delete(APILog).where(col(APILog.extra)[key].as_string() == value))
        await session.commit()


async def test_request_logs_persist_through_middleware(sink_on_container, db_engine: AsyncEngine):
    """An HTTP request through the real middleware stack persists correlated Request + Response rows.

    The middleware logs metadata only (no bodies or query-param values) as bound fields, so the
    marker is carried in the URL path, which lands in ``extra["path"]``. The Request/Response pair
    is correlated through the shared ``extra["request_id"]``.
    """
    marker = uuid4().hex
    path = f"/e2e-ping-{marker}"
    app = FastAPI()

    @app.get(path)
    async def _ping() -> dict[str, str]:
        return {"ok": "true"}

    setup_middlewares(app)  # real CORS + Session + LoggerMiddleware + UserId + RequestID
    start_db_log_sink(asyncio.get_running_loop(), LoggerConfig(db_sink_enabled=True))
    request_id = ""
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.get(path)
            assert resp.status_code == 200
        request_id = resp.headers[REQUEST_ID_HEADER]
        await asyncio.sleep(0)  # let the queued enqueues land before the flush sentinel
        await stop_db_log_sink()  # flush

        # The path is a bound field, so exactly one row (the Request row) carries it.
        path_rows = await _logs_with_extra(db_engine, "path", path)
        assert [(row.message, row.priority) for row in path_rows] == [("Request", "INFO")]
        request_extra = dict(path_rows[0].extra or {})
        assert "request_received_at" in request_extra
        received_at = request_extra.pop("request_received_at")
        assert isinstance(received_at, str)
        datetime.strptime(received_at, "%Y-%m-%d %H:%M:%S")  # raises if the format differs
        assert request_extra == {
            "request_id": request_id,  # from RequestIDMiddleware's logger.contextualize
            "method": "GET",
            "path": path,
            "user_id": None,  # unauthenticated request: UserIdMiddleware leaves state.user_id unset
            "param_keys": "",
            "request_content_length": "unknown",  # "unknown" when the header is absent
        }

        # Its Response counterpart shares the request_id (the response row has no path).
        correlated = await _logs_with_extra(db_engine, "request_id", request_id)
        assert [(row.message, row.priority) for row in correlated] == [("Request", "INFO"), ("Response", "INFO")]
        response_extra = dict(correlated[1].extra or {})
        duration_ms = response_extra.pop("duration_ms")
        assert isinstance(duration_ms, float)  # floats survive _json_safe and the JSON column unchanged
        assert response_extra == {
            "request_id": request_id,
            "status": 200,  # ints survive _json_safe and the JSON column unchanged
            "response_content_length": "13",  # 13 = len('{"ok":"true"}')
        }
    finally:
        await _delete_logs_with_extra(db_engine, "path", path)
        if request_id:
            await _delete_logs_with_extra(db_engine, "request_id", request_id)
