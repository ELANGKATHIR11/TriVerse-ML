"""
F:\3ml project\backend\app\models\dataset.py

Dataset-related ORM models: Dataset, DatasetVersion, DataQualityReport.
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


class TaskType(str, enum.Enum):
    """ML task domains supported by the platform."""

    CREDIT = "credit"
    DISEASE = "disease"
    HANDWRITING = "handwriting"


class DatasetStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"


class Dataset(Base):
    """Registered dataset with metadata and quality tracking."""

    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    name = Column(String(256), nullable=False, index=True)
    task_type = Column(
        SAEnum(TaskType, name="tasktype", native_enum=False),
        nullable=False,
    )
    description = Column(Text, nullable=True)
    file_path = Column(String(512), nullable=True)
    file_size_mb = Column(Float, nullable=True)
    row_count = Column(Integer, nullable=True)
    col_count = Column(Integer, nullable=True)
    quality_score = Column(Float, nullable=True)
    status = Column(
        SAEnum(DatasetStatus, name="datasetstatus", native_enum=False),
        nullable=False,
        default=DatasetStatus.PENDING,
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

    creator = relationship("User", back_populates="datasets", foreign_keys=[created_by])
    versions = relationship(
        "DatasetVersion",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
    quality_reports = relationship(
        "DataQualityReport",
        back_populates="dataset",
        cascade="all, delete-orphan",
    )
    experiments = relationship("Experiment", back_populates="dataset")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Dataset id={self.id} name={self.name!r} task={self.task_type.value!r}>"


class DatasetVersion(Base):
    """Immutable snapshot of a dataset at a particular point in time."""

    __tablename__ = "dataset_versions"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version = Column(String(32), nullable=False)
    schema_json = Column(JSON, nullable=True)
    stats_json = Column(JSON, nullable=True)
    file_path = Column(String(512), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="versions")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DatasetVersion dataset_id={self.dataset_id} version={self.version!r}>"


class DataQualityReport(Base):
    """Automated data-quality assessment for a dataset."""

    __tablename__ = "data_quality_reports"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    dataset_id = Column(
        Integer,
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score = Column(Float, nullable=False, default=0.0)
    missing_pct = Column(Float, nullable=False, default=0.0)
    duplicate_pct = Column(Float, nullable=False, default=0.0)
    outlier_pct = Column(Float, nullable=False, default=0.0)
    issues_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    dataset = relationship("Dataset", back_populates="quality_reports")

    def __repr__(self) -> str:  # pragma: no cover
        return f"<DataQualityReport dataset_id={self.dataset_id} score={self.score}>"
