from contextlib import asynccontextmanager
from datetime import UTC, datetime
from types import SimpleNamespace

from app.config import db_log_sink
from app.config.db_log_sink import _db_sink_filter, _json_safe, _record_to_row, _write_batch
from app.data.repositories.dal import DAL


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
    """Records originating from sqlalchemy loggers are dropped to avoid feedback."""
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
