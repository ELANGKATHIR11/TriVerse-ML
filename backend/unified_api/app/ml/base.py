"""
base.py - Shared base types and utilities for all ML pipelines.

Provides:
  - ModelResult dataclass (standardised metrics container)
  - measure_inference_time()
  - get_model_size_mb()
  - compute_memory_usage()
"""

from __future__ import annotations

import io
import os
import pickle
import time
from dataclasses import dataclass, field
from typing import Any

import numpy as np
import psutil


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class ModelResult:
    """Standardised output returned by every model trainer."""

    model_name: str
    task_type: str  # 'credit_scoring' | 'disease_prediction'

    # Core classification metrics
    accuracy: float
    precision: float
    recall: float
    f1: float
    roc_auc: float

    # Operational metrics
    training_time_sec: float
    inference_time_ms: float  # average per-sample, in ms
    memory_usage_mb: float
    model_size_mb: float

    # Hyper-parameters
    params: dict[str, Any]           # all params passed to the model constructor
    best_hyperparams: dict[str, Any]  # best params after HPO (same as params when no HPO)

    # Rich diagnostics
    classification_report: dict[str, Any]
    confusion_matrix: list[list[int]]
    feature_importances: dict[str, float]  # {feature_name: importance_value}

    # Explainability (may be None when computation is skipped)
    shap_values_b64: str | None = None   # base64-encoded PNG of SHAP summary plot
    lime_explanation: dict | None = None  # see ExplainabilityEngine.explain_lime()

    # Extra metadata
    extra: dict[str, Any] = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-serialisable representation."""
        return {
            "model_name": self.model_name,
            "task_type": self.task_type,
            "accuracy": self.accuracy,
            "precision": self.precision,
            "recall": self.recall,
            "f1": self.f1,
            "roc_auc": self.roc_auc,
            "training_time_sec": self.training_time_sec,
            "inference_time_ms": self.inference_time_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "model_size_mb": self.model_size_mb,
            "params": self.params,
            "best_hyperparams": self.best_hyperparams,
            "classification_report": self.classification_report,
            "confusion_matrix": self.confusion_matrix,
            "feature_importances": self.feature_importances,
            "shap_values_b64": self.shap_values_b64,
            "lime_explanation": self.lime_explanation,
            "extra": self.extra,
        }

    def summary(self) -> str:
        """One-line human-readable summary."""
        return (
            f"[{self.task_type}] {self.model_name} | "
            f"acc={self.accuracy:.4f} f1={self.f1:.4f} auc={self.roc_auc:.4f} | "
            f"train={self.training_time_sec:.2f}s infer={self.inference_time_ms:.3f}ms"
        )


# ---------------------------------------------------------------------------
# Utility: inference timing
# ---------------------------------------------------------------------------

def measure_inference_time(model: Any, X_test: np.ndarray, n_runs: int = 100) -> float:
    """
    Measure average per-sample inference latency.

    Runs the model ``n_runs`` times on the entire ``X_test`` array and
    returns the **per-sample** average in **milliseconds**.

    Parameters
    ----------
    model:
        Any object with a ``predict`` method (sklearn-compatible).
    X_test:
        Test feature matrix, shape (n_samples, n_features).
    n_runs:
        Number of repeated inference passes.

    Returns
    -------
    float
        Average per-sample inference time in milliseconds.
    """
    if len(X_test) == 0:
        return 0.0

    # Warm-up pass to avoid cold-start bias
    try:
        model.predict(X_test[:1])
    except Exception:
        pass

    elapsed_total = 0.0
    n_samples = len(X_test)

    for _ in range(n_runs):
        t0 = time.perf_counter()
        model.predict(X_test)
        elapsed_total += time.perf_counter() - t0

    avg_total_sec = elapsed_total / n_runs          # seconds for full X_test
    avg_per_sample_ms = (avg_total_sec / n_samples) * 1000.0
    return avg_per_sample_ms


# ---------------------------------------------------------------------------
# Utility: model size on disk
# ---------------------------------------------------------------------------

def get_model_size_mb(model: Any) -> float:
    """
    Estimate serialised model size using pickle.

    Parameters
    ----------
    model:
        Any picklable model object.

    Returns
    -------
    float
        Estimated size in megabytes.
    """
    buf = io.BytesIO()
    try:
        pickle.dump(model, buf)
        size_bytes = buf.tell()
    except Exception:
        # Fall back to 0 if the model is not picklable (e.g. some GPU models)
        return 0.0
    return size_bytes / (1024 ** 2)


# ---------------------------------------------------------------------------
# Utility: current process memory
# ---------------------------------------------------------------------------

def compute_memory_usage() -> float:
    """
    Return the current process RSS (Resident Set Size) in megabytes.

    Returns
    -------
    float
        RSS in MB.
    """
    process = psutil.Process(os.getpid())
    rss_bytes = process.memory_info().rss
    return rss_bytes / (1024 ** 2)
