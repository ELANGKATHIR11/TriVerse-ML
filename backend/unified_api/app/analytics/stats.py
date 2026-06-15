import os
from datetime import datetime, UTC
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List, Optional

from app.models.experiment import Experiment, ExperimentMetrics
from app.models.mlops import ModelRegistry, ModelVersion
from app.models.dataset import Dataset

class AnalyticsEngine:
    async def get_overview_stats(self, db: AsyncSession) -> Dict[str, Any]:
        # Count total experiments
        total_exp_stmt = select(func.count(Experiment.id))
        total_exps = (await db.execute(total_exp_stmt)).scalar() or 0

        # Count total models in registry
        total_model_stmt = select(func.count(ModelRegistry.id))
        total_models = (await db.execute(total_model_stmt)).scalar() or 0

        # Get recent experiments
        recent_exp_stmt = select(Experiment).order_by(desc(Experiment.created_at)).limit(5)
        recent_exps = (await db.execute(recent_exp_stmt)).scalars().all()

        return {
            "total_experiments": total_exps,
            "total_registered_models": total_models,
            "recent_activity": [
                {
                    "id": exp.id,
                    "name": exp.name,
                    "task_type": exp.task_type,
                    "status": exp.status.value if hasattr(exp.status, 'value') else exp.status,
                    "created_at": exp.created_at.isoformat() if exp.created_at else None
                }
                for exp in recent_exps
            ],
            "active_pipeline": {
                "status": "idle",
                "current_task": None
            }
        }

    async def get_task_summary(self, db: AsyncSession, task_type: str) -> Dict[str, Any]:
        # Count experiments of this task type
        exp_stmt = select(func.count(Experiment.id)).where(Experiment.task_type == task_type)
        count_exps = (await db.execute(exp_stmt)).scalar() or 0

        # Average accuracy and best performance
        metrics_stmt = select(ExperimentMetrics).join(Experiment).where(Experiment.task_type == task_type)
        metrics = (await db.execute(metrics_stmt)).scalars().all()

        avg_acc = 0.0
        best_acc = 0.0
        if metrics:
            accuracies = [m.accuracy for m in metrics if m.accuracy is not None]
            if accuracies:
                avg_acc = sum(accuracies) / len(accuracies)
                best_acc = max(accuracies)

        return {
            "task_type": task_type,
            "experiment_count": count_exps,
            "average_accuracy": float(avg_acc),
            "best_accuracy": float(best_acc),
            "model_counts": {
                "production": len([m for m in metrics if getattr(m, 'status', '') == 'production']),
                "staging": len([m for m in metrics if getattr(m, 'status', '') == 'staging'])
            }
        }

    async def get_leaderboard(self, db: AsyncSession, task_type: Optional[str] = None, sort_by: str = "weighted_score") -> List[Dict[str, Any]]:
        # Query all metrics
        query = select(ExperimentMetrics, Experiment).join(Experiment)
        if task_type:
            query = query.where(Experiment.task_type == task_type)

        # Ordering
        if sort_by == "accuracy":
            query = query.order_by(desc(ExperimentMetrics.accuracy))
        elif sort_by == "inference_time":
            query = query.order_by(ExperimentMetrics.inference_time_ms)
        else:
            # default to accuracy sorting
            query = query.order_by(desc(ExperimentMetrics.accuracy))

        results = (await db.execute(query)).all()
        
        leaderboard = []
        for rank, (metric, exp) in enumerate(results, 1):
            acc = metric.accuracy or 0.0
            prec = metric.precision_score or 0.0
            rec = metric.recall_score or 0.0
            inf_time = metric.inference_time_ms or 10.0
            tr_time = metric.training_time_sec or 10.0
            
            # Normalize speeds to [0, 1] range
            inf_score = 1.0 - (min(inf_time, 100.0) / 100.0)
            tr_score = 1.0 - (min(tr_time, 3600.0) / 3600.0)
            
            weighted_score = (acc * 0.4) + (prec * 0.2) + (rec * 0.2) + (inf_score * 0.1) + (tr_score * 0.1)
            
            leaderboard.append({
                "rank": rank,
                "model_name": metric.model_name,
                "task_type": exp.task_type,
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1_score": metric.f1_score or 0.0,
                "inference_time_ms": inf_time,
                "training_time_sec": tr_time,
                "weighted_score": float(weighted_score)
            })
            
        # Re-sort leaderboard based on weighted_score
        leaderboard = sorted(leaderboard, key=lambda x: x["weighted_score"], reverse=True)
        for idx, entry in enumerate(leaderboard, 1):
            entry["rank"] = idx
            
        return leaderboard

    async def get_model_comparison(self, db: AsyncSession, model_list: List[str]) -> Dict[str, Any]:
        # Fetch metrics for the list of models
        stmt = select(ExperimentMetrics).where(ExperimentMetrics.model_name.in_(model_list))
        metrics = (await db.execute(stmt)).scalars().all()

        return {
            "comparison": [
                {
                    "model_name": m.model_name,
                    "accuracy": m.accuracy or 0.0,
                    "precision": m.precision_score or 0.0,
                    "recall": m.recall_score or 0.0,
                    "f1_score": m.f1_score or 0.0,
                    "roc_auc": m.roc_auc or 0.0,
                    "inference_time_ms": m.inference_time_ms or 10.0,
                    "training_time_sec": m.training_time_sec or 0.0,
                    "model_size_mb": m.model_size_mb or 20.0
                }
                for m in metrics
            ]
        }
