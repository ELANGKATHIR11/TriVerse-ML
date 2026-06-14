"""
F:\\3ml project\\backend\\app\\api\\routes\\auth.py

Authentication router – login, refresh, logout, and current-user endpoints.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, UTC

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
)
from app.models.audit import AuditLog
from app.models.user import User, UserRole
from app.schemas.auth import Token, RefreshRequest
from app.schemas.user import UserResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _log_audit(
    db: AsyncSession,
    *,
    user_id: int | None,
    action: str,
    resource: str,
    resource_id: str | None = None,
    details: dict | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> None:
    """Persist an audit-log entry asynchronously."""
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
        details_json=details or {},
        ip_address=ip_address,
        user_agent=user_agent,
        created_at=datetime.now(UTC),
    )
    db.add(entry)
    await db.flush()


def _client_ip(request: Request) -> str:
    """Extract real client IP from request headers or connection info."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=Token,
    summary="Login with username and password",
    description="Accepts OAuth2PasswordRequestForm credentials and returns JWT access + refresh tokens.",
    status_code=status.HTTP_200_OK,
)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticate with username/password and receive JWT tokens."""
    # Fetch user by username
    result = await db.execute(select(User).where(User.username == form_data.username))
    user: User | None = result.scalar_one_or_none()

    if user is None or not verify_password(form_data.password, user.hashed_password):
        await _log_audit(
            db,
            user_id=None,
            action="login_failed",
            resource="auth",
            details={"username": form_data.username, "reason": "invalid_credentials"},
            ip_address=_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated. Contact an administrator.",
        )

    token_data = {"sub": user.username, "role": user.role.value, "user_id": user.id}

    access_token = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(
        data=token_data,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    # Update last_login timestamp
    await db.execute(
        update(User)
        .where(User.id == user.id)
        .values(last_login=datetime.now(UTC))
    )

    await _log_audit(
        db,
        user_id=user.id,
        action="login_success",
        resource="auth",
        resource_id=str(user.id),
        details={"username": user.username, "role": user.role.value},
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )

    logger.info("User %r logged in from %s", user.username, _client_ip(request))
    return Token(access_token=access_token, token_type="bearer", refresh_token=refresh_token)


# ---------------------------------------------------------------------------
# POST /auth/refresh
# ---------------------------------------------------------------------------


@router.post(
    "/refresh",
    response_model=Token,
    summary="Refresh access token using a refresh token",
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    payload: RefreshRequest,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Exchange a valid refresh token for a new access + refresh token pair."""
    decoded = decode_token(payload.refresh_token)
    if decoded is None or decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str | None = decoded.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token payload",
        )

    result = await db.execute(select(User).where(User.username == username))
    user: User | None = result.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    token_data = {"sub": user.username, "role": user.role.value, "user_id": user.id}
    new_access = create_access_token(
        data=token_data,
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    new_refresh = create_refresh_token(
        data=token_data,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    await _log_audit(
        db,
        user_id=user.id,
        action="token_refreshed",
        resource="auth",
        resource_id=str(user.id),
    )

    return Token(access_token=new_access, token_type="bearer", refresh_token=new_refresh)


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------


@router.post(
    "/logout",
    summary="Logout – invalidate session (logs audit event)",
    status_code=status.HTTP_200_OK,
)
async def logout(
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Log an audit event for the logout action.
    
    Note: JWT tokens are stateless; this endpoint logs the event and
    the frontend should discard the tokens locally. For production use,
    implement a token denylist with Redis.
    """
    await _log_audit(
        db,
        user_id=current_user.id,
        action="logout",
        resource="auth",
        resource_id=str(current_user.id),
        details={"username": current_user.username},
        ip_address=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    logger.info("User %r logged out", current_user.username)
    return {"message": "Successfully logged out. Please discard your tokens."}


# ---------------------------------------------------------------------------
# GET /auth/me
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the currently authenticated user",
    status_code=status.HTTP_200_OK,
)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)
