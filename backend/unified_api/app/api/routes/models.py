from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from typing import List, Dict, Any, Optional
import time

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.mlops import ModelRegistry, ModelVersion
from app.models.inference import PredictionLog

router = APIRouter(prefix="/models", tags=["models"])

from app.models.experiment import ExperimentMetrics

async def get_model_metrics(db: AsyncSession, registry: ModelRegistry) -> Dict[str, Any]:
    if not registry.experiment_id:
        return {}
    # Find matching model_name in ExperimentMetrics
    stmt = select(ExperimentMetrics).where(ExperimentMetrics.experiment_id == registry.experiment_id)
    metrics_list = (await db.execute(stmt)).scalars().all()
    
    # Try to match by name
    reg_name_lower = registry.name.lower()
    for m in metrics_list:
        m_name_lower = m.model_name.lower()
        if (m_name_lower in reg_name_lower) or \
           (m_name_lower == "efficientnet" and "efficientnet" in reg_name_lower) or \
           (m_name_lower == "resnet18" and "resnet" in reg_name_lower):
            return {
                "accuracy": m.accuracy,
                "precision": m.precision_score,
                "recall": m.recall_score,
                "f1_score": m.f1_score,
                "f1": m.f1_score,
                "roc_auc": m.roc_auc,
                "inference_time_ms": m.inference_time_ms,
                "training_time_sec": m.training_time_sec,
                "memory_usage_mb": m.memory_usage_mb,
                "model_size_mb": m.model_size_mb,
            }
    return {}

@router.get("", response_model=List[Dict[str, Any]])
async def list_registered_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrieve all models from the Model Registry."""
    stmt = select(ModelRegistry).order_by(ModelRegistry.created_at.desc())
    results = (await db.execute(stmt)).scalars().all()
    
    models = []
    for r in results:
        # Fetch versions
        version_stmt = select(ModelVersion).where(ModelVersion.registry_id == r.id).order_by(ModelVersion.created_at.desc())
        versions = (await db.execute(version_stmt)).scalars().all()
        
        version_list = []
        for v in versions:
            v_metrics = v.metrics_json or await get_model_metrics(db, r)
            version_list.append({
                "version": v.version,
                "is_active": v.is_active,
                "metrics": v_metrics,
                "params": v.params_json or {},
                "created_at": v.created_at.isoformat()
            })
            
        if not version_list:
            v_metrics = await get_model_metrics(db, r)
            version_list.append({
                "version": "v1",
                "is_active": True,
                "metrics": v_metrics,
                "params": {},
                "created_at": r.created_at.isoformat()
            })
            
        models.append({
            "id": r.id,
            "name": r.name,
            "task_type": r.task_type,
            "description": r.description,
            "stage": r.stage.value if hasattr(r.stage, 'value') else r.stage,
            "mlflow_model_uri": r.mlflow_model_uri,
            "mlflow_run_id": r.mlflow_run_id,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
            "versions": version_list
        })
    return models

@router.get("/{model_id}", response_model=Dict[str, Any])
async def get_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get registry detail for a specific model."""
    stmt = select(ModelRegistry).where(ModelRegistry.id == model_id)
    model = (await db.execute(stmt)).scalar()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found.")
        
    version_stmt = select(ModelVersion).where(ModelVersion.registry_id == model.id).order_by(ModelVersion.created_at.desc())
    versions = (await db.execute(version_stmt)).scalars().all()
    
    version_list = []
    for v in versions:
        v_metrics = v.metrics_json or await get_model_metrics(db, model)
        version_list.append({
            "version": v.version,
            "is_active": v.is_active,
            "metrics": v_metrics,
            "params": v.params_json or {},
            "created_at": v.created_at.isoformat()
        })
        
    if not version_list:
        v_metrics = await get_model_metrics(db, model)
        version_list.append({
            "version": "v1",
            "is_active": True,
            "metrics": v_metrics,
            "params": {},
            "created_at": model.created_at.isoformat()
        })
        
    return {
        "id": model.id,
        "name": model.name,
        "task_type": model.task_type,
        "description": model.description,
        "stage": model.stage.value if hasattr(model.stage, 'value') else model.stage,
        "mlflow_model_uri": model.mlflow_model_uri,
        "mlflow_run_id": model.mlflow_run_id,
        "created_at": model.created_at.isoformat(),
        "updated_at": model.updated_at.isoformat(),
        "versions": version_list
    }

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_model(
    name: str,
    task_type: str,
    mlflow_run_id: str,
    mlflow_model_uri: str,
    description: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Register a new model from an MLflow run."""
    # Check if name already exists
    stmt = select(ModelRegistry).where(ModelRegistry.name == name)
    existing = (await db.execute(stmt)).scalar()
    
    if existing:
        registry_id = existing.id
        # Calculate new version
        ver_stmt = select(ModelVersion).where(ModelVersion.registry_id == registry_id).order_by(ModelVersion.created_at.desc())
        last_ver = (await db.execute(ver_stmt)).scalar()
        new_ver_str = f"v{int(last_ver.version[1:]) + 1}" if last_ver else "v1"
    else:
        # Create registry entry
        new_registry = ModelRegistry(
            name=name,
            task_type=task_type,
            description=description,
            stage="staging",
            mlflow_model_uri=mlflow_model_uri,
            mlflow_run_id=mlflow_run_id,
            created_by=current_user.id
        )
        db.add(new_registry)
        await db.commit()
        await db.refresh(new_registry)
        registry_id = new_registry.id
        new_ver_str = "v1"

    # Create new model version
    new_version = ModelVersion(
        registry_id=registry_id,
        version=new_ver_str,
        file_path=mlflow_model_uri,
        metrics_json={},
        params_json={},
        is_active=True
    )
    db.add(new_version)
    await db.commit()
    
    return {"status": "success", "model_id": registry_id, "version": new_ver_str}

@router.put("/{model_id}/stage")
async def transition_stage(
    model_id: int,
    stage: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin", "ml_engineer"))
):
    """Promote or demote a model version stage (staging, production, archived)."""
    stmt = select(ModelRegistry).where(ModelRegistry.id == model_id)
    model = (await db.execute(stmt)).scalar()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found.")
        
    model.stage = stage
    await db.commit()
    return {"status": "success", "new_stage": stage}

@router.delete("/{model_id}")
async def delete_model(
    model_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role("admin"))
):
    """Delete a registered model from the registry."""
    stmt = select(ModelRegistry).where(ModelRegistry.id == model_id)
    model = (await db.execute(stmt)).scalar()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found.")
        
    await db.delete(model)
    await db.commit()
    return {"status": "success", "message": "Model registry entry deleted."}
