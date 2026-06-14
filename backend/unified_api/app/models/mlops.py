"""
F:\3ml project\backend\app\models\mlops.py

MLOps ORM models: ModelRegistry, ModelVersion, OptunaTrialRecord.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Enum as SAEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ModelStage(str, enum.Enum):
    STAGING = "staging"
    PRODUCTION = "production"
    ARCHIVED = "archived"


class ModelRegistry(Base):
    """Central registry of trained models promoted for serving."""

    __tablename__ = "model_registry"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(256), nullable=False, index=True)
    task_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)
    stage = Column(
        SAEnum(ModelStage, name="modelstage", native_enum=False),
        nullable=False,
        default=ModelStage.STAGING,
    )
    mlflow_model_uri = Column(String(512), nullable=True)
    mlflow_run_id = Column(String(256), nullable=True)
    experiment_id = Column(
        Integer,
        ForeignKey("experiments.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    creator = relationship(
        "User", back_populates="model_registries", foreign_keys=[created_by]
    )
    experiment = relationship("Experiment", back_populates="model_registries")
    versions = relationship(
        "ModelVersion",
        back_populates="registry",
        cascade="all, delete-orphan",
    )
    prediction_logs = relationship(
        "PredictionLog",
        back_populates="model",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ModelRegistry id={self.id} name={self.name!r} stage={self.stage.value!r}>"
        )


class ModelVersion(Base):
    """Versioned artifact for a registered model."""

    __tablename__ = "model_versions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    registry_id = Column(
        Integer,
        ForeignKey("model_registry.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version = Column(String(32), nullable=False)
    file_path = Column(String(512), nullable=True)
    metrics_json = Column(JSON, nullable=True)
    params_json = Column(JSON, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    registry = relationship("ModelRegistry", back_populates="versions")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ModelVersion registry_id={self.registry_id} "
            f"version={self.version!r} active={self.is_active}>"
        )


class OptunaTrialRecord(Base):
    """Persisted record of a single Optuna hyperparameter-search trial."""

    __tablename__ = "optuna_trial_records"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    experiment_id = Column(
        Integer,
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    study_name = Column(String(256), nullable=False)
    trial_number = Column(Integer, nullable=False)
    params_json = Column(JSON, nullable=True)
    value = Column(Float, nullable=True)
    state = Column(String(32), nullable=False, default="running")
    duration_sec = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="optuna_trials")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<OptunaTrialRecord experiment_id={self.experiment_id} "
            f"trial={self.trial_number} value={self.value}>"
        )
