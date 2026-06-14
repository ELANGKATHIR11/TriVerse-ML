"""
F:\\3ml project\\backend\\app\\api\\routes\\metrics.py

Experiment metrics router – query and compare model metrics.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.experiment import Experiment, ExperimentMetrics
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metrics", tags=["Metrics"])

VALID_TASK_TYPES = {"credit", "disease", "handwriting"}


# ---------------------------------------------------------------------------
# GET /metrics
# ---------------------------------------------------------------------------


@router.get(
    "",
    summary="Query metrics with optional filters",
    status_code=status.HTTP_200_OK,
)
async def list_metrics(
    experiment_id: int | None = Query(None, description="Filter by experiment ID"),
    model_name: str | None = Query(None, description="Filter by model name"),
    task_type: str | None = Query(None, description="Filter by task type: credit|disease|handwriting"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return experiment metrics with optional filtering by experiment, model, or task type."""
    # Build the base query with a join to Experiment for task_type filtering
    query = select(ExperimentMetrics).join(
        Experiment, ExperimentMetrics.experiment_id == Experiment.id
    )

    if experiment_id is not None:
        query = query.where(ExperimentMetrics.experiment_id == experiment_id)
    if model_name:
        query = query.where(ExperimentMetrics.model_name.ilike(f"%{model_name}%"))
    if task_type:
        if task_type not in VALID_TASK_TYPES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid task_type '{task_type}'. Must be one of: {', '.join(VALID_TASK_TYPES)}",
            )
        query = query.where(Experiment.task_type == task_type)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    result = await db.execute(
        query.order_by(ExperimentMetrics.created_at.desc()).offset(skip).limit(limit)
    )
    metrics_list = result.scalars().all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "metrics": [_serialize_metrics(m) for m in metrics_list],
    }


# ---------------------------------------------------------------------------
# GET /metrics/{id}
# ---------------------------------------------------------------------------


@router.get(
    "/{metrics_id}",
    summary="Get a specific metrics record by ID",
    status_code=status.HTTP_200_OK,
)
async def get_metrics(
    metrics_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Retrieve a single metrics record by its primary key."""
    result = await db.execute(
        select(ExperimentMetrics).where(ExperimentMetrics.id == metrics_id)
    )
    m: ExperimentMetrics | None = result.scalar_one_or_none()
    if m is None:
        raise HTTPException(status_code=404, detail=f"Metrics record {metrics_id} not found.")
    return _serialize_metrics(m)


# ---------------------------------------------------------------------------
# GET /metrics/experiment/{experiment_id}
# ---------------------------------------------------------------------------


@router.get(
    "/experiment/{experiment_id}",
    summary="Get all metrics for a specific experiment",
    status_code=status.HTTP_200_OK,
)
async def get_experiment_metrics(
    experiment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return all model metrics recorded for the given experiment."""
    # Verify experiment exists
    exp_result = await db.execute(select(Experiment).where(Experiment.id == experiment_id))
    experiment = exp_result.scalar_one_or_none()
    if experiment is None:
        raise HTTPException(status_code=404, detail=f"Experiment {experiment_id} not found.")

    result = await db.execute(
        select(ExperimentMetrics)
        .where(ExperimentMetrics.experiment_id == experiment_id)
        .order_by(ExperimentMetrics.accuracy.desc())
    )
    metrics_list = result.scalars().all()

    return {
        "experiment_id": experiment_id,
        "experiment_name": experiment.name,
        "task_type": experiment.task_type,
        "total": len(metrics_list),
        "metrics": [_serialize_metrics(m) for m in metrics_list],
    }


# ---------------------------------------------------------------------------
# GET /metrics/best/{task_type}
# ---------------------------------------------------------------------------


@router.get(
    "/best/{task_type}",
    summary="Get the best-performing metrics per model for a task type",
    status_code=status.HTTP_200_OK,
)
async def get_best_metrics(
    task_type: str,
    limit: int = Query(10, ge=1, le=50, description="Top N models to return"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return the top performing metrics entries for a given task type, sorted by accuracy."""
    if task_type not in VALID_TASK_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid task_type '{task_type}'. Must be one of: {', '.join(VALID_TASK_TYPES)}",
        )

    result = await db.execute(
        select(ExperimentMetrics)
        .join(Experiment, ExperimentMetrics.experiment_id == Experiment.id)
        .where(Experiment.task_type == task_type)
        .where(ExperimentMetrics.accuracy.isnot(None))
        .order_by(ExperimentMetrics.accuracy.desc())
        .limit(limit)
    )
    metrics_list = result.scalars().all()

    return {
        "task_type": task_type,
        "total": len(metrics_list),
        "best_metrics": [_serialize_metrics(m) for m in metrics_list],
    }


# ---------------------------------------------------------------------------
# Serializer
# ---------------------------------------------------------------------------


def _serialize_metrics(m: ExperimentMetrics) -> dict[str, Any]:
    return {
        "id": m.id,
        "experiment_id": m.experiment_id,
        "model_name": m.model_name,
        "accuracy": m.accuracy,
        "precision": m.precision_score,
        "recall": m.recall_score,
        "f1_score": m.f1_score,
        "roc_auc": m.roc_auc,
        "inference_time_ms": m.inference_time_ms,
        "training_time_sec": m.training_time_sec,
        "memory_usage_mb": m.memory_usage_mb,
        "model_size_mb": m.model_size_mb,
        "params": m.params_json,
        "hyperparams": m.hyperparams_json,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    }

@router.get(
    "/realtime",
    summary="Get real-time training and system metrics",
)
async def get_realtime_metrics(
    db: AsyncSession = Depends(get_db)
):
    from app.api.routes.training import _collect_system_stats
    sys_stats = await _collect_system_stats()

    from app.models.experiment import TrainingSession
    ts_stmt = select(TrainingSession).order_by(TrainingSession.updated_at.desc()).limit(1)
    ts = (await db.execute(ts_stmt)).scalar_one_or_none()

    epoch = ts.current_epoch if ts else 0
    accuracy = ts.current_accuracy if ts else 0.0
    loss = ts.current_loss if (ts and ts.current_loss is not None) else 0.0
    eta = ts.eta_seconds if (ts and ts.eta_seconds is not None) else 0

    gpu_mem = 0.0
    if sys_stats.get("gpu") and "memory_used_gb" in sys_stats["gpu"]:
        gpu_mem = sys_stats["gpu"]["memory_used_gb"]

    return {
        "epoch": epoch,
        "batch": 0,
        "totalBatches": 100,
        "accuracy": accuracy,
        "loss": loss,
        "etaSeconds": eta,
        "system": {
            "cpu": sys_stats["cpu"]["percent"],
            "ram": sys_stats["memory"]["percent"],
            "gpuTemp": 65,
            "gpuMemory": gpu_mem,
        }
    }
