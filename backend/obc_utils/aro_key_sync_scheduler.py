"""Background scheduler that automatically prepares ARO key sync commands before passes."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta

from data.data_wrappers.wrappers import CommsSessionWrapper
from data.enums.transactional import SessionStatus

from obc_utils.aro_key_sync import prepare_keys_for_session

logger = logging.getLogger(__name__)

# How often the scheduler checks for upcoming sessions
_POLL_INTERVAL_SECONDS: int = 60

# How far ahead to look for sessions that need key preparation
_LOOKAHEAD_MINUTES: int = 10


async def run_key_sync_scheduler() -> None:
    """
    Periodically check for scheduled sessions and prepare unsynced ARO keys.

    Runs as a background asyncio task inside the FastAPI lifespan.
    """
    logger.info(
        "ARO key sync scheduler started (poll every %ds, lookahead %dmin)",
        _POLL_INTERVAL_SECONDS,
        _LOOKAHEAD_MINUTES,
    )

    while True:
        try:
            _check_and_prepare()
        except Exception:
            logger.exception("Error in ARO key sync scheduler loop")

        await asyncio.sleep(_POLL_INTERVAL_SECONDS)


def _check_and_prepare() -> None:
    """Synchronous check: find upcoming SCHEDULED sessions and prepare keys for them."""
    now = datetime.now()
    horizon = now + timedelta(minutes=_LOOKAHEAD_MINUTES)

    session_wrapper = CommsSessionWrapper()
    all_sessions = session_wrapper.get_all()

    upcoming = [
        s
        for s in all_sessions
        if s.status == SessionStatus.SCHEDULED and s.start_time <= horizon and s.start_time > now
    ]

    if not upcoming:
        return

    for session in upcoming:
        logger.info(
            "Session %s starts at %s — preparing ARO keys",
            session.id,
            session.start_time.isoformat(),
        )
        try:
            cmd_ids = prepare_keys_for_session(session.id)
            if cmd_ids:
                logger.info(
                    "Prepared %d key sync command(s) for session %s",
                    len(cmd_ids),
                    session.id,
                )
        except Exception:
            logger.exception("Failed to prepare keys for session %s", session.id)
