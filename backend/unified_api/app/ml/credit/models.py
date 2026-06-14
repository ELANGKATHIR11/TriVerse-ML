"""
credit/models.py - Training all 5 credit scoring models with MLflow logging.

Models:
  1. Logistic Regression
  2. Decision Tree
  3. Random Forest
  4. CatBoost (GPU)
  5. MLP (sklearn)

All train_* methods are sync but exposed as async via run_in_executor.
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
from sklearn.tree import DecisionTreeClassifier

from app.ml.base import ModelResult, compute_memory_usage, get_model_size_mb, measure_inference_time

logger = logging.getLogger(__name__)

_EXECUTOR = ThreadPoolExecutor(max_workers=2)

MLFLOW_EXPERIMENT_BASE = "credit_scoring"


# ---------------------------------------------------------------------------
# Helper: async wrapper
# ---------------------------------------------------------------------------

async def _run_in_executor(fn: Callable, *args: Any) -> Any:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(_EXECUTOR, fn, *args)


# ---------------------------------------------------------------------------
# Trainer
# ---------------------------------------------------------------------------


class CreditModelTrainer:
    """
    Trains all 5 credit scoring models.

    Parameters
    ----------
    X_train, X_test, y_train, y_test:
        Pre-processed numpy arrays.
    feature_names:
        List of feature name strings (length == X_train.shape[1]).
    preprocessor:
        Fitted sklearn Pipeline (stored for MLflow logging).
    """

    _MODEL_NAMES = [
        "logistic_regression",
        "decision_tree",
        "random_forest",
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
        preprocessor: Any,
    ) -> None:
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.feature_names = feature_names
        self.preprocessor = preprocessor

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def train_all(
        self,
        session_id: str,
        ws_callback: Callable[[dict], Awaitable[None]] | None = None,
    ) -> list[ModelResult]:
        """
        Train all 5 models sequentially.

        Parameters
        ----------
        session_id:
            Unique identifier for this training run (used as MLflow run tag).
        ws_callback:
            Optional async callable invoked after each model finishes.
            Receives a progress dict: ``{model, status, result, index, total}``.

        Returns
        -------
        list[ModelResult]
            One result per model.
        """
        results: list[ModelResult] = []
        total = len(self._MODEL_NAMES)

        for idx, model_name in enumerate(self._MODEL_NAMES):
            logger.info("[credit] training %s (%d/%d) session=%s", model_name, idx + 1, total, session_id)

            if ws_callback:
                await ws_callback({
                    "model": model_name,
                    "status": "started",
                    "index": idx,
                    "total": total,
                })

            result = await self.train_single(model_name)
            results.append(result)

            if ws_callback:
                await ws_callback({
                    "model": model_name,
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
            One of ``logistic_regression``, ``decision_tree``, ``random_forest``,
            ``catboost``, ``mlp``.
        hyperparams:
            Optional dict of hyperparameters to override defaults.

        Returns
        -------
        ModelResult
        """
        dispatch: dict[str, Callable] = {
            "logistic_regression": self._train_logistic_regression,
            "decision_tree": self._train_decision_tree,
            "random_forest": self._train_random_forest,
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

        logger.info("[credit] Logistic Regression params=%s", params)
        t0 = time.perf_counter()
        model = LogisticRegression(**params)
        model.fit(self.X_train, self.y_train)
        train_time = time.perf_counter() - t0

        result = self._compute_metrics(
            model, self.X_test, self.y_test,
            model_name="logistic_regression",
            train_time=train_time,
            params=params,
            best_hyperparams=params,
        )
        self._log_to_mlflow(result, experiment_name=MLFLOW_EXPERIMENT_BASE)
        return result

    def _train_decision_tree(self, hyperparams: dict | None = None) -> ModelResult:
        params: dict[str, Any] = {
            "max_depth": 8,
            "min_samples_split": 20,
            "min_samples_leaf": 10,
            "class_weight": "balanced",
            "random_state": 42,
        }
        if hyperparams:
            params.update(hyperparams)

        logger.info("[credit] Decision Tree params=%s", params)
        t0 = time.perf_counter()
        model = DecisionTreeClassifier(**params)
        model.fit(self.X_train, self.y_train)
        train_time = time.perf_counter() - t0

        result = self._compute_metrics(
            model, self.X_test, self.y_test,
            model_name="decision_tree",
            train_time=train_time,
            params=params,
            best_hyperparams=params,
        )
        self._log_to_mlflow(result, experiment_name=MLFLOW_EXPERIMENT_BASE)
        return result

    def _train_random_forest(self, hyperparams: dict | None = None) -> ModelResult:
        params: dict[str, Any] = {
            "n_estimators": 200,
            "max_depth": 12,
            "min_samples_split": 10,
            "min_samples_leaf": 5,
            "max_features": "sqrt",
            "class_weight": "balanced",
            "n_jobs": -1,
            "random_state": 42,
        }
        if hyperparams:
            params.update(hyperparams)

        logger.info("[credit] Random Forest params=%s", params)
        t0 = time.perf_counter()
        model = RandomForestClassifier(**params)
        model.fit(self.X_train, self.y_train)
        train_time = time.perf_counter() - t0

        result = self._compute_metrics(
            model, self.X_test, self.y_test,
            model_name="random_forest",
            train_time=train_time,
            params=params,
            best_hyperparams=params,
        )
        self._log_to_mlflow(result, experiment_name=MLFLOW_EXPERIMENT_BASE)
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

        logger.info("[credit] CatBoost params=%s", params)
        t0 = time.perf_counter()
        model = CatBoostClassifier(**params)
        model.fit(
            self.X_train, self.y_train,
            eval_set=(self.X_test, self.y_test),
            early_stopping_rounds=50,
        )
        train_time = time.perf_counter() - t0

        result = self._compute_metrics(
            model, self.X_test, self.y_test,
            model_name="catboost",
            train_time=train_time,
            params=params,
            best_hyperparams=params,
        )
        self._log_to_mlflow(result, experiment_name=MLFLOW_EXPERIMENT_BASE)
        return result

    def _train_mlp(self, hyperparams: dict | None = None) -> ModelResult:
        params: dict[str, Any] = {
            "hidden_layer_sizes": (256, 128, 64),
            "activation": "relu",
            "solver": "adam",
            "alpha": 1e-4,
            "batch_size": 512,
            "learning_rate_init": 1e-3,
            "max_iter": 300,
            "early_stopping": True,
            "validation_fraction": 0.1,
            "n_iter_no_change": 15,
            "random_state": 42,
        }
        if hyperparams:
            params.update(hyperparams)

        logger.info("[credit] MLP params=%s", params)
        t0 = time.perf_counter()
        model = MLPClassifier(**params)
        model.fit(self.X_train, self.y_train)
        train_time = time.perf_counter() - t0

        result = self._compute_metrics(
            model, self.X_test, self.y_test,
            model_name="mlp",
            train_time=train_time,
            params=params,
            best_hyperparams=params,
        )
        self._log_to_mlflow(result, experiment_name=MLFLOW_EXPERIMENT_BASE)
        return result

    # ------------------------------------------------------------------
    # Metrics computation
    # ------------------------------------------------------------------

    def _compute_metrics(
        self,
        model: Any,
        X_test: np.ndarray,
        y_test: np.ndarray,
        model_name: str,
        train_time: float,
        params: dict[str, Any],
        best_hyperparams: dict[str, Any],
    ) -> ModelResult:
        """Compute all metrics and assemble a ModelResult."""
        import os
        import joblib
        os.makedirs("trained_models/credit", exist_ok=True)
        joblib.dump(model, f"trained_models/credit/{model_name}.joblib")
        if self.preprocessor is not None:
            joblib.dump(self.preprocessor, "trained_models/credit/preprocessor.joblib")

        y_pred = model.predict(X_test)

        # Probability for AUC
        try:
            y_proba = model.predict_proba(X_test)[:, 1]
        except AttributeError:
            y_proba = y_pred.astype(float)

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
        rec = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
        f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))
        try:
            auc = float(roc_auc_score(y_test, y_proba))
        except ValueError:
            auc = 0.0

        clf_report: dict = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
        cm: list[list[int]] = confusion_matrix(y_test, y_pred).tolist()

        infer_ms = measure_inference_time(model, X_test, n_runs=50)
        mem_mb = compute_memory_usage()
        size_mb = get_model_size_mb(model)

        # Feature importances
        feat_imp = self._get_feature_importances(model)

        return ModelResult(
            model_name=model_name,
            task_type="credit_scoring",
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
            # CatBoost
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

    def _log_to_mlflow(self, result: ModelResult, experiment_name: str) -> None:
        """Log params, metrics, and model artifact to MLflow."""
        try:
            mlflow.set_experiment(experiment_name)
            with mlflow.start_run(run_name=result.model_name, nested=True):
                # Tags
                mlflow.set_tags({
                    "model_name": result.model_name,
                    "task_type": result.task_type,
                })

                # Params
                safe_params = {k: str(v) for k, v in result.best_hyperparams.items()}
                mlflow.log_params(safe_params)

                # Metrics
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

                # Feature importances as metrics
                for feat, imp in result.feature_importances.items():
                    mlflow.log_metric(f"fi_{feat[:50]}", imp)

        except Exception as exc:
            logger.warning("[credit] MLflow logging failed: %s", exc)
