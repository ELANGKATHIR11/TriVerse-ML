"""
credit/optuna_tuner.py - Optuna HPO for all 5 credit scoring models.

Each objective function defines the search space for its respective model,
trains on the full training set (with internal CV for large datasets), and
returns 1 - ROC-AUC as the objective to minimise.

MLflow integration is handled via the MLflowCallback so every trial is
logged automatically.
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
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.neural_network import MLPClassifier
from sklearn.tree import DecisionTreeClassifier

logger = logging.getLogger(__name__)

optuna.logging.set_verbosity(optuna.logging.WARNING)

# ---------------------------------------------------------------------------
# Optimiser class
# ---------------------------------------------------------------------------


class CreditOptunaOptimizer:
    """
    Optuna-based hyperparameter optimiser for credit scoring models.

    Parameters
    ----------
    X_train, X_test, y_train, y_test:
        Pre-processed numpy arrays.
    n_cv_folds:
        Number of cross-validation folds used during optimisation.
    """

    _OBJECTIVE_MAP: dict[str, str] = {
        "logistic_regression": "_objective_logistic",
        "decision_tree": "_objective_decision_tree",
        "random_forest": "_objective_random_forest",
        "catboost": "_objective_catboost",
        "mlp": "_objective_mlp",
    }

    def __init__(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray,
        n_cv_folds: int = 3,
    ) -> None:
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
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
            ``best_params``, ``best_value``, ``n_trials``,
            ``trial_history`` (list of {trial_number, value, params})
        """
        if model_name not in self._OBJECTIVE_MAP:
            raise ValueError(
                f"Unknown model '{model_name}'. Choose from {list(self._OBJECTIVE_MAP)}"
            )

        objective_fn = getattr(self, self._OBJECTIVE_MAP[model_name])
        experiment_name = f"credit_hpo_{model_name}"

        mlflow.set_experiment(experiment_name)
        mlflow_cb = MLflowCallback(
            tracking_uri=mlflow.get_tracking_uri(),
            metric_name="1_minus_auc",
        )

        study = optuna.create_study(
            direction="minimize",
            study_name=f"credit_{model_name}",
            sampler=optuna.samplers.TPESampler(seed=42),
            pruner=optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=0),
        )

        logger.info("[credit hpo] Starting %d trials for %s", n_trials, model_name)
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
            "[credit hpo] Best for %s: %.4f | %s",
            model_name,
            study.best_value,
            study.best_params,
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
        solver = trial.suggest_categorical("solver", ["lbfgs", "saga"])
        max_iter = trial.suggest_int("max_iter", 200, 2000)
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

    def _objective_decision_tree(self, trial: optuna.Trial) -> float:
        max_depth = trial.suggest_int("max_depth", 2, 20)
        min_samples_split = trial.suggest_int("min_samples_split", 2, 50)
        min_samples_leaf = trial.suggest_int("min_samples_leaf", 1, 30)
        criterion = trial.suggest_categorical("criterion", ["gini", "entropy"])
        class_weight = trial.suggest_categorical("class_weight", ["balanced", None])

        model = DecisionTreeClassifier(
            max_depth=max_depth,
            min_samples_split=min_samples_split,
            min_samples_leaf=min_samples_leaf,
            criterion=criterion,
            class_weight=class_weight,
            random_state=42,
        )

        scores = cross_val_score(
            model, self.X_train, self.y_train,
            cv=self._cv, scoring="roc_auc", n_jobs=-1,
        )
        return float(1.0 - scores.mean())

    def _objective_random_forest(self, trial: optuna.Trial) -> float:
        n_estimators = trial.suggest_int("n_estimators", 50, 500)
        max_depth = trial.suggest_int("max_depth", 3, 20)
        min_samples_split = trial.suggest_int("min_samples_split", 2, 30)
        min_samples_leaf = trial.suggest_int("min_samples_leaf", 1, 20)
        max_features = trial.suggest_categorical("max_features", ["sqrt", "log2", None])
        class_weight = trial.suggest_categorical("class_weight", ["balanced", "balanced_subsample"])

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

    def _objective_catboost(self, trial: optuna.Trial) -> float:
        """CatBoost objective — GPU training, no sklearn CV (train/val split instead)."""
        iterations = trial.suggest_int("iterations", 100, 1000)
        learning_rate = trial.suggest_float("learning_rate", 1e-3, 0.3, log=True)
        depth = trial.suggest_int("depth", 4, 10)
        l2_leaf_reg = trial.suggest_float("l2_leaf_reg", 1.0, 10.0)
        bagging_temperature = trial.suggest_float("bagging_temperature", 0.0, 1.0)

        from sklearn.model_selection import train_test_split
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
        layer_size = trial.suggest_categorical("layer_size", [64, 128, 256, 512])
        hidden_layer_sizes = tuple([layer_size] * n_layers)

        activation = trial.suggest_categorical("activation", ["relu", "tanh"])
        alpha = trial.suggest_float("alpha", 1e-5, 1e-1, log=True)
        learning_rate_init = trial.suggest_float("learning_rate_init", 1e-4, 1e-1, log=True)
        batch_size = trial.suggest_categorical("batch_size", [128, 256, 512, 1024])

        model = MLPClassifier(
            hidden_layer_sizes=hidden_layer_sizes,
            activation=activation,
            alpha=alpha,
            learning_rate_init=learning_rate_init,
            batch_size=batch_size,
            max_iter=200,
            early_stopping=True,
            validation_fraction=0.1,
            n_iter_no_change=10,
            random_state=42,
        )

        scores = cross_val_score(
            model, self.X_train, self.y_train,
            cv=self._cv, scoring="roc_auc", n_jobs=1,  # MLP not safe with n_jobs=-1 in CV
        )
        return float(1.0 - scores.mean())
