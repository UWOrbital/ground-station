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

ACCESS_TOKEN_LIFETIME = timedelta(minutes=10)
REFRESH_TOKEN_LIFETIME = timedelta(days=14)  # real session length

_bearer_scheme = HTTPBearer(auto_error=False)

token_wrapper = AROUserAuthTokenWrapper()


def _hash_refresh_token(raw_token: str) -> str:
    """
    Hash a refresh token before it ever touches the database.

    :param raw_token: the raw refresh token value.
    :return: a hex-encoded SHA-256 digest of the token.
    """
    return hashlib.sha256(raw_token.encode()).hexdigest()


def create_access_token(user: AROUsers) -> tuple[str, datetime]:
    """
    Mint a short-lived JWT carrying just enough to identify the user.

    :param user: the authenticated user to encode a token for.
    :return: an encoded JWT access token.
    """
    expiry = datetime.now(UTC) + ACCESS_TOKEN_LIFETIME
    payload = {
        "sub": str(user.id),
        "exp": expiry,
    }
    encoded_jwt = jwt.encode(payload, settings.auth.jwt_secret, algorithm="HS256")
    return encoded_jwt, expiry


def issue_refresh_token(user_id: UUID, family_id: UUID | None = None) -> str:
    """
    Create a new refresh-token row, return the raw (unhashed) value.

    :param user_id: owner of the new token.
    :param family_id: pass the existing family when rotating a session
    :return: the raw token (keep it SECURE)
    """
    raw_token = secrets.token_urlsafe(32)
    family_id = family_id or uuid4()

    token_wrapper = AROUserAuthTokenWrapper()
    token_wrapper.create(
        {
            "token_hash": _hash_refresh_token(raw_token),
            "family_id": family_id,
            "user_id": user_id,
            "expiry": datetime.now(UTC) + REFRESH_TOKEN_LIFETIME,
            "rotated_at": None,
            "revoked_at": None,
        }
    )

    return raw_token


def rotate_refresh_token(raw_token: str) -> tuple[str, AROUsers]:
    """
    Exchange one refresh token for the next one in its family.

    :param raw_token: the value read from the client's refresh cookie.
    :return: (new raw refresh token, the authenticated AROUsers row).
    :raises HTTPException: 401 refresh_token_invalid
    """
    token_hash = _hash_refresh_token(raw_token)

    existing = token_wrapper.get_first_by(token_hash=token_hash)
    if existing is None:
        # Unknown token
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Session invalid.", "code": "refresh_token_invalid"},
        )

    if existing.rotated_at is not None:
        # Reuse detected -> kill all descendants
        revoke_family(existing.family_id)

        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Session invalid.", "code": "refresh_token_invalid"},
        )

    if existing.revoked_at is not None or existing.expiry < datetime.now(UTC):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Session expired.", "code": "refresh_token_invalid"},
        )

    if not token_wrapper.claim_rotation(existing.id):
        # something else rotated this row, so close with 401
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Session invalid.", "code": "refresh_token_invalid"},
        )

    new_raw = issue_refresh_token(existing.user_id, existing.family_id)
    user = AROUsersWrapper().get_by_id(existing.user_id)

    return (new_raw, user)


def revoke_token(refresh_token: str | None) -> None:
    """
    Invalidate a single refresh token.

    :param refresh_token: str | None
    :returns: None
    """
    if refresh_token is not None:
        token_hash = _hash_refresh_token(refresh_token)
        existing = token_wrapper.get_first_by(token_hash=token_hash)
        if existing is not None:
            token_wrapper.update(existing.id, {"revoked_at": datetime.now(UTC)})


def revoke_family(family_id: UUID) -> int:
    """
    Invalidate every refresh token descended from one login.

    :param family_id: the family to kill
    :return revoked_rows: number of rows revoked
    """
    return AROUserAuthTokenWrapper().revoke_by_family_id(family_id)


async def get_user_by_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AROUsers:
    """
    Resolve the bearer access token on a request to an AROUsers row. Every protected ARO route depends on this.

    :param credentials: the parsed Authorization header, or None if absent.
    :return the authenticated AROUsers row.
    :raises HTTPException: 401 with a `code` distinguishing why.
    """
    if credentials is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Not authenticated.", "code": "missing_token"},
        )

    try:
        payload = jwt.decode(credentials.credentials, settings.auth.jwt_secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Token expired.", "code": "access_token_expired"},
        ) from None
    except jwt.InvalidTokenError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid token.", "code": "invalid_token"},
        ) from None

    raw_user_id = payload.get("sub")
    if not raw_user_id:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid token payload.", "code": "invalid_token"},
        )

    try:
        user = AROUsersWrapper().get_by_id(UUID(raw_user_id))
    except ValueError:
        # UUID(raw_user_id) raises ValueError if "sub" wasn't a valid UUID
        # get_by_id raises its own plain ValueError when no row matches
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Invalid token.", "code": "invalid_token"},
        ) from None

    return user


async def require_superuser(user: AROUsers = Depends(get_user_by_token)) -> AROUsers:
    """
    Asserts the user in question is a superuser.

    :param user: AROUsers
    :returns: AROUsers if user is a superuser
    """
    if not user.is_superuser:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            detail={"message": "Superuser permissions are required.", "code": "require_superuser"},
        )
    return user
