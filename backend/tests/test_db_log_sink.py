import asyncio
import contextlib
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from loguru import logger

from app.config import db_log_sink
from app.config.db_log_sink import (
    _SENTINEL,
    _consumer,
    _db_sink_filter,
    _enqueue,
    _json_safe,
    _record_to_row,
    _sink,
    _write_batch,
    start_db_log_sink,
    stop_db_log_sink,
)
from app.config.env_settings.logger_config import LoggerConfig
from app.data.repositories.dal import DAL


@pytest.fixture(autouse=True)
def _reset_sink_globals():
    """Ensure no loguru handler or module state leaks between tests in this file."""
    yield
    if db_log_sink._sink_id is not None:
        with contextlib.suppress(Exception):
            logger.remove(db_log_sink._sink_id)
    db_log_sink._sink_id = None
    db_log_sink._queue = None
    db_log_sink._consumer_task = None
    db_log_sink._loop = None


def _record(level_name: str = "INFO", name: str = "app.api.middleware", extra: dict | None = None) -> dict:
    """Build a minimal loguru-style record dict for the sink helpers."""
    return {
        "time": datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        "level": SimpleNamespace(name=level_name),
        "message": "a message",
        "name": name,
        "function": "handler",
        "line": 7,
        "extra": extra or {},
    }


def test_filter_drops_verbose_records():
    """VERBOSE records (the sink's own SQLAlchemy query logs) must be filtered out."""
    assert _db_sink_filter(_record(level_name="VERBOSE")) is False


def test_filter_drops_sqlalchemy_named_records():
    """Defense-in-depth: anything logging under a sqlalchemy-prefixed logger is dropped.

    This is not the main recursion path (re-emitted engine logs are named after
    setup_logging's module and caught by the VERBOSE/level guard instead), but the
    name check still shields against a library logging directly as ``sqlalchemy.*``.
    """
    assert _db_sink_filter(_record(name="sqlalchemy.engine.Engine")) is False


def test_filter_keeps_normal_records():
    """Ordinary application records pass the filter."""
    assert _db_sink_filter(_record(level_name="ERROR")) is True


def test_record_to_row_maps_fields():
    """The loguru record is mapped onto APILog column kwargs."""
    row = _record_to_row(_record(level_name="WARNING", extra={"request_id": "abc"}))

    assert row["priority"] == "WARNING"
    assert row["message"] == "a message"
    assert row["module"] == "app.api.middleware"
    assert row["function"] == "handler"
    assert row["line"] == 7
    assert row["extra"] == {"request_id": "abc"}


def test_json_safe_stringifies_non_serializable_values():
    """Non-JSON values in extra are stringified so a batch never fails to insert."""
    result = _json_safe({"ok": 1, "obj": object()})

    assert result["ok"] == 1
    assert isinstance(result["obj"], str)


def test_json_safe_empty_returns_none():
    """An empty or missing extra bag maps to NULL, not an empty object."""
    assert _json_safe(None) is None
    assert _json_safe({}) is None


async def test_write_batch_persists_rows(monkeypatch, db_session):
    """_write_batch inserts every row it is given into logs.api."""

    @asynccontextmanager
    async def _fake_session():
        yield db_session

    monkeypatch.setattr(db_log_sink, "get_db_session", _fake_session, raising=True)

    rows = [_record_to_row(_record()), _record_to_row(_record(level_name="ERROR"))]
    await _write_batch(rows)

    stored = await DAL.api_logs().get_recent(limit=10)
    assert len(stored) == 2
    assert {log.priority for log in stored} == {"INFO", "ERROR"}


async def test_write_batch_empty_is_noop(monkeypatch):
    """An empty batch never touches the database."""

    def _boom():
        raise AssertionError("get_db_session should not be called for an empty batch")

    monkeypatch.setattr(db_log_sink, "get_db_session", _boom, raising=True)
    await _write_batch([])  # must not raise


# --- consumer batching -------------------------------------------------------


def _capture_write_batch(monkeypatch) -> list[list[dict]]:
    """Replace _write_batch with an async capture; return the list of batches written."""
    batches: list[list[dict]] = []

    async def _capture(rows: list[dict]) -> None:
        batches.append(list(rows))

    monkeypatch.setattr(db_log_sink, "_write_batch", _capture, raising=True)
    return batches


async def test_consumer_collapses_a_burst_into_one_batch(monkeypatch):
    """Rows already queued (fewer than batch_size) are written in a single batch."""
    batches = _capture_write_batch(monkeypatch)
    queue: asyncio.Queue = asyncio.Queue()
    rows = [_record_to_row(_record()) for _ in range(3)]
    for row in rows:
        queue.put_nowait(row)
    queue.put_nowait(_SENTINEL)

    await _consumer(queue, batch_size=50)

    assert batches == [rows]


