"""
Optuna Hyperparameter Tuning for Handwriting Recognition Models.

Provides two optimisers:
- HandwritingOptunaOptimizer.optimize_cnn  — tunes CNN (learning_rate, batch_size, dropout, conv filters)
- HandwritingOptunaOptimizer.optimize_resnet — tunes ResNet18 (learning_rate, batch_size, weight_decay)

Both run synchronously (Optuna is sync) and return a dict summarising the
best trial and the full trial history.
"""

from __future__ import annotations

import gc
import logging
import time
from typing import Any

import numpy as np
import optuna
from optuna.samplers import CmaEsSampler, TPESampler

logger = logging.getLogger(__name__)

# Suppress Optuna's verbose INFO during trials
optuna.logging.set_verbosity(optuna.logging.WARNING)


class HandwritingOptunaOptimizer:
    """Wraps Optuna studies for CNN and ResNet18 hyperparameter search."""

    def __init__(self, storage_url: str | None = None) -> None:
        """
        Parameters
        ----------
        storage_url : optional SQLAlchemy DB URL for persistent storage.
                      Defaults to in-memory (None) for ad-hoc searches.
        """
        self.storage_url = storage_url

    # ------------------------------------------------------------------
    # CNN optimisation
    # ------------------------------------------------------------------

    def optimize_cnn(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray,
        n_trials: int = 20,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Tune CNN hyperparameters with Optuna TPE sampler.

        Search space
        ------------
        - learning_rate : log-uniform [1e-4, 1e-2]
        - batch_size    : categorical [64, 128, 256, 512]
        - dropout       : uniform [0.2, 0.6]
        - filters_1     : categorical [16, 32, 64]  (first Conv block)
        - filters_2     : categorical [32, 64, 128] (second Conv block)
        - filters_3     : categorical [64, 128, 256] (third Conv block)
        - dense_units   : categorical [128, 256, 512]

        Returns
        -------
        {
            "best_params": {...},
            "best_value": float,
            "n_trials": int,
            "trials": [{trial_number, params, value, duration_s}],
            "study_name": str,
        }
        """
        num_classes = len(np.unique(y_train))
        study_name = f"cnn_handwriting_{int(time.time())}"

        study = optuna.create_study(
            study_name=study_name,
            direction="maximize",
            sampler=TPESampler(seed=42),
            storage=self.storage_url,
            load_if_exists=False,
        )

        def objective(trial: optuna.Trial) -> float:
            import tensorflow as tf  # type: ignore[import]

            lr = trial.suggest_float("learning_rate", 1e-4, 1e-2, log=True)
            batch_size = trial.suggest_categorical("batch_size", [64, 128, 256, 512])
            dropout = trial.suggest_float("dropout", 0.2, 0.6)
            f1 = trial.suggest_categorical("filters_1", [16, 32, 64])
            f2 = trial.suggest_categorical("filters_2", [32, 64, 128])
            f3 = trial.suggest_categorical("filters_3", [64, 128, 256])
            dense_units = trial.suggest_categorical("dense_units", [128, 256, 512])
            epochs = trial.suggest_int("epochs", 5, 15)

            try:
                model = _build_cnn(num_classes, lr, dropout, f1, f2, f3, dense_units)
                history = model.fit(
                    X_train,
                    y_train,
                    epochs=epochs,
                    batch_size=batch_size,
                    validation_data=(X_test, y_test),
                    callbacks=[
                        tf.keras.callbacks.EarlyStopping(
                            monitor="val_accuracy",
                            patience=3,
                            restore_best_weights=True,
                        )
                    ],
                    verbose=0,
                )
                val_acc = max(history.history["val_accuracy"])
                logger.info(
                    "Trial %d — val_acc=%.4f  lr=%.5f  bs=%d  dropout=%.2f",
                    trial.number,
                    val_acc,
                    lr,
                    batch_size,
                    dropout,
                )
                return float(val_acc)
            except Exception as exc:
                logger.warning("CNN trial %d failed: %s", trial.number, exc)
                return 0.0
            finally:
                tf.keras.backend.clear_session()
                gc.collect()

        study.optimize(objective, n_trials=n_trials, timeout=timeout, show_progress_bar=False)

        return self._summarise_study(study)

    # ------------------------------------------------------------------
    # ResNet18 optimisation
    # ------------------------------------------------------------------

    def optimize_resnet(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray,
        n_trials: int = 20,
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Tune ResNet18 hyperparameters with Optuna TPE sampler.

        Search space
        ------------
        - learning_rate  : log-uniform [1e-4, 1e-1]
        - batch_size     : categorical [64, 128, 256, 512]
        - weight_decay   : log-uniform [1e-5, 1e-2]
        - momentum       : uniform [0.8, 0.99]
        - epochs         : int [5, 15]

        Returns
        -------
        Same structure as optimize_cnn.
        """
        import torch  # type: ignore[import]
        from torch.utils.data import DataLoader, TensorDataset  # type: ignore[import]

        num_classes = len(np.unique(y_train))
        study_name = f"resnet_handwriting_{int(time.time())}"

        study = optuna.create_study(
            study_name=study_name,
            direction="maximize",
            sampler=TPESampler(seed=42),
            storage=self.storage_url,
            load_if_exists=False,
        )

        # Pre-convert data once outside the trial closure
        X_train_t = _to_3ch_tensor(X_train)
        X_test_t = _to_3ch_tensor(X_test)
        y_train_t = torch.from_numpy(y_train.astype(np.int64))
        y_test_t = torch.from_numpy(y_test.astype(np.int64))

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        def objective(trial: optuna.Trial) -> float:
            import torchvision.models as tv_models  # type: ignore[import]

            lr = trial.suggest_float("learning_rate", 1e-4, 1e-1, log=True)
            batch_size = trial.suggest_categorical("batch_size", [64, 128, 256, 512])
            weight_decay = trial.suggest_float("weight_decay", 1e-5, 1e-2, log=True)
            momentum = trial.suggest_float("momentum", 0.80, 0.99)
            epochs = trial.suggest_int("epochs", 5, 15)

            try:
                model = _build_resnet18(num_classes, device)
                optimizer = torch.optim.SGD(
                    model.parameters(),
                    lr=lr,
                    momentum=momentum,
                    weight_decay=weight_decay,
                )
                criterion = torch.nn.CrossEntropyLoss()
                train_ds = TensorDataset(X_train_t, y_train_t)
                test_ds = TensorDataset(X_test_t, y_test_t)
                train_loader = DataLoader(
                    train_ds, batch_size=batch_size, shuffle=True, num_workers=0
                )
                test_loader = DataLoader(
                    test_ds, batch_size=batch_size, shuffle=False, num_workers=0
                )

                best_acc = 0.0
                patience_counter = 0
                for epoch in range(epochs):
                    model.train()
                    for x_b, y_b in train_loader:
                        x_b, y_b = x_b.to(device), y_b.to(device)
                        optimizer.zero_grad()
                        loss = criterion(model(x_b), y_b)
                        loss.backward()
                        optimizer.step()

                    # Validation
                    model.eval()
                    correct, total = 0, 0
                    with torch.no_grad():
                        for x_b, y_b in test_loader:
                            x_b, y_b = x_b.to(device), y_b.to(device)
                            preds = model(x_b).argmax(dim=1)
                            correct += (preds == y_b).sum().item()
                            total += len(y_b)
                    val_acc = correct / total

                    if val_acc > best_acc:
                        best_acc = val_acc
                        patience_counter = 0
                    else:
                        patience_counter += 1
                    if patience_counter >= 3:
                        break

                    # Optuna pruning support
                    trial.report(val_acc, epoch)
                    if trial.should_prune():
                        raise optuna.TrialPruned()

                logger.info(
                    "ResNet trial %d — val_acc=%.4f  lr=%.5f  bs=%d  wd=%.6f",
                    trial.number,
                    best_acc,
                    lr,
                    batch_size,
                    weight_decay,
                )
                return float(best_acc)
            except optuna.TrialPruned:
                raise
            except Exception as exc:
                logger.warning("ResNet trial %d failed: %s", trial.number, exc)
                return 0.0
            finally:
                del model
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()

        study.optimize(objective, n_trials=n_trials, timeout=timeout, show_progress_bar=False)
        return self._summarise_study(study)

    # ------------------------------------------------------------------
    # Shared summary helper
    # ------------------------------------------------------------------

    @staticmethod
    def _summarise_study(study: optuna.Study) -> dict[str, Any]:
        """Convert an Optuna study into a serialisable summary dict."""
        best_trial = study.best_trial
        trials_summary = [
            {
                "trial_number": t.number,
                "params": t.params,
                "value": t.value,
                "state": t.state.name,
                "duration_s": (
                    (t.datetime_complete - t.datetime_start).total_seconds()
                    if t.datetime_complete and t.datetime_start
                    else None
                ),
            }
            for t in study.trials
        ]
        return {
            "study_name": study.study_name,
            "best_params": best_trial.params,
            "best_value": best_trial.value,
            "n_trials": len(study.trials),
            "trials": trials_summary,
        }


# ---------------------------------------------------------------------------
# Module-level model factory helpers
# ---------------------------------------------------------------------------

def _build_cnn(
    num_classes: int,
    lr: float,
    dropout: float,
    f1: int,
    f2: int,
    f3: int,
    dense_units: int,
) -> "tf.keras.Model":  # type: ignore[name-defined]
    """Build a compact CNN with configurable filters for Optuna trials."""
    import tensorflow as tf  # type: ignore[import]

    inputs = tf.keras.Input(shape=(28, 28, 1))
    x = tf.keras.layers.Conv2D(f1, 3, padding="same", activation="relu")(inputs)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.MaxPooling2D()(x)

    x = tf.keras.layers.Conv2D(f2, 3, padding="same", activation="relu")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.MaxPooling2D()(x)

    x = tf.keras.layers.Conv2D(f3, 3, padding="same", activation="relu")(x)
    x = tf.keras.layers.BatchNormalization()(x)
    x = tf.keras.layers.MaxPooling2D()(x)

    x = tf.keras.layers.Flatten()(x)
    x = tf.keras.layers.Dense(dense_units, activation="relu")(x)
    x = tf.keras.layers.Dropout(dropout)(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax")(x)

    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=lr),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def _build_resnet18(num_classes: int, device: "torch.device") -> "nn.Module":  # type: ignore[name-defined]
    """Build a ResNet18 adapted for 28×28 input."""
    import torch.nn as nn  # type: ignore[import]
    import torchvision.models as tv_models  # type: ignore[import]

    net = tv_models.resnet18(weights=None)
    net.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
    net.maxpool = nn.Identity()  # type: ignore[assignment]
    net.fc = nn.Linear(net.fc.in_features, num_classes)
    return net.to(device)


def _to_3ch_tensor(x: np.ndarray) -> "torch.Tensor":  # type: ignore[name-defined]
    """Convert (N, H, W, 1) or (N, 1, H, W) float32 → (N, 3, H, W) torch tensor."""
    import torch  # type: ignore[import]

    arr = x.astype(np.float32)
    if arr.ndim == 4 and arr.shape[-1] == 1:
        arr = arr.transpose(0, 3, 1, 2)
    t = torch.from_numpy(arr)
    if t.shape[1] == 1:
        t = t.repeat(1, 3, 1, 1)
    return t
