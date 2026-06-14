"""
disease/models.py - Training all 6 disease prediction models with MLflow logging.

Models:
  1. Logistic Regression
  2. SVM (RBF kernel)
  3. Random Forest
  4. XGBoost (GPU)
  5. CatBoost (GPU)
  6. MLP (sklearn)

All train_* methods are sync but exposed async via run_in_executor.
"""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Awaitable

import mlflow
import mlflow.catboost
import mlflow.sklearn
import numpy as np
from catboost import CatBoostClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier

from app.ml.base import ModelResult, compute_memory_usage, get_model_size_mb, measure_inference_time

logger = logging.getLogger(__name__)

_EXECUTOR = ThreadPoolExecutor(max_workers=2)

MLFLOW_EXPERIMENT_BASE = "disease_prediction"


# ---------------------------------------------------------------------------
# Helper: async wrapper
# ---------------------------------------------------------------------------

async def _run_in_executor(fn: Callable, *args: Any) -> Any:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_EXECUTOR, fn, *args)


# ---------------------------------------------------------------------------
# Trainer
# ---------------------------------------------------------------------------


class DiseaseModelTrainer:
    """
    Trains all 6 disease prediction models.

    Parameters
    ----------
    X_train, X_test, y_train, y_test:
        Pre-processed numpy arrays.
    feature_names:
        List of feature name strings.
    dataset_name:
        One of ``'heart'``, ``'diabetes'``, ``'breast_cancer'``.
    """

    _MODEL_NAMES = [
        "logistic_regression",
        "svm",
        "random_forest",
        "xgboost",
        "catboost",
        "mlp",
    ]

    def __init__(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray,
        feature_names: list[str],
        dataset_name: str,
    ) -> None:
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.feature_names = feature_names
        self.dataset_name = dataset_name

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def train_all(
        self,
        ws_callback: Callable[[dict], Awaitable[None]] | None = None,
    ) -> list[ModelResult]:
        """
        Train all 6 models sequentially.

        Parameters
        ----------
        ws_callback:
            Optional async callable receiving progress dicts.

        Returns
        -------
        list[ModelResult]
        """
        results: list[ModelResult] = []
        total = len(self._MODEL_NAMES)

        for idx, model_name in enumerate(self._MODEL_NAMES):
            logger.info(
                "[disease/%s] training %s (%d/%d)",
                self.dataset_name, model_name, idx + 1, total,
            )

            if ws_callback:
                await ws_callback({
                    "model": model_name,
                    "dataset": self.dataset_name,
                    "status": "started",
                    "index": idx,
                    "total": total,
                })

            result = await self.train_single(model_name)
            results.append(result)

            if ws_callback:
                await ws_callback({
                    "model": model_name,
                    "dataset": self.dataset_name,
                    "status": "completed",
                    "index": idx,
                    "total": total,
                    "result": result.to_dict(),
                })

        return results

    async def train_single(
        self,
        model_name: str,
        hyperparams: dict[str, Any] | None = None,
    ) -> ModelResult:
        """
        Train a single model by name.

        Parameters
        ----------
        model_name:
            One of the _MODEL_NAMES.
        hyperparams:
            Optional override dict.

        Returns
        -------
        ModelResult
        """
        dispatch: dict[str, Callable] = {
            "logistic_regression": self._train_logistic_regression,
            "svm": self._train_svm,
            "random_forest": self._train_random_forest,
            "xgboost": self._train_xgboost,
            "catboost": self._train_catboost,
            "mlp": self._train_mlp,
        }
        if model_name not in dispatch:
            raise ValueError(f"Unknown model '{model_name}'. Choose from {list(dispatch)}")

        fn = dispatch[model_name]
        result = await _run_in_executor(fn, hyperparams)
        return result

    # ------------------------------------------------------------------
    # Individual model trainers (sync)
    # ------------------------------------------------------------------

    def _train_logistic_regression(self, hyperparams: dict | None = None) -> ModelResult:
        params: dict[str, Any] = {
            "C": 1.0,
            "max_iter": 1000,
            "solver": "lbfgs",
            "class_weight": "balanced",
            "random_state": 42,
        }
        if hyperparams:
            params.update(hyperparams)

        t0 = time.perf_counter()
        model = LogisticRegression(**params)
        model.fit(self.X_train, self.y_train)
        train_time = time.perf_counter() - t0

        result = self._compute_metrics(
            model, model_name="logistic_regression",
            train_time=train_time, params=params, best_hyperparams=params,
        )
        self._log_to_mlflow(result)
        return result

    def _train_svm(self, hyperparams: dict | None = None) -> ModelResult:
        params: dict[str, Any] = {
            "C": 1.0,
            "kernel": "rbf",
            "gamma": "scale",
            "probability": True,   # needed for AUC
            "class_weight": "balanced",
            "random_state": 42,
        }
        if hyperparams:
            params.update(hyperparams)

        t0 = time.perf_counter()
        model = SVC(**params)
        model.fit(self.X_train, self.y_train)
        train_time = time.perf_counter() - t0

        result = self._compute_metrics(
            model, model_name="svm",
            train_time=train_time, params=params, best_hyperparams=params,
        )
        self._log_to_mlflow(result)
        return result

    def _train_random_forest(self, hyperparams: dict | None = None) -> ModelResult:
        params: dict[str, Any] = {
            "n_estimators": 200,
            "max_depth": 10,
            "min_samples_split": 5,
            "min_samples_leaf": 2,
            "max_features": "sqrt",
            "class_weight": "balanced",
            "n_jobs": -1,
            "random_state": 42,
        }
        if hyperparams:
            params.update(hyperparams)

        t0 = time.perf_counter()
        model = RandomForestClassifier(**params)
        model.fit(self.X_train, self.y_train)
        train_time = time.perf_counter() - t0

        result = self._compute_metrics(
            model, model_name="random_forest",
            train_time=train_time, params=params, best_hyperparams=params,
        )
        self._log_to_mlflow(result)
        return result

    def _train_xgboost(self, hyperparams: dict | None = None) -> ModelResult:
        """XGBoost with GPU histogram."""
        # Compute scale_pos_weight for class imbalance
        neg = (self.y_train == 0).sum()
        pos = (self.y_train == 1).sum()
        scale_pos_weight = float(neg / max(pos, 1))

        params: dict[str, Any] = {
            "n_estimators": 500,
            "learning_rate": 0.05,
            "max_depth": 6,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
            "reg_alpha": 0.1,
            "reg_lambda": 1.0,
            "scale_pos_weight": scale_pos_weight,
            "tree_method": "hist",
            "device": "cuda",
            "eval_metric": "auc",
            "use_label_encoder": False,
            "random_state": 42,
            "n_jobs": 1,
        }
        if hyperparams:
            params.update(hyperparams)

        # XGBoost ≥ 2.0 uses 'device' instead of 'tree_method'
        xgb_params = dict(params)
        # Remove use_label_encoder if XGBoost >= 2.0
        xgb_params.pop("use_label_encoder", None)

        t0 = time.perf_counter()
        model = XGBClassifier(**xgb_params)
        model.fit(
            self.X_train, self.y_train,
            eval_set=[(self.X_test, self.y_test)],
            verbose=False,
        )
        train_time = time.perf_counter() - t0

        result = self._compute_metrics(
            model, model_name="xgboost",
            train_time=train_time, params=params, best_hyperparams=params,
        )
        self._log_to_mlflow(result)
        return result

    def _train_catboost(self, hyperparams: dict | None = None) -> ModelResult:
        params: dict[str, Any] = {
            "iterations": 500,
            "learning_rate": 0.05,
            "depth": 6,
            "loss_function": "Logloss",
            "eval_metric": "AUC",
            "auto_class_weights": "Balanced",
            "task_type": "GPU",
            "devices": "0",
            "random_seed": 42,
            "verbose": 0,
        }
        if hyperparams:
            params.update(hyperparams)

        t0 = time.perf_counter()
        model = CatBoostClassifier(**params)
        model.fit(
            self.X_train, self.y_train,
            eval_set=(self.X_test, self.y_test),
            early_stopping_rounds=50,
        )
        train_time = time.perf_counter() - t0

        result = self._compute_metrics(
            model, model_name="catboost",
            train_time=train_time, params=params, best_hyperparams=params,
        )
        self._log_to_mlflow(result)
        return result

    def _train_mlp(self, hyperparams: dict | None = None) -> ModelResult:
        params: dict[str, Any] = {
            "hidden_layer_sizes": (128, 64, 32),
            "activation": "relu",
            "solver": "adam",
            "alpha": 1e-4,
            "batch_size": 64,
            "learning_rate_init": 1e-3,
            "max_iter": 500,
            "early_stopping": True,
            "validation_fraction": 0.1,
            "n_iter_no_change": 20,
            "random_state": 42,
        }
        if hyperparams:
            params.update(hyperparams)

        t0 = time.perf_counter()
        model = MLPClassifier(**params)
        model.fit(self.X_train, self.y_train)
        train_time = time.perf_counter() - t0

        result = self._compute_metrics(
            model, model_name="mlp",
            train_time=train_time, params=params, best_hyperparams=params,
        )
        self._log_to_mlflow(result)
        return result

    # ------------------------------------------------------------------
    # Metrics computation
    # ------------------------------------------------------------------

    def _compute_metrics(
        self,
        model: Any,
        model_name: str,
        train_time: float,
        params: dict[str, Any],
        best_hyperparams: dict[str, Any],
    ) -> ModelResult:
        """Compute all classification metrics and build a ModelResult."""
        import os
        import joblib
        os.makedirs("trained_models/disease", exist_ok=True)
        joblib.dump(model, f"trained_models/disease/{model_name}.joblib")
        # Preprocessor will be saved at train_all.py or training route
        y_pred = model.predict(self.X_test)

        try:
            y_proba = model.predict_proba(self.X_test)[:, 1]
        except AttributeError:
            y_proba = y_pred.astype(float)

        acc = float(accuracy_score(self.y_test, y_pred))
        prec = float(precision_score(self.y_test, y_pred, average="weighted", zero_division=0))
        rec = float(recall_score(self.y_test, y_pred, average="weighted", zero_division=0))
        f1 = float(f1_score(self.y_test, y_pred, average="weighted", zero_division=0))
        try:
            auc = float(roc_auc_score(self.y_test, y_proba))
        except ValueError:
            auc = 0.0

        clf_report: dict = classification_report(
            self.y_test, y_pred, output_dict=True, zero_division=0
        )
        cm: list[list[int]] = confusion_matrix(self.y_test, y_pred).tolist()

        infer_ms = measure_inference_time(model, self.X_test, n_runs=50)
        mem_mb = compute_memory_usage()
        size_mb = get_model_size_mb(model)

        feat_imp = self._get_feature_importances(model)

        return ModelResult(
            model_name=model_name,
            task_type=f"disease_prediction_{self.dataset_name}",
            accuracy=acc,
            precision=prec,
            recall=rec,
            f1=f1,
            roc_auc=auc,
            training_time_sec=round(train_time, 4),
            inference_time_ms=round(infer_ms, 4),
            memory_usage_mb=round(mem_mb, 2),
            model_size_mb=round(size_mb, 4),
            params={str(k): str(v) for k, v in params.items()},
            best_hyperparams={str(k): str(v) for k, v in best_hyperparams.items()},
            classification_report=clf_report,
            confusion_matrix=cm,
            feature_importances=feat_imp,
        )

    def _get_feature_importances(self, model: Any) -> dict[str, float]:
        """Extract feature importances in a model-agnostic way."""
        importances: np.ndarray | None = None

        if hasattr(model, "feature_importances_"):
            importances = model.feature_importances_
        elif hasattr(model, "coef_"):
            coef = model.coef_
            if coef.ndim > 1:
                importances = np.abs(coef).mean(axis=0)
            else:
                importances = np.abs(coef)
        elif hasattr(model, "get_feature_importance"):
            try:
                importances = model.get_feature_importance()
            except Exception:
                pass

        if importances is None:
            return {}

        importances_norm = importances / (importances.sum() + 1e-12)
        names = self.feature_names[: len(importances_norm)]
        return {name: float(imp) for name, imp in zip(names, importances_norm)}

    # ------------------------------------------------------------------
    # MLflow logging
    # ------------------------------------------------------------------

    def _log_to_mlflow(self, result: ModelResult) -> None:
        """Log params, metrics to MLflow under disease_prediction experiment."""
        experiment_name = f"{MLFLOW_EXPERIMENT_BASE}_{self.dataset_name}"
        try:
            mlflow.set_experiment(experiment_name)
            with mlflow.start_run(run_name=result.model_name, nested=True):
                mlflow.set_tags({
                    "model_name": result.model_name,
                    "task_type": result.task_type,
                    "dataset": self.dataset_name,
                })

                safe_params = {k: str(v) for k, v in result.best_hyperparams.items()}
                mlflow.log_params(safe_params)

                mlflow.log_metrics({
                    "accuracy": result.accuracy,
                    "precision": result.precision,
                    "recall": result.recall,
                    "f1": result.f1,
                    "roc_auc": result.roc_auc,
                    "training_time_sec": result.training_time_sec,
                    "inference_time_ms": result.inference_time_ms,
                    "model_size_mb": result.model_size_mb,
                    "memory_usage_mb": result.memory_usage_mb,
                })

                for feat, imp in result.feature_importances.items():
                    mlflow.log_metric(f"fi_{feat[:50]}", imp)

        except Exception as exc:
            logger.warning("[disease] MLflow logging failed: %s", exc)
