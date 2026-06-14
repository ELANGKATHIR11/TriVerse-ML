from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Dict, Any, List
import time
import numpy as np

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.models.inference import PredictionLog
from app.models.mlops import ModelRegistry

from app.ml.inference_service import CreditInferenceService, DiseaseInferenceService, HandwritingInferenceService

router = APIRouter(prefix="/predictions", tags=["predictions"])

class CreditInferenceRequest(BaseModel):
    features: Dict[str, float]

class DiseaseInferenceRequest(BaseModel):
    features: Dict[str, float]

class HandwritingInferenceRequest(BaseModel):
    image_b64: str  # Base64 encoded grayscale 28x28 image string

def clean_for_json(val: Any) -> Any:
    if isinstance(val, dict):
        return {k: clean_for_json(v) for k, v in val.items()}
    elif isinstance(val, (list, tuple)):
        return [clean_for_json(v) for v in val]
    elif isinstance(val, (np.float32, np.float64, np.floating)):
        return float(val)
    elif isinstance(val, (np.int32, np.int64, np.integer)):
        return int(val)
    elif isinstance(val, np.ndarray):
        return clean_for_json(val.tolist())
    return val

@router.post("/credit")
async def predict_credit(
    req: CreditInferenceRequest,
    model_name: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run real-time credit default prediction using actual trained model."""
    start_time = time.time()
    
    if not model_name:
        stmt = select(ModelRegistry).where(
            ModelRegistry.task_type == "credit",
            ModelRegistry.stage == "production"
        )
        registry_entry = (await db.execute(stmt)).scalars().first()
        if registry_entry:
            model_name = registry_entry.name.replace("Credit-", "")
        else:
            model_name = "random_forest"

    try:
        res = CreditInferenceService.predict(req.features, model_name=model_name)
        res = clean_for_json(res)
    except FileNotFoundError as fnf:
        # If model is not found, fallback to training default or return 500
        raise HTTPException(status_code=500, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")

    latency = (time.time() - start_time) * 1000
    
    # Log prediction to DB
    log = PredictionLog(
        input_json=req.features,
        output_json={"prediction": res["prediction"], "probability": res["probability"], "score": res["score"], "risk": res["risk"], "model_name": model_name},
        latency_ms=latency,
        user_id=current_user.id
    )
    db.add(log)
    await db.commit()
    
    return {
        "prediction": res["prediction"],
        "probability": res["probability"],
        "score": res["score"],
        "risk": res["risk"],
        "latency_ms": latency,
        "model_name": model_name
    }

@router.post("/disease")
async def predict_disease(
    req: DiseaseInferenceRequest,
    model_name: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run real-time disease prediction using actual trained model."""
    start_time = time.time()
    
    if not model_name:
        stmt = select(ModelRegistry).where(
            ModelRegistry.task_type == "disease",
            ModelRegistry.stage == "production"
        )
        registry_entry = (await db.execute(stmt)).scalars().first()
        if registry_entry:
            model_name = registry_entry.name.replace("Disease-", "")
        else:
            model_name = "xgboost"

    try:
        res = DiseaseInferenceService.predict(req.features, model_name=model_name)
        res = clean_for_json(res)
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=500, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
        
    latency = (time.time() - start_time) * 1000
    
    log = PredictionLog(
        input_json=req.features,
        output_json={"prediction": res["prediction"], "probability": res["probability"], "risk": res["risk"], "model_name": model_name},
        latency_ms=latency,
        user_id=current_user.id
    )
    db.add(log)
    await db.commit()
    
    return {
        "prediction": res["prediction"],
        "probability": res["probability"],
        "risk": res["risk"],
        "latency_ms": latency,
        "model_name": model_name
    }

@router.post("/handwriting")
async def predict_handwriting(
    req: HandwritingInferenceRequest,
    model_name: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recognize a handwritten character from grayscale base64 image using actual CNN/ResNet18."""
    start_time = time.time()
    
    if not model_name:
        stmt = select(ModelRegistry).where(
            ModelRegistry.task_type == "handwriting",
            ModelRegistry.stage == "production"
        )
        registry_entry = (await db.execute(stmt)).scalars().first()
        if registry_entry:
            model_name = registry_entry.name.replace("Handwriting-", "")
        else:
            model_name = "cnn"

    try:
        res = HandwritingInferenceService.predict(req.image_b64, model_name=model_name)
        res = clean_for_json(res)
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=500, detail=str(fnf))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")
    
    latency = (time.time() - start_time) * 1000
    
    log = PredictionLog(
        input_json={"image_len": len(req.image_b64)},
        output_json={"prediction": res["prediction"], "probability": res["probability"], "top_predictions": res["top_predictions"], "model_name": model_name},
        latency_ms=latency,
        user_id=current_user.id
    )
    db.add(log)
    await db.commit()
    
    return {
        "prediction": res["prediction"],
        "probability": res["probability"],
        "top_predictions": res["top_predictions"],
        "probabilities": res["probabilities"],
        "latency_ms": latency,
        "model_name": model_name
    }

@router.get("/logs", response_model=List[Dict[str, Any]])
async def get_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve historical prediction logs."""
    stmt = select(PredictionLog).order_by(PredictionLog.created_at.desc()).limit(100)
    logs = (await db.execute(stmt)).scalars().all()
    return [{
        "id": l.id,
        "input": l.input_json,
        "output": l.output_json,
        "latency_ms": l.latency_ms,
        "created_at": l.created_at.isoformat()
    } for l in logs]
