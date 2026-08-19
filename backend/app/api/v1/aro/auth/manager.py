"""
manager.py

The fastapi-users integration seam. The UserManager subclass and the connection to AROUserDatabaseAdapter.

router.py and aro_session.py never import from here directly.
"""

from collections.abc import AsyncGenerator
from uuid import UUID

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin

from app.api.v1.aro.auth.adapter import AROUserDatabaseAdapter, AROUserRecord
from app.config.env_settings.backend_config import settings


class AROUserManager(UUIDIDMixin, BaseUserManager[AROUserRecord, UUID]):
    """
    fastapi-users UserManager for AROUserRecord
    """

    reset_password_token_secret = settings.auth.jwt_secret
    verification_token_secret = settings.auth.jwt_secret

    async def on_after_register(self, user: AROUserRecord, request: Request | None = None) -> None:
        """Called after a new user row is committed."""
        # TODO: Wire up an after-registeration hook the day we need one
        pass


async def get_user_db() -> AsyncGenerator[AROUserDatabaseAdapter, None]:
    """
    Dependency yielding the DB adapter.

    :returns: yields AROUserDatabaseAdapter
    """
    yield AROUserDatabaseAdapter()


async def get_user_manager(
    user_db: AROUserDatabaseAdapter = Depends(get_user_db),
) -> AsyncGenerator[AROUserManager, None]:
    """
    Dependency yielding the UserManager.

    :param user_db: injected via get_user_db
    :returns: yields AROUserManager
    """
    yield AROUserManager(user_db)
