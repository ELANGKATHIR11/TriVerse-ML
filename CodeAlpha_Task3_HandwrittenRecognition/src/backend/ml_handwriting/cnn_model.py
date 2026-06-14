"""
Handwriting Recognition CNN Trainer (TensorFlow / Keras, GPU-accelerated)
RTX 5060 ready — uses tf.config.experimental.set_memory_growth to avoid
pre-allocating all VRAM.

Architecture
------------
Conv2D(32,3)→BN→MaxPool → Conv2D(64,3)→BN→MaxPool → Conv2D(128,3)→BN→MaxPool
→ Flatten → Dense(256,relu) → Dropout(0.5) → Dense(num_classes, softmax)
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Coroutine

import mlflow
import mlflow.keras
import numpy as np
import tensorflow as tf

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Custom Keras callback that forwards epoch metrics to the WebSocket callback
# ---------------------------------------------------------------------------

class _WsEpochCallback(tf.keras.callbacks.Callback):
    """Fires ws_callback after every epoch with a progress payload."""

    def __init__(
        self,
        ws_callback: Callable[[dict], Coroutine] | None,
        total_epochs: int,
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        super().__init__()
        self._ws_callback = ws_callback
        self._total_epochs = total_epochs
        self._loop = loop
        self._epoch_start: float = 0.0

    def on_epoch_begin(self, epoch: int, logs: dict | None = None) -> None:  # type: ignore[override]
        self._epoch_start = time.perf_counter()

    def on_epoch_end(self, epoch: int, logs: dict | None = None) -> None:  # type: ignore[override]
        if self._ws_callback is None:
            return
        elapsed = time.perf_counter() - self._epoch_start
        payload: dict[str, Any] = {
            "event": "epoch_end",
            "epoch": epoch + 1,
            "total_epochs": self._total_epochs,
            "epoch_duration_s": round(elapsed, 3),
            "metrics": {k: float(v) for k, v in (logs or {}).items()},
        }
        try:
            if self._loop.is_running():
                asyncio.run_coroutine_threadsafe(self._ws_callback(payload), self._loop)
            else:
                self._loop.run_until_complete(self._ws_callback(payload))
        except Exception as exc:  # pragma: no cover
            logger.warning("ws_callback failed on epoch %d: %s", epoch + 1, exc)


# ---------------------------------------------------------------------------
# CNNTrainer
# ---------------------------------------------------------------------------

class CNNTrainer:
    """Builds, trains, and evaluates a Keras CNN for handwriting recognition."""

    def __init__(
        self,
        X_train: np.ndarray,
        X_test: np.ndarray,
        y_train: np.ndarray,
        y_test: np.ndarray,
        num_classes: int,
        ws_callback: Callable[[dict], Coroutine] | None = None,
    ) -> None:
        """
        Parameters
        ----------
        X_train / X_test : float32 arrays of shape (N, 28, 28, 1)
        y_train / y_test : int64 arrays of shape (N,)
        num_classes      : number of output classes (10 for MNIST, 47 for EMNIST)
        ws_callback      : optional async callable; called with epoch progress dicts
        """
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.num_classes = num_classes
        self.ws_callback = ws_callback
        self.model: tf.keras.Model | None = None

        self._configure_gpu()

    # ------------------------------------------------------------------
    # GPU setup
    # ------------------------------------------------------------------

    @staticmethod
    def _configure_gpu() -> None:
        """Enable memory growth so TF doesn't consume all VRAM at startup."""
        gpus = tf.config.list_physical_devices("GPU")
        if gpus:
            for gpu in gpus:
                try:
                    tf.config.experimental.set_memory_growth(gpu, True)
                    logger.info("GPU memory growth enabled: %s", gpu.name)
                except RuntimeError as exc:
                    logger.warning("Could not set memory growth: %s", exc)
        else:
            logger.warning("No GPU found — training on CPU.")

    # ------------------------------------------------------------------
    # Model construction
    # ------------------------------------------------------------------

    def build_model(self) -> tf.keras.Model:
        """Build and compile the CNN.

        Returns
        -------
        Compiled tf.keras.Model (also stored as self.model).
        """
        inputs = tf.keras.Input(shape=(28, 28, 1), name="image_input")

        # Block 1 — 32 filters
        x = tf.keras.layers.Conv2D(32, (3, 3), padding="same", activation="relu", name="conv1")(inputs)
        x = tf.keras.layers.BatchNormalization(name="bn1")(x)
        x = tf.keras.layers.MaxPooling2D((2, 2), name="pool1")(x)

        # Block 2 — 64 filters
        x = tf.keras.layers.Conv2D(64, (3, 3), padding="same", activation="relu", name="conv2")(x)
        x = tf.keras.layers.BatchNormalization(name="bn2")(x)
        x = tf.keras.layers.MaxPooling2D((2, 2), name="pool2")(x)

        # Block 3 — 128 filters
        x = tf.keras.layers.Conv2D(128, (3, 3), padding="same", activation="relu", name="conv3")(x)
        x = tf.keras.layers.BatchNormalization(name="bn3")(x)
        x = tf.keras.layers.MaxPooling2D((2, 2), name="pool3")(x)

        # Classifier head
        x = tf.keras.layers.Flatten(name="flatten")(x)
        x = tf.keras.layers.Dense(256, activation="relu", name="dense1")(x)
        x = tf.keras.layers.Dropout(0.5, name="dropout")(x)
        outputs = tf.keras.layers.Dense(self.num_classes, activation="softmax", name="predictions")(x)

        model = tf.keras.Model(inputs=inputs, outputs=outputs, name="handwriting_cnn")
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        logger.info("CNN built — total params: %d", model.count_params())
        self.model = model
        return model

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    async def train(
        self,
        epochs: int = 20,
        batch_size: int = 256,
        experiment_name: str = "handwriting_cnn",
    ) -> dict[str, Any]:
        """Train the CNN and log results to MLflow.

        Parameters
        ----------
        epochs          : maximum training epochs
        batch_size      : mini-batch size
        experiment_name : MLflow experiment name

        Returns
        -------
        dict compatible with the ModelResult schema:
        {
            "accuracy", "precision", "recall", "f1",
            "training_time", "inference_time", "memory_mb", "model_size_mb",
            "run_id", "epochs_trained"
        }
        """
        if self.model is None:
            self.build_model()

        assert self.model is not None  # for type checker

        # Retrieve the running event loop so the callback can schedule coroutines
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        # MLflow experiment
        try:
            mlflow.set_experiment(experiment_name)
        except Exception as exc:
            logger.warning("MLflow set_experiment failed: %s", exc)

        callbacks: list[tf.keras.callbacks.Callback] = [
            tf.keras.callbacks.EarlyStopping(
                monitor="val_loss",
                patience=5,
                restore_best_weights=True,
                verbose=1,
            ),
            self._epoch_callback(epochs, loop),
        ]

        train_start = time.perf_counter()

        with mlflow.start_run(run_name=f"cnn_e{epochs}_b{batch_size}") as run:
            run_id = run.info.run_id

            # Log hyperparameters
            mlflow.log_params(
                {
                    "model_type": "CNN",
                    "epochs": epochs,
                    "batch_size": batch_size,
                    "num_classes": self.num_classes,
                    "optimizer": "adam",
                    "learning_rate": 1e-3,
                    "dropout": 0.5,
                    "architecture": "Conv32-Conv64-Conv128-Dense256",
                }
            )

            # Custom MLflow epoch-level callback
            mlflow_epoch_cb = _MLflowEpochCallback()
            callbacks.append(mlflow_epoch_cb)

            # Train (run in executor so we don't block the async event loop)
            history = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.model.fit(  # type: ignore[union-attr]
                    self.X_train,
                    self.y_train,
                    epochs=epochs,
                    batch_size=batch_size,
                    validation_data=(self.X_test, self.y_test),
                    callbacks=callbacks,
                    verbose=0,
                ),
            )

            training_time = time.perf_counter() - train_start

            # Full evaluation metrics
            metrics = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self._compute_metrics(batch_size),
            )
            metrics["training_time"] = round(training_time, 3)
            metrics["epochs_trained"] = len(history.history["loss"])
            metrics["run_id"] = run_id

            # Inference time on 1000-sample batch
            infer_start = time.perf_counter()
            _ = self.model.predict(self.X_test[:1000], batch_size=256, verbose=0)
            metrics["inference_time_ms"] = round((time.perf_counter() - infer_start) * 1000 / 1000, 4)

            # Memory / model size
            metrics["memory_mb"] = self._process_memory_mb()
            metrics["model_size_mb"] = self._model_size_mb()

            # Log final metrics to MLflow
            mlflow.log_metrics(
                {
                    "accuracy": metrics["accuracy"],
                    "precision": metrics["precision"],
                    "recall": metrics["recall"],
                    "f1": metrics["f1"],
                    "training_time_s": metrics["training_time"],
                    "inference_time_ms": metrics["inference_time_ms"],
                    "model_size_mb": metrics["model_size_mb"],
                }
            )

            # Log model artifact
            try:
                mlflow.keras.log_model(self.model, artifact_path="model")
            except Exception as exc:
                logger.warning("MLflow model logging failed: %s", exc)

        logger.info("CNN training complete: accuracy=%.4f  run_id=%s", metrics["accuracy"], run_id)
        return metrics

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _epoch_callback(self, total_epochs: int, loop: asyncio.AbstractEventLoop) -> tf.keras.callbacks.Callback:
        """Return the custom WebSocket epoch callback."""
        return _WsEpochCallback(
            ws_callback=self.ws_callback,
            total_epochs=total_epochs,
            loop=loop,
        )

    def _compute_metrics(self, batch_size: int) -> dict[str, float]:
        """Compute accuracy, precision, recall, F1 on the test set."""
        from sklearn.metrics import (  # type: ignore[import]
            accuracy_score,
            f1_score,
            precision_score,
            recall_score,
        )

        assert self.model is not None

        y_pred_probs = self.model.predict(self.X_test, batch_size=batch_size, verbose=0)
        y_pred = np.argmax(y_pred_probs, axis=1)

        acc = float(accuracy_score(self.y_test, y_pred))
        prec = float(precision_score(self.y_test, y_pred, average="weighted", zero_division=0))
        rec = float(recall_score(self.y_test, y_pred, average="weighted", zero_division=0))
        f1 = float(f1_score(self.y_test, y_pred, average="weighted", zero_division=0))

        return {
            "accuracy": round(acc, 6),
            "precision": round(prec, 6),
            "recall": round(rec, 6),
            "f1": round(f1, 6),
        }

    @staticmethod
    def _process_memory_mb() -> float:
        """Return current process RSS in MB."""
        try:
            import psutil  # type: ignore[import]
            import os

            proc = psutil.Process(os.getpid())
            return round(proc.memory_info().rss / 1_048_576, 2)
        except Exception:
            return -1.0

    def _model_size_mb(self) -> float:
        """Estimate model size in MB from total parameter count."""
        if self.model is None:
            return 0.0
        total_params = sum(np.prod(v.shape) for v in self.model.trainable_weights)
        return round(total_params * 4 / 1_048_576, 3)  # float32 = 4 bytes


class _MLflowEpochCallback(tf.keras.callbacks.Callback):
    """Logs per-epoch metrics to the active MLflow run."""

    def on_epoch_end(self, epoch: int, logs: dict | None = None) -> None:  # type: ignore[override]
        if not logs:
            return
        try:
            mlflow.log_metrics(
                {k: float(v) for k, v in logs.items()},
                step=epoch,
            )
        except Exception as exc:
            logger.debug("MLflow epoch metric log failed: %s", exc)
