from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.analytics.stats import AnalyticsEngine

router = APIRouter(prefix="/leaderboard", tags=["leaderboard"])
analytics_engine = AnalyticsEngine()

@router.get("", response_model=List[Dict[str, Any]])
async def get_leaderboard(
    task_type: Optional[str] = Query(None, description="Filter by task type: credit, disease, handwriting"),
    sort_by: str = Query("weighted_score", description="Sort by: weighted_score, accuracy, inference_time"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve weighted model rankings and achievements."""
    try:
        return await analytics_engine.get_leaderboard(db, task_type=task_type, sort_by=sort_by)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/compare", response_model=Dict[str, Any])
async def compare_models(
    models: str = Query(..., description="Comma-separated model names to compare"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve detailed comparative stats for multiple models."""
    model_list = [m.strip() for m in models.split(",") if m.strip()]
    if not model_list:
        raise HTTPException(status_code=400, detail="No models specified for comparison.")
    try:
        return await analytics_engine.get_model_comparison(db, model_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
