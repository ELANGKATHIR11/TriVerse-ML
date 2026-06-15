"""
vision_efficientnet_trainer.py

EfficientNet-B0 model implemented in PyTorch for handwriting recognition (MNIST / EMNIST).
Supports GPU, Automatic Mixed Precision (AMP), gradient scaling, and MLflow logging/registry.
"""

from __future__ import annotations
import os
import time
import logging
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import torchvision.models as models
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import mlflow

from app.ml.base import compute_memory_usage, get_model_size_mb

logger = logging.getLogger(__name__)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class EfficientNetB0(nn.Module):
    """EfficientNet-B0 adapted for single-channel grayscale 28x28 images"""
    def __init__(self, num_classes: int = 10):
        super().__init__()
        # Load weights=None to train from scratch (local requirement)
        self.model = models.efficientnet_b0(weights=None)
        
        # Modify first layer: from 3 channels to 1 channel (grayscale)
        original_conv = self.model.features[0][0]
        self.model.features[0][0] = nn.Conv2d(
            in_channels=1,
            out_channels=original_conv.out_channels,
            kernel_size=original_conv.kernel_size,
            stride=original_conv.stride,
            padding=original_conv.padding,
            bias=False
        )
        
        # Modify classification head
        in_features = self.model.classifier[1].in_features
        self.model.classifier[1] = nn.Linear(in_features, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.model(x)

class EfficientNetB0Trainer:
    """Trainer class for EfficientNet-B0 on vision datasets"""
    def __init__(self, X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray, num_classes: int = 10):
        # Input shape expected: (N, H, W, 1) or (N, 1, H, W)
        if X_train.shape[-1] == 1:
            X_train = np.transpose(X_train, (0, 3, 1, 2))  # NHWC -> NCHW
            X_test = np.transpose(X_test, (0, 3, 1, 2))
            
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.num_classes = num_classes
        
        self.model = EfficientNetB0(num_classes=num_classes).to(DEVICE)
        self.optimizer = optim.Adam(self.model.parameters(), lr=0.001)
        self.criterion = nn.CrossEntropyLoss()

    def train(self, epochs: int = 2, batch_size: int = 256) -> dict[str, float]:
        self.model.train()
        
        dataset = TensorDataset(
            torch.tensor(self.X_train, dtype=torch.float32),
            torch.tensor(self.y_train, dtype=torch.long)
        )
        loader = DataLoader(
            dataset,
            batch_size=batch_size,
            shuffle=True,
            pin_memory=True,
            num_workers=0
        )
        
        scaler = torch.amp.GradScaler("cuda") if DEVICE.type == "cuda" else None
        t0 = time.perf_counter()
        
        for epoch in range(epochs):
            running_loss = 0.0
            for batch_x, batch_y in loader:
                batch_x, batch_y = batch_x.to(DEVICE), batch_y.to(DEVICE)
                self.optimizer.zero_grad()
                
                if scaler:
                    with torch.amp.autocast("cuda"):
                        logits = self.model(batch_x)
                        loss = self.criterion(logits, batch_y)
                    scaler.scale(loss).backward()
                    scaler.step(self.optimizer)
                    scaler.update()
                else:
                    logits = self.model(batch_x)
                    loss = self.criterion(logits, batch_y)
                    loss.backward()
                    self.optimizer.step()
                    
                running_loss += loss.item() * batch_x.size(0)
            
            epoch_loss = running_loss / len(self.X_train)
            logger.info(f"[EfficientNet-B0] Epoch {epoch+1}/{epochs} - Loss: {epoch_loss:.4f}")
            
        training_time = time.perf_counter() - t0
        
        # Evaluation
        self.model.eval()
        test_dataset = TensorDataset(torch.tensor(self.X_test, dtype=torch.float32))
        test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
        
        preds = []
        t_infer0 = time.perf_counter()
        with torch.no_grad():
            for batch_x, in test_loader:
                batch_x = batch_x.to(DEVICE)
                logits = self.model(batch_x)
                preds.append(torch.argmax(logits, dim=1).cpu().numpy())
        inference_time_total = time.perf_counter() - t_infer0
        
        y_pred = np.concatenate(preds, axis=0)
        
        # Calculate standard metrics
        acc = float(accuracy_score(self.y_test, y_pred))
        prec = float(precision_score(self.y_test, y_pred, average="weighted", zero_division=0))
        rec = float(recall_score(self.y_test, y_pred, average="weighted", zero_division=0))
        f1 = float(f1_score(self.y_test, y_pred, average="weighted", zero_division=0))
        
        avg_infer_ms = (inference_time_total / len(self.X_test)) * 1000.0
        mem_mb = compute_memory_usage()
        size_mb = get_model_size_mb(self.model)
        
        # Save model weights
        os.makedirs("trained_models/vision", exist_ok=True)
        torch.save(self.model.state_dict(), "trained_models/vision/efficientnet.pth")
        
        metrics = {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "f1": f1,
            "training_time": training_time,
            "inference_time_ms": avg_infer_ms,
            "memory_mb": mem_mb,
            "model_size_mb": size_mb,
        }
        
        # Log to MLflow
        try:
            mlflow.set_experiment("handwriting_recognition")
            with mlflow.start_run(run_name="efficientnet_b0") as run:
                mlflow.set_tags({
                    "model_name": "efficientnet_b0",
                    "task_type": "handwriting",
                })
                mlflow.log_params({
                    "epochs": epochs,
                    "batch_size": batch_size,
                    "lr": 0.001,
                    "optimizer": "Adam",
                })
                mlflow.log_metrics({
                    "accuracy": acc,
                    "precision": prec,
                    "recall": rec,
                    "f1": f1,
                    "training_time_sec": training_time,
                    "inference_time_ms": avg_infer_ms,
                    "model_size_mb": size_mb,
                    "memory_usage_mb": mem_mb,
                })
                metrics["run_id"] = run.info.run_id
        except Exception as exc:
            logger.warning("[vision-efficientnet] MLflow logging failed: %s", exc)
            metrics["run_id"] = "offline_run"
            
        return metrics