async def test_consumer_splits_on_batch_size(monkeypatch):
    """A burst larger than batch_size is written in batch_size-bounded chunks."""
    batches = _capture_write_batch(monkeypatch)
    queue: asyncio.Queue = asyncio.Queue()
    rows = [_record_to_row(_record(extra={"i": i})) for i in range(4)]
    for row in rows:
        queue.put_nowait(row)
    queue.put_nowait(_SENTINEL)

    await _consumer(queue, batch_size=2)

    assert [len(b) for b in batches] == [2, 2]
    assert batches[0] == rows[:2]
    assert batches[1] == rows[2:]


async def test_consumer_flushes_partial_batch_before_stopping(monkeypatch):
    """A sentinel encountered mid-batch flushes what was collected, then returns."""
    batches = _capture_write_batch(monkeypatch)
    queue: asyncio.Queue = asyncio.Queue()
    rows = [_record_to_row(_record()) for _ in range(2)]
    for row in rows:
        queue.put_nowait(row)
    queue.put_nowait(_SENTINEL)

    await _consumer(queue, batch_size=10)  # returns (does not hang) on the sentinel

    assert batches == [rows]


async def test_consumer_sentinel_first_writes_nothing(monkeypatch):
    """A sentinel with no preceding rows stops the consumer without any write."""
    batches = _capture_write_batch(monkeypatch)
    queue: asyncio.Queue = asyncio.Queue()
    queue.put_nowait(_SENTINEL)

    await _consumer(queue, batch_size=10)

    assert batches == []


# --- enqueue / sink hand-off -------------------------------------------------


def test_enqueue_puts_row_on_queue():
    """_enqueue places the row on the module queue."""
    db_log_sink._queue = asyncio.Queue()
    row = _record_to_row(_record())

    _enqueue(row)

    assert db_log_sink._queue.get_nowait() is row


def test_enqueue_drops_row_when_queue_full(capsys):
    """When the buffer is full the row is dropped (and reported), never blocking."""
    db_log_sink._queue = asyncio.Queue(maxsize=1)
    db_log_sink._queue.put_nowait(_record_to_row(_record()))

    _enqueue(_record_to_row(_record(level_name="ERROR")))  # must not raise/block

    assert db_log_sink._queue.qsize() == 1
    assert "dropping a log row" in capsys.readouterr().err


def test_enqueue_noop_when_not_started():
    """With no queue configured, _enqueue is a silent no-op."""
    db_log_sink._queue = None
    _enqueue(_record_to_row(_record()))  # must not raise


async def test_sink_noop_when_not_started():
    """The sink callback does nothing when the loop/queue are not configured."""
    db_log_sink._loop = None
    db_log_sink._queue = None
    _sink(SimpleNamespace(record=_record()))  # must not raise


async def test_sink_schedules_row_onto_queue():
    """_sink maps the record and schedules it onto the queue via the event loop."""
    db_log_sink._loop = asyncio.get_running_loop()
    db_log_sink._queue = asyncio.Queue()

    _sink(SimpleNamespace(record=_record(level_name="WARNING", extra={"request_id": "xyz"})))
    await asyncio.sleep(0)  # let call_soon_threadsafe run _enqueue

    row = db_log_sink._queue.get_nowait()
    assert row["priority"] == "WARNING"
    assert row["extra"] == {"request_id": "xyz"}


# --- start / stop lifecycle --------------------------------------------------


async def test_start_is_noop_when_disabled():
    """The sink is never registered when db_sink_enabled is False."""
    start_db_log_sink(asyncio.get_running_loop(), LoggerConfig(db_sink_enabled=False))

    assert db_log_sink._sink_id is None
    assert db_log_sink._queue is None


async def test_start_is_idempotent():
    """Calling start twice does not register a second loguru handler."""
    config = LoggerConfig(db_sink_enabled=True)
    start_db_log_sink(asyncio.get_running_loop(), config)
    first_id = db_log_sink._sink_id
    start_db_log_sink(asyncio.get_running_loop(), config)

    assert db_log_sink._sink_id == first_id
    await stop_db_log_sink()


async def test_start_then_stop_flushes_and_resets(monkeypatch):
    """start wires up the pipeline; stop drains buffered rows and clears state."""
    batches = _capture_write_batch(monkeypatch)
    config = LoggerConfig(db_sink_enabled=True, db_sink_batch_size=50, db_sink_queue_maxsize=100)

    start_db_log_sink(asyncio.get_running_loop(), config)
    assert db_log_sink._sink_id is not None
    assert db_log_sink._consumer_task is not None

    _enqueue(_record_to_row(_record()))
    _enqueue(_record_to_row(_record(level_name="ERROR")))

    await stop_db_log_sink()

    assert [row["priority"] for batch in batches for row in batch] == ["INFO", "ERROR"]
    assert db_log_sink._sink_id is None
    assert db_log_sink._queue is None
    assert db_log_sink._consumer_task is None


async def test_stop_without_start_is_safe():
    """stop is a no-op when the sink was never started."""
    await stop_db_log_sink()  # must not raise
    assert db_log_sink._queue is None
