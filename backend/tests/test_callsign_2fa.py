import pytest
from loguru import logger

from app.api.aro.auth.services.callsign_2fa import callsign_verified
from app.data.repositories.dal import DAL


@pytest.fixture
def captured_logs():
    """Capture the raw message of every loguru record emitted during a test."""
    messages: list[str] = []
    sink_id = logger.add(lambda m: messages.append(m.record["message"]), level="INFO")  # INFO+ only: excludes VERBOSE SQLAlchemy param echo (a separate, console-only vector)
    try:
        yield messages
    finally:
        logger.remove(sink_id)


async def test_callsign_mismatch_logs_level_not_callsign(db_session, captured_logs):
    """On a qualification mismatch the callsign (PII) is never logged, only the level that differs."""
    call_sign = "VE3ABC"
    await DAL.aro_user_callsigns().create(
        {
            "call_sign": call_sign,
            "qual_level_a": True,
            "qual_level_b": True,
            "qual_level_c": True,
            "qual_level_d": True,
            "qual_level_e": True,
        }
    )

    # User supplies a mismatching level A, which triggers the warning path.
    await callsign_verified(qual_levels=(False, True, True, True, True), user_call_sign=call_sign)

    joined = "\n".join(captured_logs)
    assert "qual_level_a" in joined  # the mismatched level is logged
    assert call_sign not in joined  # but the callsign itself is not
