"""
disease/optuna_tuner.py - Optuna HPO for all 6 disease prediction models.

Each objective function defines the search space for its model and
returns ``1 - ROC-AUC`` as the objective to minimise.
MLflow integration via MLflowCallback logs every trial automatically.
"""

from __future__ import annotations

import logging
from typing import Any

import mlflow
import numpy as np
import optuna
from catboost import CatBoostClassifier
from optuna.integration.mlflow import MLflowCallback
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_score, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier

logger = logging.getLogger(__name__)
optuna.logging.set_verbosity(optuna.logging.WARNING)


class DiseaseOptunaOptimizer:
    """
    Optuna-based hyperparameter optimiser for disease prediction models.

    Parameters
    ----------
    X_train, X_test, y_train, y_test:
        Pre-processed numpy arrays.
    dataset_name:
        One of ``'heart'``, ``'diabetes'``, ``'breast_cancer'``.
    n_cv_folds:
        Folds for cross-validation objectives.
    """

    _OBJECTIVE_MAP: dict[str, str] = {
        "logistic_regression": "_objective_logistic",
        "svm": "_objective_svm",
        "random_forest": "_objective_random_forest",
        "xgboost": "_objective_xgboost",
        "catboost": "_objective_catboost",
        "mlp": "_objective_mlp",
    }

    def __init__(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray,
        dataset_name: str = "heart",
        n_cv_folds: int = 5,
    ) -> None:
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.dataset_name = dataset_name
        self.n_cv_folds = n_cv_folds
        self._cv = StratifiedKFold(n_splits=n_cv_folds, shuffle=True, random_state=42)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def optimize(self, model_name: str, n_trials: int = 30) -> dict[str, Any]:
        """
        Run Optuna study for the given model.

        Parameters
        ----------
        model_name:
            One of the keys in _OBJECTIVE_MAP.
        n_trials:
            Number of Optuna trials.

        Returns
        -------
        dict with keys:
            ``best_params``, ``best_value``, ``n_trials``, ``trial_history``
        """
        if model_name not in self._OBJECTIVE_MAP:
            raise ValueError(
                f"Unknown model '{model_name}'. Choose from {list(self._OBJECTIVE_MAP)}"
            )

        objective_fn = getattr(self, self._OBJECTIVE_MAP[model_name])
        experiment_name = f"disease_hpo_{self.dataset_name}_{model_name}"

        mlflow.set_experiment(experiment_name)
        mlflow_cb = MLflowCallback(
            tracking_uri=mlflow.get_tracking_uri(),
            metric_name="1_minus_auc",
        )

        study = optuna.create_study(
            direction="minimize",
            study_name=f"disease_{self.dataset_name}_{model_name}",
            sampler=optuna.samplers.TPESampler(seed=42),
            pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=0),
        )

        logger.info(
            "[disease hpo] Starting %d trials for %s on %s",
            n_trials, model_name, self.dataset_name,
        )
        study.optimize(
            objective_fn,
            n_trials=n_trials,
            callbacks=[mlflow_cb],
            show_progress_bar=False,
            catch=(Exception,),
        )

        trial_history = [
            {
                "trial_number": t.number,
                "value": t.value,
                "params": t.params,
                "state": str(t.state),
            }
            for t in study.trials
        ]

        logger.info(
            "[disease hpo] Best for %s/%s: %.4f | %s",
            self.dataset_name, model_name, study.best_value, study.best_params,
        )

        return {
            "best_params": study.best_params,
            "best_value": study.best_value,
            "n_trials": len(study.trials),
            "trial_history": trial_history,
        }

    # ------------------------------------------------------------------
    # Objective functions
    # ------------------------------------------------------------------

    def _objective_logistic(self, trial: optuna.Trial) -> float:
        C = trial.suggest_float("C", 1e-4, 100.0, log=True)
        solver = trial.suggest_categorical("solver", ["lbfgs", "saga", "liblinear"])
        max_iter = trial.suggest_int("max_iter", 100, 2000)
        class_weight = trial.suggest_categorical("class_weight", ["balanced", None])

        model = LogisticRegression(
            C=C,
            solver=solver,
            max_iter=max_iter,
            class_weight=class_weight,
            random_state=42,
            n_jobs=-1,
        )
        scores = cross_val_score(
            model, self.X_train, self.y_train,
            cv=self._cv, scoring="roc_auc", n_jobs=-1,
        )
        return float(1.0 - scores.mean())

    def _objective_svm(self, trial: optuna.Trial) -> float:
        C = trial.suggest_float("C", 1e-3, 100.0, log=True)
        kernel = trial.suggest_categorical("kernel", ["rbf", "poly", "sigmoid"])
        gamma = trial.suggest_categorical("gamma", ["scale", "auto"])
        degree = trial.suggest_int("degree", 2, 5)  # only used when kernel='poly'
        class_weight = trial.suggest_categorical("class_weight", ["balanced", None])

        model = SVC(
            C=C,
            kernel=kernel,
            gamma=gamma,
            degree=degree,
            class_weight=class_weight,
            probability=True,
            random_state=42,
        )
        scores = cross_val_score(
            model, self.X_train, self.y_train,
            cv=self._cv, scoring="roc_auc", n_jobs=-1,
        )
        return float(1.0 - scores.mean())

    def _objective_random_forest(self, trial: optuna.Trial) -> float:
        n_estimators = trial.suggest_int("n_estimators", 50, 500)
        max_depth = trial.suggest_int("max_depth", 2, 25)
        min_samples_split = trial.suggest_int("min_samples_split", 2, 30)
        min_samples_leaf = trial.suggest_int("min_samples_leaf", 1, 20)
        max_features = trial.suggest_categorical("max_features", ["sqrt", "log2"])
        class_weight = trial.suggest_categorical(
            "class_weight", ["balanced", "balanced_subsample"]
        )

        model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            max_features=max_features,
            class_weight=class_weight,
            n_jobs=-1,
            random_state=42,
        )
        scores = cross_val_score(
            model, self.X_train, self.y_train,
            cv=self._cv, scoring="roc_auc", n_jobs=-1,
        )
        return float(1.0 - scores.mean())

    def _objective_xgboost(self, trial: optuna.Trial) -> float:
        """XGBoost objective — GPU training, train/val split instead of CV."""
        n_estimators = trial.suggest_int("n_estimators", 100, 1000)
        learning_rate = trial.suggest_float("learning_rate", 1e-3, 0.3, log=True)
        max_depth = trial.suggest_int("max_depth", 3, 10)
        subsample = trial.suggest_float("subsample", 0.5, 1.0)
        colsample_bytree = trial.suggest_float("colsample_bytree", 0.5, 1.0)
        reg_alpha = trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True)
        reg_lambda = trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True)
        min_child_weight = trial.suggest_int("min_child_weight", 1, 10)

        X_tr, X_val, y_tr, y_val = train_test_split(
            self.X_train, self.y_train,
            test_size=0.2, random_state=42, stratify=self.y_train,
        )

        neg = (y_tr == 0).sum()
        pos = (y_tr == 1).sum()
        scale_pos_weight = float(neg / max(pos, 1))

        model = XGBClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            subsample=subsample,
            colsample_bytree=colsample_bytree,
            reg_alpha=reg_alpha,
            reg_lambda=reg_lambda,
            min_child_weight=min_child_weight,
            scale_pos_weight=scale_pos_weight,
            tree_method="hist",
            device="cuda",
            eval_metric="auc",
            random_state=42,
            n_jobs=1,
        )
        model.fit(
            X_tr, y_tr,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )
        y_proba = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, y_proba)
        return float(1.0 - auc)

    def _objective_catboost(self, trial: optuna.Trial) -> float:
        iterations = trial.suggest_int("iterations", 100, 1000)
        learning_rate = trial.suggest_float("learning_rate", 1e-3, 0.3, log=True)
        depth = trial.suggest_int("depth", 3, 10)
        l2_leaf_reg = trial.suggest_float("l2_leaf_reg", 1.0, 10.0)
        bagging_temperature = trial.suggest_float("bagging_temperature", 0.0, 1.0)
        border_count = trial.suggest_int("border_count", 32, 255)

        X_tr, X_val, y_tr, y_val = train_test_split(
            self.X_train, self.y_train,
            test_size=0.2, random_state=42, stratify=self.y_train,
        )

        model = CatBoostClassifier(
            iterations=iterations,
            learning_rate=learning_rate,
            depth=depth,
            l2_leaf_reg=l2_leaf_reg,
            bagging_temperature=bagging_temperature,
            border_count=border_count,
            loss_function="Logloss",
            eval_metric="AUC",
            auto_class_weights="Balanced",
            task_type="GPU",
            devices="0",
            random_seed=42,
            verbose=0,
        )
        model.fit(
            X_tr, y_tr,
            eval_set=(X_val, y_val),
            early_stopping_rounds=30,
        )
        y_proba = model.predict_proba(X_val)[:, 1]
        auc = roc_auc_score(y_val, y_proba)
        return float(1.0 - auc)

    def _objective_mlp(self, trial: optuna.Trial) -> float:
        n_layers = trial.suggest_int("n_layers", 1, 4)
        layer_size = trial.suggest_categorical("layer_size", [32, 64, 128, 256])
        hidden_layer_sizes = tuple([layer_size] * n_layers)
        activation = trial.suggest_categorical("activation", ["relu", "tanh", "logistic"])
        alpha = trial.suggest_float("alpha", 1e-5, 1e-1, log=True)
        learning_rate_init = trial.suggest_float("learning_rate_init", 1e-4, 1e-1, log=True)
        batch_size = trial.suggest_categorical("batch_size", [16, 32, 64, 128])

        model = MLPClassifier(
            hidden_layer_sizes=hidden_layer_sizes,
            activation=activation,
            alpha=alpha,
            learning_rate_init=learning_rate_init,
            batch_size=batch_size,
            max_iter=300,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=15,
            random_state=42,
        )
        scores = cross_val_score(
            model, self.X_train, self.y_train,
            cv=self._cv, scoring="roc_auc", n_jobs=1,
        )
        return float(1.0 - scores.mean())
