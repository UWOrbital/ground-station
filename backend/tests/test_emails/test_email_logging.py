import pytest
from loguru import logger
from pydantic import NameEmail

import app.utils.email as email_module
from app.utils.email import Email, EmailType, send_many


@pytest.fixture
def captured_logs():
    """Capture the raw message of every loguru record emitted during a test."""
    messages: list[str] = []
    sink_id = logger.add(lambda m: messages.append(m.record["message"]), level="INFO")  # INFO+ only: excludes VERBOSE SQLAlchemy param echo (a separate, console-only vector)
    try:
        yield messages
    finally:
        logger.remove(sink_id)


class _FakeFastMail:
    """Stand-in for FastMail so send_many logs without touching a real SMTP server."""

    async def send_message(self, message: object) -> None:
        """No-op send.

        :param message: the message that would be sent; ignored.
        """
        return None


async def test_send_many_logs_recipient_count_not_addresses(monkeypatch, captured_logs):
    """send_many must log how many recipients there are, never the actual addresses (PII)."""
    monkeypatch.setattr(email_module, "_create_fastmail", lambda: _FakeFastMail(), raising=True)

    email = Email(
        subject="Subject",
        recipients=[
            NameEmail(name="Jane Doe", email="jane.doe@example.com"),
            NameEmail(name="John Roe", email="john.roe@example.com"),
        ],
        type=EmailType.TEST,
        text="body",
    )

    await send_many([email])

    joined = "\n".join(captured_logs)
    assert "EMAIL SEND START" in joined
    assert "EMAIL SEND SUCCESS" in joined
    assert "Recipients: 2" in joined  # count, not the list
    assert "jane.doe@example.com" not in joined
    assert "john.roe@example.com" not in joined
