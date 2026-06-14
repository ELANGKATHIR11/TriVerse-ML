"""
F:\\3ml project\\backend\\app\\api\\routes\\datasets.py

Dataset management router – upload, validate, version, quality analysis.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import uuid
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.dataset import Dataset, DataQualityReport, DatasetStatus, DatasetVersion, TaskType
from app.models.user import User, UserRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/datasets", tags=["Datasets"])

from app.core.config import settings

# Directories for dataset storage
DATASETS_DIR = settings.ARTIFACTS_DIR / "datasets"
DATASETS_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".csv", ".tsv", ".json", ".parquet", ".xlsx"}
MAX_FILE_SIZE_MB = 500


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_quality_score(stats: dict[str, Any]) -> float:
    """Compute a simple quality score 0–100 based on data statistics."""
    missing_pct = stats.get("missing_pct", 0.0)
    duplicate_pct = stats.get("duplicate_pct", 0.0)
    outlier_pct = stats.get("outlier_pct", 0.0)
    score = 100.0 - (missing_pct * 0.4 + duplicate_pct * 0.3 + outlier_pct * 0.3)
    return max(0.0, min(100.0, round(score, 2)))


async def _analyze_csv(file_path: Path) -> dict[str, Any]:
    """Basic CSV analysis using pandas (imported lazily to avoid top-level overhead)."""
    try:
        import pandas as pd  # noqa: PLC0415

        df = pd.read_csv(file_path)
        total = len(df)
        missing_pct = float(df.isnull().sum().sum() / max(df.size, 1) * 100)
        duplicate_pct = float(df.duplicated().sum() / max(total, 1) * 100)

        col_stats: dict[str, Any] = {}
        for col in df.columns:
            col_stats[col] = {
                "dtype": str(df[col].dtype),
                "null_count": int(df[col].isnull().sum()),
                "unique_count": int(df[col].nunique()),
            }

        return {
            "row_count": total,
            "col_count": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
            "column_stats": col_stats,
            "missing_pct": round(missing_pct, 4),
            "duplicate_pct": round(duplicate_pct, 4),
            "outlier_pct": 0.0,  # Placeholder for advanced outlier detection
        }
    except Exception as exc:
        logger.warning("CSV analysis failed: %s", exc)
        return {
            "row_count": 0,
            "col_count": 0,
            "columns": [],
            "missing_pct": 0.0,
            "duplicate_pct": 0.0,
            "outlier_pct": 0.0,
        }


# ---------------------------------------------------------------------------
# POST /datasets/upload
# ---------------------------------------------------------------------------


@router.post(
    "/upload",
    summary="Upload a dataset file",
    status_code=status.HTTP_201_CREATED,
)
async def upload_dataset(
    name: str = Form(..., description="Human-readable dataset name"),
    task_type: TaskType = Form(..., description="ML task: credit | disease | handwriting"),
    description: str | None = Form(None, description="Optional description"),
    file: UploadFile = File(..., description="Dataset file (CSV, TSV, JSON, Parquet, Excel)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Upload a dataset file and register it in the platform."""
    # Validate file extension
    suffix = Path(file.filename or "data.csv").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{suffix}'. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    # Save file to disk
    unique_id = uuid.uuid4().hex
    dest_filename = f"{unique_id}_{file.filename}"
    dest_path = DATASETS_DIR / dest_filename

    content = await file.read()
    file_size_mb = len(content) / (1024 * 1024)

    if file_size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size_mb:.1f} MB) exceeds the {MAX_FILE_SIZE_MB} MB limit.",
        )

    async with aiofiles.open(dest_path, "wb") as f:
        await f.write(content)

    # Analyze dataset
    stats: dict[str, Any] = {}
    row_count = 0
    col_count = 0
    if suffix == ".csv":
        stats = await _analyze_csv(dest_path)
        row_count = stats.get("row_count", 0)
        col_count = stats.get("col_count", 0)

    quality_score = _compute_quality_score(stats)

    # Persist to database
    dataset = Dataset(
        name=name,
        task_type=task_type,
        description=description,
        file_path=str(dest_path),
        file_size_mb=round(file_size_mb, 4),
        row_count=row_count,
        col_count=col_count,
        quality_score=quality_score,
        status=DatasetStatus.READY,
        created_by=current_user.id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    db.add(dataset)
    await db.flush()
    await db.refresh(dataset)

    # Create initial quality report
    if stats:
        report = DataQualityReport(
            dataset_id=dataset.id,
            score=quality_score,
            missing_pct=stats.get("missing_pct", 0.0),
            duplicate_pct=stats.get("duplicate_pct", 0.0),
            outlier_pct=stats.get("outlier_pct", 0.0),
            issues_json=stats,
            created_at=datetime.now(UTC),
        )
        db.add(report)
        await db.flush()

    # Create version 1
    version_record = DatasetVersion(
        dataset_id=dataset.id,
        version="v1.0",
        schema_json={"columns": stats.get("columns", []), "dtypes": stats.get("dtypes", {})},
        stats_json=stats,
        file_path=str(dest_path),
        created_at=datetime.now(UTC),
    )
    db.add(version_record)
    await db.flush()

    logger.info("Dataset '%s' (id=%d) uploaded by %r", name, dataset.id, current_user.username)

    return {
        "id": dataset.id,
        "name": dataset.name,
        "task_type": dataset.task_type.value,
        "file_size_mb": dataset.file_size_mb,
        "row_count": dataset.row_count,
        "col_count": dataset.col_count,
        "quality_score": dataset.quality_score,
        "status": dataset.status.value,
        "created_at": dataset.created_at.isoformat(),
        "version": "v1.0",
    }


# ---------------------------------------------------------------------------
# GET /datasets
# ---------------------------------------------------------------------------


@router.get(
    "",
    summary="List datasets (paginated)",
    status_code=status.HTTP_200_OK,
)
async def list_datasets(
    task_type: TaskType | None = Query(None, description="Filter by task type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return a paginated list of datasets."""
    query = select(Dataset)
    if task_type:
        query = query.where(Dataset.task_type == task_type)

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar_one()

    datasets_result = await db.execute(
        query.order_by(Dataset.created_at.desc()).offset(skip).limit(limit)
    )
    datasets = datasets_result.scalars().all()

    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "datasets": [
            {
                "id": d.id,
                "name": d.name,
                "task_type": d.task_type.value,
                "description": d.description,
                "file_size_mb": d.file_size_mb,
                "row_count": d.row_count,
                "col_count": d.col_count,
                "quality_score": d.quality_score,
                "status": d.status.value,
                "created_at": d.created_at.isoformat(),
            }
            for d in datasets
        ],
    }


# ---------------------------------------------------------------------------
# GET /datasets/{id}
# ---------------------------------------------------------------------------


@router.get(
    "/{dataset_id}",
    summary="Get dataset details",
    status_code=status.HTTP_200_OK,
)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return full metadata for a specific dataset."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset: Dataset | None = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Dataset {dataset_id} not found.")

    return {
        "id": dataset.id,
        "name": dataset.name,
        "task_type": dataset.task_type.value,
        "description": dataset.description,
        "file_path": dataset.file_path,
        "file_size_mb": dataset.file_size_mb,
        "row_count": dataset.row_count,
        "col_count": dataset.col_count,
        "quality_score": dataset.quality_score,
        "status": dataset.status.value,
        "created_by": dataset.created_by,
        "created_at": dataset.created_at.isoformat(),
        "updated_at": dataset.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# GET /datasets/{id}/quality
# ---------------------------------------------------------------------------


@router.get(
    "/{dataset_id}/quality",
    summary="Get the latest data quality report for a dataset",
    status_code=status.HTTP_200_OK,
)
async def get_dataset_quality(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return the most recent data quality report for the given dataset."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found.")

    report_result = await db.execute(
        select(DataQualityReport)
        .where(DataQualityReport.dataset_id == dataset_id)
        .order_by(DataQualityReport.created_at.desc())
        .limit(1)
    )
    report: DataQualityReport | None = report_result.scalar_one_or_none()
    if report is None:
        raise HTTPException(status_code=404, detail="No quality report found for this dataset.")

    return {
        "dataset_id": dataset_id,
        "score": report.score,
        "missing_pct": report.missing_pct,
        "duplicate_pct": report.duplicate_pct,
        "outlier_pct": report.outlier_pct,
        "issues": report.issues_json,
        "created_at": report.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# POST /datasets/{id}/validate
# ---------------------------------------------------------------------------


@router.post(
    "/{dataset_id}/validate",
    summary="Trigger a validation / re-analysis of the dataset",
    status_code=status.HTTP_200_OK,
)
async def validate_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Re-run data quality analysis and create a new quality report."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset: Dataset | None = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found.")

    if not dataset.file_path or not Path(dataset.file_path).exists():
        raise HTTPException(status_code=404, detail="Dataset file not found on disk.")

    file_path = Path(dataset.file_path)
    stats = await _analyze_csv(file_path) if file_path.suffix == ".csv" else {}
    quality_score = _compute_quality_score(stats)

    report = DataQualityReport(
        dataset_id=dataset_id,
        score=quality_score,
        missing_pct=stats.get("missing_pct", 0.0),
        duplicate_pct=stats.get("duplicate_pct", 0.0),
        outlier_pct=stats.get("outlier_pct", 0.0),
        issues_json=stats,
        created_at=datetime.now(UTC),
    )
    db.add(report)
    # Update dataset's quality score
    dataset.quality_score = quality_score
    dataset.updated_at = datetime.now(UTC)
    await db.flush()

    return {
        "dataset_id": dataset_id,
        "new_quality_score": quality_score,
        "missing_pct": stats.get("missing_pct", 0.0),
        "duplicate_pct": stats.get("duplicate_pct", 0.0),
        "outlier_pct": stats.get("outlier_pct", 0.0),
        "validated_at": datetime.now(UTC).isoformat(),
    }


# ---------------------------------------------------------------------------
# GET /datasets/{id}/schema
# ---------------------------------------------------------------------------


@router.get(
    "/{dataset_id}/schema",
    summary="Get the schema (columns, dtypes) of a dataset",
    status_code=status.HTTP_200_OK,
)
async def get_dataset_schema(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return the column schema of the latest dataset version."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset: Dataset | None = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found.")

    # Get the latest version
    version_result = await db.execute(
        select(DatasetVersion)
        .where(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.created_at.desc())
        .limit(1)
    )
    version = version_result.scalar_one_or_none()
    schema = version.schema_json if version and version.schema_json else {}

    return {
        "dataset_id": dataset_id,
        "name": dataset.name,
        "task_type": dataset.task_type.value,
        "schema": schema,
        "row_count": dataset.row_count,
        "col_count": dataset.col_count,
    }


# ---------------------------------------------------------------------------
# POST /datasets/{id}/version
# ---------------------------------------------------------------------------


@router.post(
    "/{dataset_id}/version",
    summary="Create a new version snapshot of the dataset",
    status_code=status.HTTP_201_CREATED,
)
async def create_dataset_version(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Snapshot the current state of a dataset as a new version."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset: Dataset | None = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found.")

    # Count existing versions
    count_result = await db.execute(
        select(func.count()).where(DatasetVersion.dataset_id == dataset_id)
    )
    existing_count = count_result.scalar_one()
    new_version_tag = f"v{existing_count + 1}.0"

    # Re-analyze if file exists
    stats: dict[str, Any] = {}
    if dataset.file_path and Path(dataset.file_path).exists():
        file_path = Path(dataset.file_path)
        if file_path.suffix == ".csv":
            stats = await _analyze_csv(file_path)

    version = DatasetVersion(
        dataset_id=dataset_id,
        version=new_version_tag,
        schema_json={"columns": stats.get("columns", []), "dtypes": stats.get("dtypes", {})},
        stats_json=stats,
        file_path=dataset.file_path,
        created_at=datetime.now(UTC),
    )
    db.add(version)
    await db.flush()
    await db.refresh(version)

    return {
        "dataset_id": dataset_id,
        "version_id": version.id,
        "version": new_version_tag,
        "created_at": version.created_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# GET /datasets/{id}/versions
# ---------------------------------------------------------------------------


@router.get(
    "/{dataset_id}/versions",
    summary="List all versions of a dataset",
    status_code=status.HTTP_200_OK,
)
async def list_dataset_versions(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return all version snapshots for a given dataset."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found.")

    versions_result = await db.execute(
        select(DatasetVersion)
        .where(DatasetVersion.dataset_id == dataset_id)
        .order_by(DatasetVersion.created_at.desc())
    )
    versions = versions_result.scalars().all()

    return {
        "dataset_id": dataset_id,
        "total": len(versions),
        "versions": [
            {
                "id": v.id,
                "version": v.version,
                "file_path": v.file_path,
                "created_at": v.created_at.isoformat(),
            }
            for v in versions
        ],
    }


# ---------------------------------------------------------------------------
# DELETE /datasets/{id}
# ---------------------------------------------------------------------------


@router.delete(
    "/{dataset_id}",
    summary="Delete a dataset (Admin or creator)",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a dataset and its file from disk. Admins can delete any dataset; others can only delete their own."""
    result = await db.execute(select(Dataset).where(Dataset.id == dataset_id))
    dataset: Dataset | None = result.scalar_one_or_none()
    if dataset is None:
        raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found.")

    if current_user.role != UserRole.ADMIN and dataset.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own datasets.")

    # Remove file from disk
    if dataset.file_path and Path(dataset.file_path).exists():
        try:
            os.remove(dataset.file_path)
        except OSError as exc:
            logger.warning("Failed to remove dataset file: %s", exc)

    await db.delete(dataset)
    logger.info("Dataset id=%d deleted by %r", dataset_id, current_user.username)
