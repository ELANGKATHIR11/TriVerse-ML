from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.digital_twin.pipeline_tracker import DigitalTwinTracker

router = APIRouter(prefix="/digital-twin", tags=["digital-twin"])
tracker = DigitalTwinTracker()

@router.get("/{experiment_id}", response_model=List[Dict[str, Any]])
async def get_digital_twin_status(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve full pipeline status and node diagnostics for an experiment."""
    try:
        return await tracker.get_pipeline_status(db, experiment_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{experiment_id}/replay", response_model=List[Dict[str, Any]])
async def get_replay_history(
    experiment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get historical state updates for replaying execution progress."""
    try:
        return await tracker.get_replay_history(db, experiment_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
