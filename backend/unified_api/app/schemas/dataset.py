"""
Pydantic V2 schemas for dataset management endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.dataset import DatasetStatus, TaskType


class DatasetCreate(BaseModel):
    """Payload to register a new dataset."""

    name: str = Field(..., min_length=1, max_length=256)
    task_type: TaskType
    description: str | None = None


class DatasetResponse(BaseModel):
    """Full dataset representation returned from API."""

    model_config = {"from_attributes": True}

    id: int
    name: str
    task_type: TaskType
    description: str | None
    file_path: str | None
    file_size_mb: float | None
    row_count: int | None
    col_count: int | None
    quality_score: float | None
    status: DatasetStatus
    created_by: int
    created_at: datetime
    updated_at: datetime


class DataQualityResponse(BaseModel):
    """Data-quality report for a dataset."""

    model_config = {"from_attributes": True}

    id: int
    dataset_id: int
    score: float
    missing_pct: float
    duplicate_pct: float
    outlier_pct: float
    issues_json: dict[str, Any] | None
    created_at: datetime
