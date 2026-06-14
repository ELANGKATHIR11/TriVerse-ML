"""
Pydantic V2 schemas for user management endpoints.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, model_validator

from app.models.user import UserRole


class UserCreate(BaseModel):
    """Payload to register a new user."""

    username: str = Field(..., min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: UserRole = UserRole.VIEWER


class UserUpdate(BaseModel):
    """Partial update for an existing user (all fields optional)."""

    email: EmailStr | None = None
    role: UserRole | None = None
    is_active: bool | None = None


class UserResponse(BaseModel):
    """Public representation of a user – never exposes the password hash."""

    model_config = {"from_attributes": True}

    id: int
    username: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None = None


class UserList(BaseModel):
    """Paginated list of users."""

    users: list[UserResponse]
    total: int
