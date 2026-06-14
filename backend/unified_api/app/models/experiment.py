"""
F:\3ml project\backend\app\models\experiment.py

Experiment-related ORM models:
  - Experiment
  - ExperimentMetrics
  - TrainingSession
  - PipelineStatus
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    JSON,
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


class ExperimentStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Experiment(Base):
    """ML experiment tracking entity."""

    __tablename__ = "experiments"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(256), nullable=False, index=True)
    task_type = Column(String(64), nullable=False)
    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status = Column(
        SAEnum(ExperimentStatus, name="experimentstatus", native_enum=False),
        nullable=False,
        default=ExperimentStatus.PENDING,
    )
    description = Column(Text, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    mlflow_run_id = Column(String(256), nullable=True)
    mlflow_experiment_id = Column(String(256), nullable=True)
    config_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    creator = relationship(
        "User", back_populates="experiments", foreign_keys=[created_by]
    )
    dataset = relationship("Dataset", back_populates="experiments")
    metrics = relationship(
        "ExperimentMetrics",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )
    training_sessions = relationship(
        "TrainingSession",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )
    pipeline_statuses = relationship(
        "PipelineStatus",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )
    model_registries = relationship("ModelRegistry", back_populates="experiment")
    optuna_trials = relationship(
        "OptunaTrialRecord",
        back_populates="experiment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Experiment id={self.id} name={self.name!r} status={self.status.value!r}>"


class ExperimentMetrics(Base):
    """Scalar evaluation metrics for a trained model within an experiment."""

    __tablename__ = "experiment_metrics"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    experiment_id = Column(
        Integer,
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_name = Column(String(128), nullable=False)
    accuracy = Column(Float, nullable=True)
    precision_score = Column(Float, nullable=True)
    recall_score = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    roc_auc = Column(Float, nullable=True)
    inference_time_ms = Column(Float, nullable=True)
    training_time_sec = Column(Float, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    model_size_mb = Column(Float, nullable=True)
    params_json = Column(JSON, nullable=True)
    hyperparams_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    experiment = relationship("Experiment", back_populates="metrics")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<ExperimentMetrics experiment_id={self.experiment_id} "
            f"model={self.model_name!r} acc={self.accuracy}>"
        )


class TrainingSession(Base):
    """Real-time progress tracking for an ongoing training run."""

    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    experiment_id = Column(
        Integer,
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    model_name = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    progress_pct = Column(Float, nullable=False, default=0.0)
    current_epoch = Column(Integer, nullable=False, default=0)
    total_epochs = Column(Integer, nullable=False, default=0)
    current_loss = Column(Float, nullable=True)
    current_val_loss = Column(Float, nullable=True)
    current_accuracy = Column(Float, nullable=True)
    current_val_accuracy = Column(Float, nullable=True)
    eta_seconds = Column(Integer, nullable=True)
    logs = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True, default=datetime.utcnow)
    updated_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    experiment = relationship("Experiment", back_populates="training_sessions")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<TrainingSession id={self.id} model={self.model_name!r} "
            f"progress={self.progress_pct:.1f}%>"
        )


class PipelineStatus(Base):
    """Stage-level status for a multi-step ML pipeline."""

    __tablename__ = "pipeline_statuses"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    experiment_id = Column(
        Integer,
        ForeignKey("experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    stage = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False, default="pending")
    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    logs = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    experiment = relationship("Experiment", back_populates="pipeline_statuses")

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<PipelineStatus experiment_id={self.experiment_id} "
            f"stage={self.stage!r} status={self.status!r}>"
        )
