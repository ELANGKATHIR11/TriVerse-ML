"""
Pydantic V2 schemas for JWT authentication flows.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Token(BaseModel):
    """Full token response returned after successful login."""

    access_token: str
    token_type: str = "bearer"
    refresh_token: str


class TokenData(BaseModel):
    """Decoded payload embedded inside a JWT."""

    username: str | None = None
    role: str | None = None


class LoginRequest(BaseModel):
    """Request body for the login endpoint."""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)


class RefreshRequest(BaseModel):
    """Request body for the token-refresh endpoint."""

    refresh_token: str
