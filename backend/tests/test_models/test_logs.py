from datetime import UTC, datetime, timedelta

import pytest
from app.data.repositories.dal import DAL


@pytest.fixture
def log_repo():
    """Provides an APILog repository bound to the test database."""
    return DAL.api_logs()


@pytest.fixture
def log_row():
    """A representative logs.api row payload."""
    return {
        "priority": "ERROR",
        "message": "something went wrong",
        "module": "app.api.middleware",
        "function": "dispatch",
        "line": 42,
        "extra": {"request_id": "abc-123", "user_id": "anon"},
    }


async def test_create_persists_all_columns(log_repo, log_row):
    """A created APILog round-trips every column, including the JSON extra bag."""
    result = await log_repo.create(log_row)

    assert result.id is not None
    assert result.time is not None  # default_factory populated it
    assert result.priority == log_row["priority"]
    assert result.message == log_row["message"]
    assert result.module == log_row["module"]
    assert result.function == log_row["function"]
    assert result.line == log_row["line"]
    assert result.extra == log_row["extra"]


async def test_create_allows_minimal_row(log_repo):
    """Only priority and message are required; the rest default to None."""
    result = await log_repo.create({"priority": "INFO", "message": "hello"})

    assert result.priority == "INFO"
    assert result.message == "hello"
    assert result.module is None
    assert result.function is None
    assert result.line is None
    assert result.extra is None


async def test_get_recent_returns_newest_first(log_repo):
    """get_recent orders rows by time descending and honours the limit."""
    base = datetime(2026, 1, 1, tzinfo=UTC)
    for i in range(3):
        await log_repo.create(
            {"priority": "INFO", "message": f"msg {i}", "time": base + timedelta(minutes=i)}
        )

    recent = await log_repo.get_recent(limit=2)

    assert len(recent) == 2
    assert recent[0].message == "msg 2"
    assert recent[1].message == "msg 1"
