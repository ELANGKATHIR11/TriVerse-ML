from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.optuna_engine.optimizer import OptunaEngine

router = APIRouter(prefix="/optuna", tags=["optuna"])
optuna_engine = OptunaEngine()

@router.get("/studies", response_model=List[Dict[str, Any]])
async def list_studies(current_user: User = Depends(get_current_user)):
    """List all Optuna studies."""
    try:
        return optuna_engine.list_studies()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/studies/{study_name}/trials", response_model=List[Dict[str, Any]])
async def get_study_trials(study_name: str, current_user: User = Depends(get_current_user)):
    """Get trial history for a study."""
    try:
        return optuna_engine.get_trial_history(study_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/studies/{study_name}/best", response_model=Dict[str, Any])
async def get_best_params(study_name: str, current_user: User = Depends(get_current_user)):
    """Get the best parameters for a study."""
    try:
        return {
            "study_name": study_name,
            "best_params": optuna_engine.get_best_params(study_name)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/studies/{study_name}/param-importances", response_model=Dict[str, Any])
async def get_param_importances(study_name: str, current_user: User = Depends(get_current_user)):
    """Get hyperparameter importances for a study."""
    try:
        return optuna_engine.get_param_importances(study_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
