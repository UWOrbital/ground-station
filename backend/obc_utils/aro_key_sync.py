"""Service for preparing ARO key sync commands before a satellite pass."""

from __future__ import annotations

import logging
from uuid import UUID

from data.data_wrappers.wrappers import AROUserKeyWrapper, CommandsWrapper
from data.database.engine import get_db_session
from data.tables.transactional_tables import CommsSession

logger = logging.getLogger(__name__)

_ARO_KEY_SYNC_MAIN_COMMAND_ID: int = 13


def prepare_keys_for_session(session_id: UUID) -> list[UUID]:
    """
    Query unsynced active ARO keys, build CMD_ARO_KEY_SYNC commands, and persist
    them to the transactional.commands table for the given comms session.

    :param session_id: The comms session these commands belong to.
    :type session_id: UUID
    :return: UUIDs of the created command records.
    :rtype: list[UUID]
    """
    user_keys = AROUserKeyWrapper()
    commands = CommandsWrapper()

    # Find all unsynced active keys
    unsynced_keys = user_keys.get_all_by(is_active=True, synced_to_obc_at=None)

    if not unsynced_keys:
        logger.info("No unsynced active ARO keys to prepare for session %s", session_id)
        return []

    # Verify the session exists
    with get_db_session() as session:
        comms_session = session.get(CommsSession, session_id)
        if not comms_session:
            raise ValueError(f"CommsSession with ID {session_id} not found.")

    command_ids: list[UUID] = []

    for aro_key in unsynced_keys:
        # Persist as a transactional command record
        created = commands.create(
            {
                "type_": _ARO_KEY_SYNC_MAIN_COMMAND_ID,
                "params": aro_key.key_data,  # hex string
                "user_id": aro_key.user_id,
                "status": "PENDING",
            }
        )
        command_ids.append(created.id)
        logger.info(
            "Prepared ARO key sync command %s for key %s (user %s)",
            created.id,
            aro_key.id,
            aro_key.user_id,
        )

    logger.info(
        "Prepared %d ARO key sync command(s) for session %s",
        len(command_ids),
        session_id,
    )
    return command_ids
