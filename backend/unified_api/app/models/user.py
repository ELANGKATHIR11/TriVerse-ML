"""
User ORM model with role-based access control.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    """Platform roles used for RBAC."""

    ADMIN = "admin"
    ML_ENGINEER = "ml_engineer"
    RESEARCHER = "researcher"
    VIEWER = "viewer"


class User(Base):
    """Registered platform user."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(
        SAEnum(UserRole, name="userrole", native_enum=False),
        nullable=False,
        default=UserRole.VIEWER,
    )
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    last_login = Column(DateTime, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    datasets = relationship(
        "Dataset",
        back_populates="creator",
        foreign_keys="Dataset.created_by",
        lazy="select",
    )
    experiments = relationship(
        "Experiment",
        back_populates="creator",
        foreign_keys="Experiment.created_by",
        lazy="select",
    )
    model_registries = relationship(
        "ModelRegistry",
        back_populates="creator",
        foreign_keys="ModelRegistry.created_by",
        lazy="select",
    )
    prediction_logs = relationship(
        "PredictionLog",
        back_populates="user",
        lazy="select",
    )
    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
        lazy="select",
    )
    chat_history = relationship(
        "ChatHistory",
        back_populates="user",
        lazy="select",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<User id={self.id} username={self.username!r} role={self.role.value!r}>"
