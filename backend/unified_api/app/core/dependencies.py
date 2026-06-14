"""
F:\3ml project\backend\app\core\dependencies.py

FastAPI dependency-injection helpers for authentication and
role-based access control (RBAC).
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Coroutine
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_token, oauth2_scheme
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Token → User resolution
# ---------------------------------------------------------------------------

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the JWT bearer token to an ORM :class:`~app.models.user.User`.

    Raises :class:`~fastapi.HTTPException` 401 if the token is absent,
    invalid, expired, or does not correspond to any user in the database.
    """
    payload = decode_token(token)
    if payload is None:
        raise _CREDENTIALS_EXCEPTION

    username: str | None = payload.get("sub")
    if username is None:
        raise _CREDENTIALS_EXCEPTION

    result = await db.execute(select(User).where(User.username == username))
    user: User | None = result.scalar_one_or_none()

    if user is None:
        raise _CREDENTIALS_EXCEPTION

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Like :func:`get_current_user` but additionally rejects inactive accounts.

    Raises :class:`~fastapi.HTTPException` 403 if the user's
    ``is_active`` flag is ``False``.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account",
        )
    return current_user


# ---------------------------------------------------------------------------
# Role-based access control
# ---------------------------------------------------------------------------


def require_role(
    *roles: UserRole,
) -> Callable[..., Coroutine[Any, Any, User]]:
    """Return a FastAPI dependency that enforces membership in *roles*.

    Usage::

        @router.delete("/users/{user_id}")
        async def delete_user(
            user_id: int,
            current_user: User = Depends(require_role(UserRole.ADMIN)),
        ):
            ...

    Multiple roles can be passed – any match is sufficient::

        Depends(require_role(UserRole.ADMIN, UserRole.ML_ENGINEER))

    Raises :class:`~fastapi.HTTPException` 403 if the authenticated user's
    role is not in *roles*.
    """
    allowed: frozenset[UserRole] = frozenset(roles)

    async def _check_role(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied. Required role(s): "
                    f"{', '.join(r.value for r in allowed)}. "
                    f"Your role: {current_user.role.value}."
                ),
            )
        return current_user

    return _check_role
