"""
F:\3ml project\backend\app\models\audit.py

Audit-related ORM models: AuditLog, ChatHistory.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class AuditLog(Base):
    """Immutable record of every significant platform action."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action = Column(String(128), nullable=False, index=True)
    resource = Column(String(128), nullable=False)
    resource_id = Column(String(128), nullable=True)
    details_json = Column(JSON, nullable=True)
    ip_address = Column(String(64), nullable=True)
    user_agent = Column(String(512), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="audit_logs")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<AuditLog id={self.id} action={self.action!r} "
            f"resource={self.resource!r}>"
        )


class ChatHistory(Base):
    """Persistent LLM-chat message store, keyed by session."""

    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = Column(String(128), nullable=False, index=True)
    role = Column(String(16), nullable=False)  # 'user' | 'assistant' | 'system'
    content = Column(Text, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    user = relationship("User", back_populates="chat_history")

    def __repr__(self) -> str:  # pragma: no cover
        preview = (self.content or "")[:40]
        return (
            f"<ChatHistory id={self.id} session={self.session_id!r} "
            f"role={self.role!r} content={preview!r}>"
        )
