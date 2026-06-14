"""
startup_diagnostics.py — TriVerse AI Platform Startup Validator

Performs pre-flight checks on all critical services:
  - SQLite database connectivity
  - MLflow tracking server
  - Ollama LLM server + qwen2.5-coder:3b availability
  - Trained model files (credit / disease / vision)

Results are cached and exposed via /health/diagnostics endpoint.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# ── Model files expected on disk ────────────────────────────────────────────

_BASE_DIR = Path(__file__).resolve().parents[2]  # app/core -> app -> unified_api
_TRAINED = _BASE_DIR / "trained_models"


EXPECTED_MODELS: dict[str, list[str]] = {
    "credit": [
        "catboost.joblib",
        "logistic_regression.joblib",
        "mlp.joblib",
        "random_forest.joblib",
        "decision_tree.joblib",
        "preprocessor.joblib",
    ],
    "disease": [
        "catboost.joblib",
        "logistic_regression.joblib",
        "mlp.joblib",
        "random_forest.joblib",
        "svm.joblib",
        "xgboost.joblib",
        "preprocessor.joblib",
    ],
    "vision": [
        "cnn.h5",
        "resnet18.pth",
    ],
}

# ── Diagnostic result ────────────────────────────────────────────────────────

_diagnostic_cache: dict[str, Any] = {}


def get_cached_diagnostics() -> dict[str, Any]:
    """Return the most recent diagnostic snapshot (populated at startup)."""
    return _diagnostic_cache


# ── Individual checks ────────────────────────────────────────────────────────

async def _check_database(db_url: str) -> dict[str, Any]:
    """Verify that the SQLite database is accessible."""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text

        engine = create_async_engine(db_url, echo=False)
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        await engine.dispose()
        return {"status": "ok", "message": "Database reachable"}
    except Exception as exc:
        logger.error("[Diagnostics] DB check failed: %s", exc)
        return {"status": "error", "message": str(exc)}


async def _check_mlflow(tracking_uri: str) -> dict[str, Any]:
    """Verify MLflow REST API is reachable."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{tracking_uri}/api/2.0/mlflow/experiments/list")
            if res.status_code in (200, 404):  # 404 is fine — server is up
                return {"status": "ok", "message": f"MLflow reachable (HTTP {res.status_code})"}
            return {"status": "warning", "message": f"MLflow returned HTTP {res.status_code}"}
    except Exception as exc:
        logger.warning("[Diagnostics] MLflow check failed: %s", exc)
        return {"status": "warning", "message": f"MLflow unreachable: {exc}"}


async def _check_ollama(base_url: str, model: str) -> dict[str, Any]:
    """Check Ollama server and model availability; trigger pull if missing."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            res = await client.get(f"{base_url}/api/tags")
            if res.status_code != 200:
                return {"status": "warning", "message": f"Ollama returned HTTP {res.status_code}"}

            pulled_models = [m["name"] for m in res.json().get("models", [])]
            model_ready = any(model in m or m in model for m in pulled_models)

            if not model_ready:
                logger.info("[Diagnostics] Ollama model %s not pulled. Triggering background pull.", model)
                asyncio.create_task(_pull_ollama_model(base_url, model))
                return {
                    "status": "warning",
                    "message": f"Model '{model}' not pulled yet — pulling in background",
                }

            return {"status": "ok", "message": f"Ollama + model '{model}' ready"}
    except Exception as exc:
        logger.warning("[Diagnostics] Ollama check failed: %s", exc)
        return {"status": "warning", "message": f"Ollama unreachable: {exc}"}


async def _pull_ollama_model(base_url: str, model: str) -> None:
    try:
        async with httpx.AsyncClient(timeout=600.0) as client:
            await client.post(f"{base_url}/api/pull", json={"name": model})
        logger.info("[Diagnostics] Ollama model %s pulled successfully.", model)
    except Exception as exc:
        logger.error("[Diagnostics] Failed to pull Ollama model %s: %s", model, exc)


def _check_model_files() -> dict[str, Any]:
    """Verify all expected trained model files exist on disk."""
    missing: list[str] = []
    found: list[str] = []

    for task_type, filenames in EXPECTED_MODELS.items():
        task_dir = _TRAINED / task_type
        for fname in filenames:
            fp = task_dir / fname
            if fp.exists() and fp.stat().st_size > 0:
                found.append(f"{task_type}/{fname}")
            else:
                missing.append(f"{task_type}/{fname}")

    if not missing:
        return {
            "status": "ok",
            "message": f"All {len(found)} model files present",
            "found": found,
            "missing": [],
        }
    else:
        return {
            "status": "warning",
            "message": f"{len(missing)} model file(s) missing — run training first",
            "found": found,
            "missing": missing,
        }


# ── Master diagnostic runner ─────────────────────────────────────────────────

async def run_startup_diagnostics() -> dict[str, Any]:
    """
    Execute all pre-flight checks concurrently and cache the results.
    Called once during FastAPI lifespan startup.
    Returns the full diagnostic snapshot.
    """
    from app.core.config import settings

    logger.info("[Diagnostics] Running startup checks …")

    db_task = asyncio.create_task(_check_database(str(settings.DATABASE_URL)))
    mlflow_task = asyncio.create_task(_check_mlflow(settings.MLFLOW_TRACKING_URI))
    ollama_task = asyncio.create_task(_check_ollama(settings.OLLAMA_BASE_URL, settings.OLLAMA_MODEL))

    db_result, mlflow_result, ollama_result = await asyncio.gather(
        db_task, mlflow_task, ollama_task
    )
    model_result = _check_model_files()

    overall_statuses = {
        db_result["status"],
        mlflow_result["status"],
        ollama_result["status"],
        model_result["status"],
    }

    if "error" in overall_statuses:
        overall = "error"
    elif "warning" in overall_statuses:
        overall = "degraded"
    else:
        overall = "healthy"

    snapshot: dict[str, Any] = {
        "overall": overall,
        "timestamp": datetime.now(UTC).isoformat(),
        "checks": {
            "database": db_result,
            "mlflow": mlflow_result,
            "ollama": ollama_result,
            "model_files": model_result,
        },
        "platform": {
            "python_version": __import__("sys").version,
            "trained_models_dir": str(_TRAINED),
        },
    }

    _diagnostic_cache.clear()
    _diagnostic_cache.update(snapshot)

    logger.info("[Diagnostics] Startup check complete — overall: %s", overall)
    return snapshot
