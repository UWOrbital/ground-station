"""
aro_session.py

Everything fastapi-users does NOT provide.
1. A short-lived, stateless accesstoken (raw PyJWT, not JWTStrategy — see note above)
2. A long-lived, DB-backed, rotating refresh token. 

Deliberately has no import from manager.py or adapter.py. This file doesn't need to know fastapi-users exists.
"""

import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config.env_settings.backend_config import settings
from app.data.data_wrappers.wrappers import AROUserAuthTokenWrapper, AROUsersWrapper
from app.data.models.aro_user_models import AROUsers

# Short on purpose: an access token can't be revoked once issued (unlike the
# refresh token below), so its lifetime IS the blast radius if one leaks.
ACCESS_TOKEN_LIFETIME = timedelta(minutes=10)

# This, not the access token, is the real session length a user experiences.
REFRESH_TOKEN_LIFETIME = timedelta(days=14)

_bearer_scheme = HTTPBearer(auto_error=False)


def _hash_refresh_token(raw_token: str) -> str:
    """
    Hash a refresh token before it ever touches the database.

    Same reasoning as password storage: a stolen row shouldn't be a
    directly-usable session.
    """
    return hashlib.sha256(raw_token.encode()).hexdigest()


def create_access_token(user: AROUsers) -> str:
    """
    Mint a short-lived JWT carrying just enough to identify the user.

    Verified by signature + exp claim alone, no DB hit — that statelessness
    is *specifically* about not needing a revocation check. Fetching the
    user by primary key afterward (see get_current_user) is a separate,
    cheap concern and doesn't undermine it.

    :param user: the authenticated user to encode a token for.
    :return: an encoded JWT access token.
    """
    # TODO: build the pa need "sub"(str(user.id))
    # and "exp" (datetime.now(UTC) + ACCESS_TOKEN_LIFETIME). jwt.encode wants
    # exp as a datetime he pyjwt docs for which.
    raise NotImplementedError


def rotate_refresh_token(raw_token: str) -> tuple[str, AROUsers]:
    """
    Exchange one refresh token for the next one in its family.

    :param raw_token: the value read from the client's refresh cookie.
    :return: (new raw refresh token, the authenticated AROUsers row).
    :raises HTTPException: 401 refresh_token_invalid — unknown, expired, or
        already-rotated (reuse) token. Deliberately one generic message to
        the client either way; only the server-side branch differs.
    """
    token_hash = _hash_refresh_token(raw_token)

    # TODO: look up the row by token_hash via AROUserAuthTokenWrapper.
    # If nothing matches, raise the 401 immediately — nothing to rotate.
    existing = ...  # placeholder, replace with the real lookup

    if existing.rotated_at is not None:
        # Reuse detected. The only way an already-superseded token comes
        # back is if two parties hold a copy: the real user (who already
        # rotated past it) and whoever stole it earlier. We can't tell
        # which caller *this* request is, so we don't try — kill the whole
        # family, including the legitimate session, and force a real login.
        # TODO: revoke_family(existing.family_id)
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Session invalid.", "code": "refresh_token_invalid"},
        )

    if existing.revoked_at is not None or existing.expiry < datetime.now(UTC):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Session expired.", "code": "refresh_token_invalid"},
        )

    # Race to flag here: two near-simultaneous /refresh calls (e.g. a flaky
    # reload racing a background refresh) can both read rotated_at=None
    # before either writes it, and both believe they're the legitimate
    # rotation. TODO: figure out how to make only one of them win — look at
    # a conditional UPDATE (`WHERE rotated_at IS NULL`) rather than a plain
    # read-then-write, and think about what the loser should see.

    # TODO: mark existing.rotated_at = datetime.now(UTC) and persist it.
    # This row isn't "canceled" at this point — it stays around on purpose,
    # as the tripwire the reuse check above depends on.

    # TODO: new_raw = issue_refresh_token(existing.user_id, family_id=existing.family_id)
    # TODO: fetch the AROUsers row for existing.user_id via AROUsersWrapper
    # TODO: return (new_raw, user)
    raise NotImplementedError


def revoke_family(family_id: UUID) -> None:
    """
    Invalidate every refresh token descended from one login.

    Used by the reuse-detection branch above; also the natural building
    block for a future "log out of all devices" feature, if that ever
    becomes a real request rather than a hypothetical one.

    :param family_id: the family to kill.
    """
    # TODO: bulk-set revoked_at = now on every AROUserAuthToken row with
    # this family_id, regardless of their current rotated_at value.
    raise NotImplementedError


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AROUsers:
    """
    Resolve the bearer access token on a request to an AROUsers row.

    Every protected ARO route depends on this. The three failure branches
    below map directly onto the 401-code table: the frontend's eventual
    interceptor needs to tell "silently retry via /refresh" apart from
    "give up, log out" — a single generic 401 can't carry that distinction.

    :param credentials: the parsed Authorization header, or None if absent.
    :return: the authenticated AROUsers row.
    :raises HTTPException: 401, with a `code` distinguishing why.
    """
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Not authenticated.", "code": "missing_token"},
        )

    # TODO: jwt.decode(credentials.credentials, settings.auth.jwt_secret_key,
    # algorithms=["HS256"]) inside a try/except. On any decode/signature
    # failure -> code "invalid_token". On jwt.ExpiredSignatureError
    # specifically -> code "access_token_expired". These must NOT share a
    # code — that's the one case the interceptor should auto-retry via
    # /refresh, the other means don't bother, something's wrong.

    # TODO: pull "sub" out of the decoded payload, AROUsersWrapper().get_by_id(...)
    # and return it.
    raise NotImplementedError
