"""
health.py — /health/* diagnostic endpoints for TriVerse AI

Exposes:
  GET /health/diagnostics  -> full startup diagnostic snapshot
  GET /health/live         -> simple liveness probe (Kubernetes / Electron health-check)
  GET /health/models       -> list of trained model files on disk
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter

from app.core.startup_diagnostics import get_cached_diagnostics, _check_model_files

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("/live")
async def liveness() -> dict[str, str]:
    """Simple liveness probe — always returns 200 if the process is alive."""
    return {"status": "alive", "service": "TriVerse AI Backend"}


@router.get("/diagnostics")
async def diagnostics() -> dict[str, Any]:
    """
    Return the cached startup diagnostic report.

    The report is populated once at application startup.
    It includes status of: database, MLflow, Ollama, and model files.
    """
    cached = get_cached_diagnostics()
    if not cached:
        # Re-run on demand if not cached yet (e.g. dev server cold-start)
        from app.core.startup_diagnostics import run_startup_diagnostics
        return await run_startup_diagnostics()
    return cached


@router.get("/models")
async def list_model_files() -> dict[str, Any]:
    """
    List all trained model files currently on disk with their sizes.
    Useful for the frontend Model Registry view.
    """
    result = _check_model_files()
    base_dir = Path(__file__).resolve().parents[3] / "trained_models"  # routes->api->app->unified_api


    file_details: list[dict[str, Any]] = []
    for task_type in ("credit", "disease", "vision"):
        task_dir = base_dir / task_type
        if task_dir.exists():
            for fp in sorted(task_dir.iterdir()):
                if fp.is_file():
                    size_mb = round(fp.stat().st_size / (1024 ** 2), 3)
                    file_details.append({
                        "task": task_type,
                        "filename": fp.name,
                        "size_mb": size_mb,
                        "path": str(fp),
                    })

    return {
        "status": result["status"],
        "summary": result["message"],
        "files": file_details,
        "missing": result.get("missing", []),
    }
