"""
F:\\3ml project\\backend\\app\\api\\routes\\mlflow_routes.py

MLflow proxy router – proxies requests to the MLflow tracking server.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.dependencies import get_current_active_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mlflow", tags=["MLflow"])

# MLflow tracking server base URL – override via env
MLFLOW_BASE_URL = "http://localhost:5000/api/2.0/mlflow"

_http_client: httpx.AsyncClient | None = None


def get_mlflow_client() -> httpx.AsyncClient:
    """Return a shared async HTTP client for MLflow API calls."""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(base_url=MLFLOW_BASE_URL, timeout=30.0)
    return _http_client


async def _mlflow_get(path: str, params: dict | None = None) -> dict[str, Any]:
    """Make a GET request to the MLflow REST API."""
    client = get_mlflow_client()
    try:
        response = await client.get(path, params=params or {})
        response.raise_for_status()
        return response.json()
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="MLflow tracking server is not reachable at " + MLFLOW_BASE_URL,
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail=f"MLflow API error: {exc.response.text}",
        )


# ---------------------------------------------------------------------------
# GET /mlflow/experiments
# ---------------------------------------------------------------------------


@router.get(
    "/experiments",
    summary="List all MLflow experiments",
    status_code=status.HTTP_200_OK,
)
async def list_mlflow_experiments(
    view_type: str = Query("ACTIVE_ONLY", description="ACTIVE_ONLY | DELETED_ONLY | ALL"),
    max_results: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Return all experiments from the MLflow tracking server."""
    data = await _mlflow_get(
        "/experiments/search",
        params={"view_type": view_type, "max_results": max_results},
    )
    experiments = data.get("experiments", [])
    return {
        "total": len(experiments),
        "experiments": [
            {
                "experiment_id": e.get("experiment_id"),
                "name": e.get("name"),
                "artifact_location": e.get("artifact_location"),
                "lifecycle_stage": e.get("lifecycle_stage"),
                "tags": e.get("tags", []),
                "creation_time": e.get("creation_time"),
                "last_update_time": e.get("last_update_time"),
            }
            for e in experiments
        ],
    }


# ---------------------------------------------------------------------------
# GET /mlflow/experiments/{id}/runs
# ---------------------------------------------------------------------------


@router.get(
    "/experiments/{experiment_id}/runs",
    summary="List runs for an MLflow experiment",
    status_code=status.HTTP_200_OK,
)
async def list_experiment_runs(
    experiment_id: str,
    max_results: int = Query(50, ge=1, le=500),
    order_by: str = Query("start_time DESC", description="Sort field and direction"),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Return all runs for a given MLflow experiment ID."""
    data = await _mlflow_get(
        "/runs/search",
        params={
            "experiment_ids": [experiment_id],
            "max_results": max_results,
            "order_by": [order_by],
        },
    )
    runs = data.get("runs", [])
    return {
        "experiment_id": experiment_id,
        "total": len(runs),
        "runs": [_serialize_run(r) for r in runs],
    }


# ---------------------------------------------------------------------------
# GET /mlflow/runs/{run_id}
# ---------------------------------------------------------------------------


@router.get(
    "/runs/{run_id}",
    summary="Get details for a specific MLflow run",
    status_code=status.HTTP_200_OK,
)
async def get_mlflow_run(
    run_id: str,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Return full details for a specific MLflow run."""
    data = await _mlflow_get("/runs/get", params={"run_id": run_id})
    run = data.get("run", {})
    return _serialize_run(run)


# ---------------------------------------------------------------------------
# GET /mlflow/runs/{run_id}/metrics
# ---------------------------------------------------------------------------


@router.get(
    "/runs/{run_id}/metrics",
    summary="Get metric history for a specific MLflow run",
    status_code=status.HTTP_200_OK,
)
async def get_run_metrics(
    run_id: str,
    metric_key: str | None = Query(None, description="Filter by a specific metric key"),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Return logged metric history for a run."""
    # First get the run to determine which metrics exist
    run_data = await _mlflow_get("/runs/get", params={"run_id": run_id})
    run = run_data.get("run", {})
    run_info = run.get("info", {})
    metrics_data = run.get("data", {}).get("metrics", [])

    # If a specific metric key is requested, fetch its full history
    if metric_key:
        history_data = await _mlflow_get(
            "/metrics/get-history",
            params={"run_id": run_id, "metric_key": metric_key},
        )
        return {
            "run_id": run_id,
            "metric_key": metric_key,
            "history": history_data.get("metrics", []),
        }

    # Otherwise return the latest value for each metric
    return {
        "run_id": run_id,
        "experiment_id": run_info.get("experiment_id"),
        "status": run_info.get("status"),
        "metrics": {m["key"]: m["value"] for m in metrics_data},
    }


# ---------------------------------------------------------------------------
# GET /mlflow/runs/{run_id}/params
# ---------------------------------------------------------------------------


@router.get(
    "/runs/{run_id}/params",
    summary="Get logged parameters for a specific MLflow run",
    status_code=status.HTTP_200_OK,
)
async def get_run_params(
    run_id: str,
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Return all logged parameters for a run."""
    data = await _mlflow_get("/runs/get", params={"run_id": run_id})
    run = data.get("run", {})
    params = run.get("data", {}).get("params", [])
    tags = run.get("data", {}).get("tags", [])
    run_info = run.get("info", {})

    return {
        "run_id": run_id,
        "experiment_id": run_info.get("experiment_id"),
        "run_name": run_info.get("run_name"),
        "status": run_info.get("status"),
        "params": {p["key"]: p["value"] for p in params},
        "tags": {t["key"]: t["value"] for t in tags},
    }


# ---------------------------------------------------------------------------
# Helper serializer
# ---------------------------------------------------------------------------


def _serialize_run(run: dict[str, Any]) -> dict[str, Any]:
    info = run.get("info", {})
    data = run.get("data", {})
    return {
        "run_id": info.get("run_id"),
        "experiment_id": info.get("experiment_id"),
        "run_name": info.get("run_name"),
        "status": info.get("status"),
        "start_time": info.get("start_time"),
        "end_time": info.get("end_time"),
        "artifact_uri": info.get("artifact_uri"),
        "lifecycle_stage": info.get("lifecycle_stage"),
        "metrics": {m["key"]: m["value"] for m in data.get("metrics", [])},
        "params": {p["key"]: p["value"] for p in data.get("params", [])},
        "tags": {t["key"]: t["value"] for t in data.get("tags", [])},
    }
