"""MCC endpoints for managing satellite passes and key preparation."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from obc_utils.aro_key_sync import prepare_keys_for_session

passes_router = APIRouter(tags=["MCC", "Passes"])


@passes_router.post("/{session_id}/prepare-keys")
async def prepare_keys(session_id: UUID) -> dict[str, str | int]:
    """
    Prepare all unsynced active ARO keys for the given comms session.

    This queues CMD_ARO_KEY_SYNC commands into the transactional.commands table
    so they will be uplinked during the next pass. Can also be triggered
    automatically by the pre-pass scheduler.

    :param session_id: UUID of the CommsSession to prepare keys for.
    :return: Summary of how many commands were prepared.
    """
    try:
        command_ids = prepare_keys_for_session(session_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    return {
        "message": f"Prepared {len(command_ids)} key sync command(s)",
        "count": len(command_ids),
    }
