"""
Handwriting Recognition ResNet18 Trainer (PyTorch / CUDA — RTX 5060)

The grayscale 28×28 input is replicated to 3 channels so the standard
ImageNet-pretrained ResNet18 backbone can be used out-of-the-box.
The first convolutional layer keeps stride=1 and kernel=3 (instead of 7/2)
to avoid excessive spatial downsampling on small 28×28 images.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Coroutine

import mlflow
import mlflow.pytorch
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
from torch.optim.lr_scheduler import CosineAnnealingLR
from torch.utils.data import DataLoader, TensorDataset

logger = logging.getLogger(__name__)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
logger.info("ResNet18Trainer using device: %s", DEVICE)


class ResNet18Trainer:
    """Trains a modified ResNet18 on handwriting data using PyTorch + CUDA."""

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
        X_train / X_test : float32 arrays shape (N, 28, 28, 1) OR (N, 1, 28, 28)
        y_train / y_test : int64 arrays shape (N,)
        num_classes      : 10 for MNIST, 47 for EMNIST Balanced
        ws_callback      : optional async callable; receives batch-level progress dicts
        """
        self.num_classes = num_classes
        self.ws_callback = ws_callback
        self.model: nn.Module | None = None

        # Convert numpy arrays to PyTorch tensors (NCHW, 3 channels)
        self.X_train_t = self._to_3channel_tensor(X_train)
        self.X_test_t = self._to_3channel_tensor(X_test)
        self.y_train_t = torch.from_numpy(y_train.astype(np.int64))
        self.y_test_t = torch.from_numpy(y_test.astype(np.int64))

    # ------------------------------------------------------------------
    # Model construction
    # ------------------------------------------------------------------

    def build_model(self) -> nn.Module:
        """Build a ResNet18 adapted for 28×28 grayscale input.

        Changes vs. standard ResNet18:
        - First Conv2D: kernel 3×3, stride 1, padding 1  (was 7×7/stride-2)
        - MaxPool after first conv: removed  (would collapse spatial dims too aggressively)
        - Final FC layer: replaced with Linear(512 → num_classes)

        Returns
        -------
        nn.Module placed on DEVICE, stored as self.model.
        """
        net = models.resnet18(weights=None)

        # Adapt for small 28×28 images
        net.conv1 = nn.Conv2d(3, 64, kernel_size=3, stride=1, padding=1, bias=False)
        net.maxpool = nn.Identity()  # type: ignore[assignment]

        # Replace final classification layer
        in_features = net.fc.in_features
        net.fc = nn.Linear(in_features, self.num_classes)

        self.model = net.to(DEVICE)
        n_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)
        logger.info("ResNet18 built — trainable params: %d  device: %s", n_params, DEVICE)
        return self.model

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    async def train(
        self,
        epochs: int = 20,
        batch_size: int = 256,
        learning_rate: float = 1e-3,
        experiment_name: str = "handwriting_resnet18",
    ) -> dict[str, Any]:
        """Train ResNet18 and log results to MLflow.

        Parameters
        ----------
        epochs          : maximum training epochs
        batch_size      : mini-batch size
        learning_rate   : initial SGD learning rate
        experiment_name : MLflow experiment name

        Returns
        -------
        ModelResult-compatible dict with accuracy, precision, recall, f1,
        training_time, inference_time_ms, memory_mb, model_size_mb, run_id.
        """
        if self.model is None:
            self.build_model()

        assert self.model is not None

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()

        # MLflow setup
        try:
            mlflow.set_experiment(experiment_name)
        except Exception as exc:
            logger.warning("MLflow set_experiment failed: %s", exc)

        # Data loaders
        train_loader, test_loader = self._build_data_loaders(batch_size)

        # Optimiser + scheduler
        optimizer = torch.optim.SGD(
            self.model.parameters(),
            lr=learning_rate,
            momentum=0.9,
            weight_decay=1e-4,
        )
        scheduler = CosineAnnealingLR(optimizer, T_max=epochs, eta_min=1e-6)
        criterion = nn.CrossEntropyLoss()

        train_start = time.perf_counter()

        with mlflow.start_run(run_name=f"resnet18_e{epochs}_b{batch_size}_lr{learning_rate}") as run:
            run_id = run.info.run_id

            mlflow.log_params(
                {
                    "model_type": "ResNet18",
                    "epochs": epochs,
                    "batch_size": batch_size,
                    "learning_rate": learning_rate,
                    "optimizer": "sgd",
                    "momentum": 0.9,
                    "weight_decay": 1e-4,
                    "scheduler": "cosine_annealing",
                    "num_classes": self.num_classes,
                    "device": str(DEVICE),
                }
            )

            # Run training loop in a thread so we don't block the event loop
            history = await loop.run_in_executor(
                None,
                lambda: self._train_loop(
                    train_loader=train_loader,
                    test_loader=test_loader,
                    optimizer=optimizer,
                    scheduler=scheduler,
                    criterion=criterion,
                    epochs=epochs,
                    loop=loop,
                ),
            )

            training_time = time.perf_counter() - train_start

            # Evaluation metrics
            metrics = await loop.run_in_executor(
                None,
                lambda: self._compute_metrics(test_loader),
            )
            metrics["training_time"] = round(training_time, 3)
            metrics["epochs_trained"] = epochs
            metrics["run_id"] = run_id

            # Inference time on first 1000 test samples
            infer_start = time.perf_counter()
            self._infer(self.X_test_t[:1000])
            metrics["inference_time_ms"] = round(
                (time.perf_counter() - infer_start) * 1000 / 1000, 4
            )

            metrics["memory_mb"] = self._process_memory_mb()
            metrics["model_size_mb"] = self._model_size_mb()

            # Log final metrics
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

            # Log per-epoch history
            for epoch_idx, (train_loss, val_loss, val_acc) in enumerate(
                zip(history["train_loss"], history["val_loss"], history["val_acc"])
            ):
                mlflow.log_metrics(
                    {
                        "train_loss": train_loss,
                        "val_loss": val_loss,
                        "val_accuracy": val_acc,
                    },
                    step=epoch_idx,
                )

            # Save model to disk
            try:
                import os
                os.makedirs("trained_models/vision", exist_ok=True)
                torch.save(self.model.state_dict(), "trained_models/vision/resnet18.pth")
                logger.info("ResNet18 weights saved to trained_models/vision/resnet18.pth")
            except Exception as save_exc:
                logger.warning("Failed to save ResNet18 model: %s", save_exc)

            # Log model artifact
            try:
                mlflow.pytorch.log_model(self.model, artifact_path="model")
            except Exception as exc:
                logger.warning("MLflow model logging failed: %s", exc)

        logger.info(
            "ResNet18 training complete: accuracy=%.4f  run_id=%s",
            metrics["accuracy"],
            run_id,
        )
        return metrics

    # ------------------------------------------------------------------
    # Internal training loop
    # ------------------------------------------------------------------

    def _train_loop(
        self,
        train_loader: DataLoader,
        test_loader: DataLoader,
        optimizer: torch.optim.Optimizer,
        scheduler: Any,
        criterion: nn.Module,
        epochs: int,
        loop: asyncio.AbstractEventLoop,
    ) -> dict[str, list[float]]:
        """Core epoch/batch training loop (runs in a thread pool executor)."""
        assert self.model is not None

        history: dict[str, list[float]] = {
            "train_loss": [],
            "val_loss": [],
            "val_acc": [],
        }

        total_batches = len(train_loader)

        for epoch in range(epochs):
            self.model.train()
            running_loss = 0.0
            n_seen = 0

            for batch_idx, (x_batch, y_batch) in enumerate(train_loader):
                x_batch = x_batch.to(DEVICE, non_blocking=True)
                y_batch = y_batch.to(DEVICE, non_blocking=True)

                optimizer.zero_grad()
                logits = self.model(x_batch)
                loss = criterion(logits, y_batch)
                loss.backward()
                optimizer.step()

                running_loss += loss.item() * len(y_batch)
                n_seen += len(y_batch)

                # Send per-batch progress via ws_callback
                if self.ws_callback is not None and batch_idx % max(1, total_batches // 10) == 0:
                    payload = {
                        "event": "batch_end",
                        "epoch": epoch + 1,
                        "total_epochs": epochs,
                        "batch": batch_idx + 1,
                        "total_batches": total_batches,
                        "train_loss": round(running_loss / n_seen, 6),
                    }
                    try:
                        if loop.is_running():
                            asyncio.run_coroutine_threadsafe(
                                self.ws_callback(payload), loop
                            )
                    except Exception as exc:
                        logger.debug("ws_callback error: %s", exc)

            scheduler.step()
            epoch_train_loss = running_loss / n_seen

            # Validation
            val_loss, val_acc = self._evaluate_loader(test_loader, criterion)
            history["train_loss"].append(round(epoch_train_loss, 6))
            history["val_loss"].append(round(val_loss, 6))
            history["val_acc"].append(round(val_acc, 6))

            logger.info(
                "Epoch %2d/%d — train_loss=%.4f  val_loss=%.4f  val_acc=%.4f",
                epoch + 1,
                epochs,
                epoch_train_loss,
                val_loss,
                val_acc,
            )

        return history

    def _evaluate_loader(
        self, loader: DataLoader, criterion: nn.Module
    ) -> tuple[float, float]:
        """Return (mean_loss, accuracy) on a DataLoader."""
        assert self.model is not None
        self.model.eval()
        total_loss = 0.0
        correct = 0
        n_total = 0

        with torch.no_grad():
            for x_batch, y_batch in loader:
                x_batch = x_batch.to(DEVICE, non_blocking=True)
                y_batch = y_batch.to(DEVICE, non_blocking=True)
                logits = self.model(x_batch)
                loss = criterion(logits, y_batch)
                total_loss += loss.item() * len(y_batch)
                preds = logits.argmax(dim=1)
                correct += (preds == y_batch).sum().item()
                n_total += len(y_batch)

        return total_loss / n_total, correct / n_total

    # ------------------------------------------------------------------
    # Inference & metrics
    # ------------------------------------------------------------------

    def _infer(self, x_tensor: torch.Tensor) -> np.ndarray:
        """Run inference; returns logits as numpy array."""
        assert self.model is not None
        self.model.eval()
        with torch.no_grad():
            out = self.model(x_tensor.to(DEVICE))
        return out.cpu().numpy()

    def _compute_metrics(self, test_loader: DataLoader) -> dict[str, float]:
        """Compute weighted precision, recall, F1 and accuracy on test set."""
        from sklearn.metrics import (  # type: ignore[import]
            accuracy_score,
            f1_score,
            precision_score,
            recall_score,
        )

        assert self.model is not None
        self.model.eval()
        all_preds: list[int] = []
        all_labels: list[int] = []

        with torch.no_grad():
            for x_batch, y_batch in test_loader:
                x_batch = x_batch.to(DEVICE, non_blocking=True)
                logits = self.model(x_batch)
                preds = logits.argmax(dim=1).cpu().numpy().tolist()
                all_preds.extend(preds)
                all_labels.extend(y_batch.numpy().tolist())

        y_true = np.array(all_labels)
        y_pred = np.array(all_preds)

        return {
            "accuracy": round(float(accuracy_score(y_true, y_pred)), 6),
            "precision": round(
                float(precision_score(y_true, y_pred, average="weighted", zero_division=0)), 6
            ),
            "recall": round(
                float(recall_score(y_true, y_pred, average="weighted", zero_division=0)), 6
            ),
            "f1": round(
                float(f1_score(y_true, y_pred, average="weighted", zero_division=0)), 6
            ),
        }

    # ------------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------------

    def _build_data_loaders(self, batch_size: int) -> tuple[DataLoader, DataLoader]:
        train_ds = TensorDataset(self.X_train_t, self.y_train_t)
        test_ds = TensorDataset(self.X_test_t, self.y_test_t)
        n_workers = 0  # Keep 0 for Windows compatibility
        train_loader = DataLoader(
            train_ds,
            batch_size=batch_size,
            shuffle=True,
            num_workers=n_workers,
            pin_memory=(DEVICE.type == "cuda"),
        )
        test_loader = DataLoader(
            test_ds,
            batch_size=batch_size,
            shuffle=False,
            num_workers=n_workers,
            pin_memory=(DEVICE.type == "cuda"),
        )
        return train_loader, test_loader

    @staticmethod
    def _to_3channel_tensor(x: np.ndarray) -> torch.Tensor:
        """Convert (N, 28, 28, 1) or (N, 1, 28, 28) float32 → (N, 3, 28, 28) tensor."""
        arr = x.astype(np.float32)
        if arr.ndim == 4 and arr.shape[-1] == 1:
            arr = arr.transpose(0, 3, 1, 2)  # NHWC → NCHW
        # Repeat channel dim: (N,1,28,28) → (N,3,28,28)
        tensor = torch.from_numpy(arr)
        if tensor.shape[1] == 1:
            tensor = tensor.repeat(1, 3, 1, 1)
        return tensor

    @staticmethod
    def _process_memory_mb() -> float:
        try:
            import os
            import psutil  # type: ignore[import]
            return round(psutil.Process(os.getpid()).memory_info().rss / 1_048_576, 2)
        except Exception:
            return -1.0

    def _model_size_mb(self) -> float:
        if self.model is None:
            return 0.0
        total = sum(p.numel() for p in self.model.parameters())
        return round(total * 4 / 1_048_576, 3)  # float32 = 4 bytes
