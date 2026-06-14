from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.dataset import Dataset
from app.analytics.stats import AnalyticsEngine

router = APIRouter(prefix="/analytics", tags=["analytics"])
analytics_engine = AnalyticsEngine()

@router.get("/overview", response_model=Dict[str, Any])
async def get_overview(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve global analytics and recent activity details."""
    try:
        return await analytics_engine.get_overview_stats(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/task/{task_type}", response_model=Dict[str, Any])
async def get_task_summary(
    task_type: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve aggregate performance details for a specific task."""
    if task_type not in ["credit", "disease", "handwriting"]:
        raise HTTPException(status_code=400, detail="Invalid task type.")
    try:
        return await analytics_engine.get_task_summary(db, task_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dataset/{dataset_id}/distribution", response_model=Dict[str, Any])
async def get_dataset_distribution(
    dataset_id: int,
    column: str = Query(..., description="The feature column to calculate distribution for"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate distribution bins and histogram stats for a feature column in a dataset."""
    # Find dataset path
    stmt = select(Dataset).where(Dataset.id == dataset_id)
    dataset = (await db.execute(stmt)).scalar()
    if not dataset or not dataset.file_path:
        raise HTTPException(status_code=404, detail="Dataset not found or no file path available.")
        
    try:
        df = pd.read_csv(dataset.file_path)
        if column not in df.columns:
            raise HTTPException(status_code=400, detail=f"Column '{column}' not found in dataset.")
            
        series = df[column].dropna()
        if pd.api.types.is_numeric_dtype(series):
            counts, bin_edges = np.histogram(series, bins=20)
            return {
                "column": column,
                "type": "numeric",
                "bins": [{"bin_start": float(bin_edges[i]), "bin_end": float(bin_edges[i+1]), "count": int(counts[i])} for i in range(len(counts))],
                "mean": float(series.mean()),
                "median": float(series.median()),
                "std": float(series.std()),
                "min": float(series.min()),
                "max": float(series.max())
            }
        else:
            value_counts = series.value_counts().head(20)
            return {
                "column": column,
                "type": "categorical",
                "counts": [{"value": str(k), "count": int(v)} for k, v in value_counts.items()]
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
from sqlalchemy import select
