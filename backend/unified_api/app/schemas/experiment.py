"""
Pydantic V2 schemas for experiment management and leaderboard endpoints.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.models.experiment import ExperimentStatus


# ---------------------------------------------------------------------------
# Experiment
# ---------------------------------------------------------------------------


class ExperimentCreate(BaseModel):
    """Payload to create a new experiment."""

    name: str = Field(..., min_length=1, max_length=256)
    task_type: str
    dataset_id: int
    description: str | None = None
    config_json: dict[str, Any] | None = None


class ExperimentUpdate(BaseModel):
    """Partial update for an existing experiment."""

    name: str | None = Field(default=None, min_length=1, max_length=256)
    status: ExperimentStatus | None = None
    description: str | None = None


class ExperimentResponse(BaseModel):
    """Full experiment representation returned from API."""

    model_config = {"from_attributes": True}

    id: int
    name: str
    task_type: str
    dataset_id: int | None
    status: ExperimentStatus
    description: str | None
    created_by: int
    mlflow_run_id: str | None
    mlflow_experiment_id: str | None
    config_json: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------


class MetricsResponse(BaseModel):
    """Evaluation metrics for a single model within an experiment."""

    model_config = {"from_attributes": True}

    id: int
    experiment_id: int
    model_name: str
    accuracy: float | None
    precision_score: float | None
    recall_score: float | None
    f1_score: float | None
    roc_auc: float | None
    inference_time_ms: float | None
    training_time_sec: float | None
    memory_usage_mb: float | None
    model_size_mb: float | None
    params_json: dict[str, Any] | None
    hyperparams_json: dict[str, Any] | None
    created_at: datetime


# ---------------------------------------------------------------------------
# Training Session
# ---------------------------------------------------------------------------


class TrainingSessionResponse(BaseModel):
    """Real-time training progress snapshot."""

    model_config = {"from_attributes": True}

    id: int
    experiment_id: int
    model_name: str
    status: str
    progress_pct: float
    current_epoch: int
    total_epochs: int
    current_loss: float | None
    current_val_loss: float | None
    current_accuracy: float | None
    current_val_accuracy: float | None
    eta_seconds: int | None
    logs: str | None
    started_at: datetime | None
    updated_at: datetime


# ---------------------------------------------------------------------------
# Leaderboard
# ---------------------------------------------------------------------------


class LeaderboardEntry(BaseModel):
    """A single row in the model performance leaderboard."""

    rank: int
    model_name: str
    task_type: str
    accuracy: float | None
    precision_score: float | None
    recall_score: float | None
    f1_score: float | None
    roc_auc: float | None
    inference_time_ms: float | None
    training_time_sec: float | None
    weighted_score: float
    badges: list[str] = Field(default_factory=list)
