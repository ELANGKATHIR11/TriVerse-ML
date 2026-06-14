"""
F:\3ml project\backend\app\core\security.py

JWT-based token handling + bcrypt password hashing utilities.
All token creation/validation logic lives here so that routes
and dependencies stay thin.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from passlib.context import CryptContext

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration – override via environment variables in production
# ---------------------------------------------------------------------------

SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION_USE_32+_RANDOM_BYTES"  # noqa: S105
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
REFRESH_TOKEN_EXPIRE_DAYS: int = 7

# ---------------------------------------------------------------------------
import bcrypt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Return True if *plain_password* matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Return a bcrypt hash for *password*."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


# ---------------------------------------------------------------------------
# JWT helpers
# ---------------------------------------------------------------------------


def _build_token(
    data: dict[str, Any],
    expires_delta: timedelta,
    *,
    token_type: str = "access",
) -> str:
    """Internal factory – do not call directly outside this module."""
    payload = data.copy()
    now = datetime.now(UTC)
    payload.update(
        {
            "iat": now,
            "exp": now + expires_delta,
            "type": token_type,
        }
    )
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT access token.

    Parameters
    ----------
    data:
        Arbitrary claims to embed (e.g. ``{"sub": username, "role": role}``).
    expires_delta:
        Custom TTL. Defaults to :data:`ACCESS_TOKEN_EXPIRE_MINUTES`.

    Returns
    -------
    str
        Encoded JWT string.
    """
    delta = expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return _build_token(data, delta, token_type="access")


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Create a signed JWT refresh token with a longer TTL.

    Parameters
    ----------
    data:
        Same claims dict as for :func:`create_access_token`.
    expires_delta:
        Custom TTL. Defaults to :data:`REFRESH_TOKEN_EXPIRE_DAYS`.
    """
    delta = expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    return _build_token(data, delta, token_type="refresh")


def decode_token(token: str) -> dict[str, Any] | None:
    """Decode and verify a JWT token.

    Parameters
    ----------
    token:
        Raw JWT string received from the client.

    Returns
    -------
    dict | None
        The decoded payload dict on success, or ``None`` if the token is
        invalid, expired, or tampered with.
    """
    try:
        payload: dict[str, Any] = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except JWTError as exc:
        logger.debug("Token decode failure: %s", exc)
        return None


# ---------------------------------------------------------------------------
# OAuth2 scheme
# ---------------------------------------------------------------------------

from fastapi.security import OAuth2PasswordBearer  # noqa: E402 – after stdlib imports

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")
