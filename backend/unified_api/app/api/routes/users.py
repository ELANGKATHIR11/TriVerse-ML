"""
F:\\3ml project\\backend\\app\\api\\routes\\users.py

Users management router – CRUD with role-based access control.
"""

from __future__ import annotations

import logging
from datetime import datetime, UTC

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user, require_role
from app.core.security import get_password_hash
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserList, UserResponse, UserUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["Users"])


# ---------------------------------------------------------------------------
# GET /users  (Admin | ML_Engineer)
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=UserList,
    summary="List all users (paginated)",
    status_code=status.HTTP_200_OK,
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum records to return"),
    current_user: User = Depends(require_role(UserRole.ADMIN, UserRole.ML_ENGINEER)),
    db: AsyncSession = Depends(get_db),
) -> UserList:
    """Return a paginated list of all registered users."""
    total_result = await db.execute(select(func.count()).select_from(User))
    total: int = total_result.scalar_one()

    users_result = await db.execute(
        select(User).order_by(User.created_at.desc()).offset(skip).limit(limit)
    )
    users = list(users_result.scalars().all())

    return UserList(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
    )


# ---------------------------------------------------------------------------
# POST /users  (Admin only)
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=UserResponse,
    summary="Create a new user (Admin only)",
    status_code=status.HTTP_201_CREATED,
)
async def create_user(
    payload: UserCreate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account. Only admins may call this endpoint."""
    # Check for duplicate username
    existing_username = await db.execute(
        select(User).where(User.username == payload.username)
    )
    if existing_username.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Username '{payload.username}' is already taken.",
        )

    # Check for duplicate email
    existing_email = await db.execute(
        select(User).where(User.email == payload.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email '{payload.email}' is already registered.",
        )

    new_user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
        is_active=True,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    logger.info("Admin %r created user %r with role %r", current_user.username, new_user.username, new_user.role.value)
    return UserResponse.model_validate(new_user)


# ---------------------------------------------------------------------------
# GET /users/{user_id}
# ---------------------------------------------------------------------------


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get a specific user by ID",
    status_code=status.HTTP_200_OK,
)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Retrieve a user by their ID.
    - Admins and ML Engineers can view any user.
    - Other roles may only view themselves.
    """
    if current_user.id != user_id and current_user.role not in (
        UserRole.ADMIN,
        UserRole.ML_ENGINEER,
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile.",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found.",
        )
    return UserResponse.model_validate(user)


# ---------------------------------------------------------------------------
# PUT /users/{user_id}  (Admin or self)
# ---------------------------------------------------------------------------


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update a user (Admin or self)",
    status_code=status.HTTP_200_OK,
)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """
    Update a user's email, role, or active status.
    - Admins can update any user's fields including role and active status.
    - Non-admin users can only update their own email.
    """
    is_admin = current_user.role == UserRole.ADMIN

    # Non-admins can only update themselves
    if not is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile.",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found.",
        )

    update_values: dict = {"updated_at": datetime.now(UTC)}

    if payload.email is not None:
        # Check email uniqueness
        conflict = await db.execute(
            select(User).where(User.email == payload.email, User.id != user_id)
        )
        if conflict.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Email '{payload.email}' is already in use.",
            )
        update_values["email"] = payload.email

    # Only admins can change role and active status
    if is_admin:
        if payload.role is not None:
            update_values["role"] = payload.role
        if payload.is_active is not None:
            update_values["is_active"] = payload.is_active

    await db.execute(update(User).where(User.id == user_id).values(**update_values))
    await db.flush()

    updated = await db.execute(select(User).where(User.id == user_id))
    return UserResponse.model_validate(updated.scalar_one())


# ---------------------------------------------------------------------------
# DELETE /users/{user_id}  (Admin only)
# ---------------------------------------------------------------------------


@router.delete(
    "/{user_id}",
    summary="Delete a user (Admin only)",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Permanently delete a user account. Admins cannot delete themselves."""
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot delete their own account.",
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found.",
        )

    await db.delete(user)
    logger.info("Admin %r deleted user %r (id=%d)", current_user.username, user.username, user_id)


# ---------------------------------------------------------------------------
# PUT /users/{user_id}/role  (Admin only)
# ---------------------------------------------------------------------------


@router.put(
    "/{user_id}/role",
    response_model=UserResponse,
    summary="Change a user's role (Admin only)",
    status_code=status.HTTP_200_OK,
)
async def update_user_role(
    user_id: int,
    role: UserRole,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Update the RBAC role for a specific user."""
    result = await db.execute(select(User).where(User.id == user_id))
    user: User | None = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found.",
        )

    await db.execute(
        update(User)
        .where(User.id == user_id)
        .values(role=role, updated_at=datetime.now(UTC))
    )
    await db.flush()

    updated = await db.execute(select(User).where(User.id == user_id))
    refreshed = updated.scalar_one()
    logger.info(
        "Admin %r changed user %r role to %r",
        current_user.username,
        refreshed.username,
        role.value,
    )
    return UserResponse.model_validate(refreshed)
