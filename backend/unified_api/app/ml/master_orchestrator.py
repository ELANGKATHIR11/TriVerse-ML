"""
master_orchestrator.py

MasterTrainingPipeline and TrainingOrchestrator for managing training executions, 
resource monitoring (GPU/RAM/Disk), retries, and job state.
"""

from __future__ import annotations
import os
import time
import asyncio
import logging
import psutil
import shutil
import torch
from pathlib import Path
from datetime import datetime, UTC
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.experiment import Experiment, ExperimentStatus, ExperimentMetrics, TrainingSession
from app.models.dataset import Dataset
from app.models.mlops import ModelRegistry

logger = logging.getLogger(__name__)

class ResourceMonitor:
    """Helper to check RAM, Disk, and CUDA GPU usage telemetry."""
    @staticmethod
    def get_telemetry() -> dict:
        ram = psutil.virtual_memory()
        disk = shutil.disk_usage(".")
        
        telemetry = {
            "ram_pct": ram.percent,
            "ram_used_gb": round(ram.used / (1024**3), 2),
            "disk_pct": round((disk.used / disk.total) * 100, 2),
            "gpu_name": "None",
            "gpu_vram_used_mb": 0.0,
            "gpu_temp_c": 45,  # fallback constant
            "gpu_util_pct": 0.0
        }
        
        if torch.cuda.is_available():
            telemetry["gpu_name"] = torch.cuda.get_device_name(0)
            telemetry["gpu_vram_used_mb"] = round(torch.cuda.memory_allocated(0) / (1024**2), 2)
            # Estimate GPU utilization from memory usage
            telemetry["gpu_util_pct"] = round((torch.cuda.memory_allocated(0) / torch.cuda.get_device_properties(0).total_memory) * 100, 2)
            
        return telemetry

class MasterTrainingPipeline:
    """Executes single models, tasks, or full suite, including retries and logging."""
    def __init__(self, experiment_id: int, user_id: int):
        self.experiment_id = experiment_id
        self.user_id = user_id

    async def execute_task_run(self, task_type: str, model_name: str | None = None, retries: int = 1) -> bool:
        """Runs training for a task type or a single model with retry logic."""
        attempt = 0
        success = False
        
        while attempt <= retries and not success:
            try:
                logger.info(f"Training attempt {attempt} for task {task_type}, model {model_name}")
                await self._run(task_type, model_name)
                success = True
            except Exception as e:
                attempt += 1
                logger.error(f"Error on attempt {attempt}: {e}")
                if attempt > retries:
                    async with AsyncSessionLocal() as db:
                        await db.execute(
                            update(Experiment)
                            .where(Experiment.id == self.experiment_id)
                            .values(status=ExperimentStatus.FAILED, finished_at=datetime.now(UTC))
                        )
                        await db.commit()
                    return False
                await asyncio.sleep(2)
        return True

    async def _run(self, task_type: str, model_name: str | None) -> None:
        async with AsyncSessionLocal() as db:
            # Load dataset details
            stmt = select(Experiment).where(Experiment.id == self.experiment_id)
            exp = (await db.execute(stmt)).scalar_one_or_none()
            if not exp:
                raise ValueError("Experiment not found")
                
            dataset_id = exp.dataset_id
            
            # Start actual training
            from app.api.routes.training import _run_training
            stop_event = asyncio.Event()
            
            # Call training script logic directly or invoke individual trainers
            await _run_training(
                session_id=f"run_master_{self.experiment_id}",
                experiment_id=self.experiment_id,
                dataset_id=dataset_id,
                task_type=task_type,
                epochs=exp.config_json.get("epochs", 5) if task_type == "handwriting" else 1,
                batch_size=exp.config_json.get("batch_size", 64),
                learning_rate=exp.config_json.get("learning_rate", 0.001),
                config=exp.config_json or {},
                stop_event=stop_event,
                user_id=self.user_id
            )

class TrainingOrchestrator:
    """Orchestrates job queues, resumes, and keeps global telemetry status."""
    _active_pipelines: dict[int, MasterTrainingPipeline] = {}

    @classmethod
    async def start_job(cls, experiment_id: int, task_type: str, user_id: int, model_name: str | None = None) -> str:
        pipeline = MasterTrainingPipeline(experiment_id, user_id)
        cls._active_pipelines[experiment_id] = pipeline
        
        # Run asynchronously in background task
        asyncio.create_task(pipeline.execute_task_run(task_type, model_name))
        return f"job_{experiment_id}"
