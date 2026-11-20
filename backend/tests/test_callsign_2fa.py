import pytest
from loguru import logger

from app.api.aro.auth.services.callsign_2fa import callsign_verified
from app.data.repositories.dal import DAL


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

    mismatches = [r for r in captured_logs if r["message"] == "Callsign qualification mismatch"]
    # Exactly one warning, for level A only: qual_level is the bare letter, chr(ord('a') + 0).
    assert mismatches == [
        {"message": "Callsign qualification mismatch", "level": "WARNING", "extra": {"qual_level": "a"}}
    ]

    # The callsign itself is in neither the message nor the bound fields.
    joined = "\n".join(f"{r['message']} {r['extra']!r}" for r in captured_logs)
    assert call_sign not in joined
