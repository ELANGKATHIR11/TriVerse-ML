"""
F:\3ml project\backend\app\models\inference.py

Inference-related ORM models: PredictionLog.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base


class PredictionLog(Base):
    """Audit trail for individual inference requests."""

    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    model_id = Column(
        Integer,
        ForeignKey("model_registry.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    input_json = Column(JSON, nullable=True)
    output_json = Column(JSON, nullable=True)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    model = relationship("ModelRegistry", back_populates="prediction_logs")
    user = relationship("User", back_populates="prediction_logs")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<PredictionLog id={self.id} model_id={self.model_id} "
            f"latency={self.latency_ms}ms>"
        )
