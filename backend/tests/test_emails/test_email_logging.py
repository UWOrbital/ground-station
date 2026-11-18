from datetime import datetime

import pytest
from loguru import logger
from pydantic import NameEmail

import app.utils.email as email_module
from app.utils.email import Email, EmailType, send_many


@pytest.fixture
def captured_logs():
    """Capture the message, level and extra of every loguru record emitted during a test."""
    records: list[dict[str, object]] = []
    sink_id = logger.add(
        lambda m: records.append(
            {
                "message": m.record["message"],
                "level": m.record["level"].name,
                "extra": dict(m.record["extra"]),
                "exception": m.record["exception"],
            }
        ),
        level="INFO",  # INFO+ only: excludes VERBOSE SQLAlchemy param echo (a separate, console-only vector)
    )
    try:
        yield records
    finally:
        logger.remove(sink_id)


def _email_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Keep only the send_many records so unrelated logs can't affect the assertions."""
    return [r for r in records if r["message"] in ("Email send start", "Email send success", "Email send fail")]


def _extra_without_time(record: dict[str, object]) -> dict[str, object]:
    """Return a record's extra minus time (wall-clock time), after checking its format."""
    extra = dict(record["extra"])
    assert "time" in extra
    time = extra.pop("time")
    assert isinstance(time, str)
    datetime.strptime(time, "%Y-%m-%d %H:%M:%S")  # raises if the format differs
    return extra


def _all_text(records: list[dict[str, object]]) -> str:
    """Join every record's message and extra into one string for PII negative checks."""
    return "\n".join(f"{r['message']} {r['extra']!r}" for r in records)


def _two_recipient_email() -> Email:
    """A TEST email to two addresses, used by both the success and failure paths."""
    return Email(
        subject="Subject",
        recipients=[
            NameEmail(name="Jane Doe", email="jane.doe@example.com"),
            NameEmail(name="John Roe", email="john.roe@example.com"),
        ],
        type=EmailType.TEST,
        text="body",
    )


class _FakeFastMail:
    """Stand-in for FastMail so send_many logs without touching a real SMTP server."""

    async def send_message(self, message: object) -> None:
        """No-op send.

        :param message: the message that would be sent; ignored.
        """
        return None


class _FailingFastMail:
    """Stand-in for FastMail whose send always raises, to drive the failure log."""

    async def send_message(self, message: object) -> None:
        """Always fail.

        :param message: the message that would be sent; ignored.
        """
        raise RuntimeError("smtp down")


# EmailType.TEST's value in app/utils/email.py.
_TEST_TYPE = "testing.test_email"


async def test_send_many_logs_recipient_count_not_addresses(monkeypatch, captured_logs):
    """send_many must log how many recipients there are, never the actual addresses (PII)."""
    monkeypatch.setattr(email_module, "_create_fastmail", lambda: _FakeFastMail(), raising=True)

    await send_many([_two_recipient_email()])

    records = _email_records(captured_logs)
    assert [(r["message"], r["level"], _extra_without_time(r)) for r in records] == [
        ("Email send start", "INFO", {"type": _TEST_TYPE, "recipient_count": 2}),  # 2 = len(recipients), not the list
        ("Email send success", "INFO", {"type": _TEST_TYPE, "recipient_count": 2}),
    ]

    # No addresses or display names in either the message or the bound fields.
    joined = _all_text(captured_logs)
    assert "jane.doe@example.com" not in joined
    assert "john.roe@example.com" not in joined
    assert "Jane Doe" not in joined
    assert "John Roe" not in joined


async def test_send_many_logs_failure_with_count_not_addresses(monkeypatch, captured_logs):
    """A failed send logs the failure (with traceback) and the count, never the addresses."""
    monkeypatch.setattr(email_module, "_create_fastmail", lambda: _FailingFastMail(), raising=True)

    await send_many([_two_recipient_email()])

    records = _email_records(captured_logs)
    assert [(r["message"], r["level"], _extra_without_time(r)) for r in records] == [
        ("Email send start", "INFO", {"type": _TEST_TYPE, "recipient_count": 2}),
        # logger.exception logs at ERROR and attaches the caught exception.
        ("Email send fail", "ERROR", {"type": _TEST_TYPE, "recipient_count": 2}),
    ]
    assert records[1]["exception"] is not None

    joined = _all_text(captured_logs)
    assert "jane.doe@example.com" not in joined
    assert "john.roe@example.com" not in joined
    assert "Jane Doe" not in joined
    assert "John Roe" not in joined
