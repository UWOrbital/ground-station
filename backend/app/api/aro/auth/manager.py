"""
manager.py

The fastapi-users integration seam. The UserManager subclass and the connection to AROUserDatabaseAdapter.

router.py and aro_session.py never import from here directly.
"""

from collections.abc import AsyncGenerator
from typing import override
from uuid import UUID

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from loguru import logger
from pydantic import NameEmail

from app.api.aro.auth.adapter import AROUserDatabaseAdapter, AROUserRecord
from app.api.aro.auth.services.verification_email import send_verification_email
from app.config.env_settings.backend_config import settings
from app.utils.email import Email, EmailType, render_email_template, send


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

    @override
    async def on_after_forgot_password(self, user: AROUserRecord, token: str, request: Request | None = None) -> None:
        """
        Called after a user requests a password reset.

        :param user: the user requesting a password reset
        :param token: the reset token
        :param request: the incoming request, if any
        """
        name = user.first_name
        if user.last_name:
            name += f" {user.last_name}"

        email = Email(
            subject="Reset your UWOrbital ARO password",
            recipients=[NameEmail(name, user.email)],
            type=EmailType.PASSWORD_RESET,
            text=(
                f"Hi {name},\n\nYour ARO password reset token is:\n{token}\n\n"
                f"If you didn't request this, ignore this email."
            ),
            html=render_email_template("reset_password.html", name=name, token=token),
        )
        await send(email)

    @override
    async def on_after_request_verify(self, user: AROUserRecord, token: str, request: Request | None = None) -> None:
        """
        Email the user the code that confirms they own their address.

        Called by fastapi-users once a verification token has been minted.

        :param user: the ARO user who asked for a verification token.
        :param token: the verification token to hand to the user.
        :param request: optional FastAPI request that triggered the operation.
        """
        await send_verification_email(user.email, token)

    @override
    async def on_after_verify(self, user: AROUserRecord, request: Request | None = None) -> None:
        """
        Record that the user confirmed their email address.

        The `is_verified` flag itself is already persisted by fastapi-users before
        this hook runs, so the handler only announces the state change.

        :param user: the now-verified ARO user.
        :param request: optional FastAPI request that triggered the operation.
        """
        logger.info(f"ARO email verified | User id: {user.id}")


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
