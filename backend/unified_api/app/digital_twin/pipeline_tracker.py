from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from app.models.experiment import PipelineStatus

class DigitalTwinTracker:
    async def get_pipeline_status(self, db: AsyncSession, experiment_id: int) -> List[Dict[str, Any]]:
        """Retrieve full pipeline status and node diagnostics for an experiment."""
        stmt = select(PipelineStatus).where(PipelineStatus.experiment_id == experiment_id)
        results = (await db.execute(stmt)).scalars().all()
        
        status_list = []
        for ps in results:
            status_list.append({
                "id": ps.id,
                "experiment_id": ps.experiment_id,
                "stage": ps.stage,
                "status": ps.status,
                "started_at": ps.started_at.isoformat() if ps.started_at else None,
                "finished_at": ps.finished_at.isoformat() if ps.finished_at else None,
                "logs": ps.logs,
                "error_message": ps.error_message
            })
        return status_list

    async def get_replay_history(self, db: AsyncSession, experiment_id: int) -> List[Dict[str, Any]]:
        """Get historical state updates for replaying execution progress."""
        stmt = select(PipelineStatus).where(PipelineStatus.experiment_id == experiment_id).order_by(PipelineStatus.started_at)
        results = (await db.execute(stmt)).scalars().all()
        
        replay_list = []
        for ps in results:
            replay_list.append({
                "stage": ps.stage,
                "status": ps.status,
                "timestamp": ps.started_at.isoformat() if ps.started_at else None,
                "finished_at": ps.finished_at.isoformat() if ps.finished_at else None,
                "logs": ps.logs,
                "error_message": ps.error_message
            })
        return replay_list
