"""
credit_tabnet_trainer.py

TabNet model implemented in PyTorch for tabular credit classification.
Supports GPU acceleration, model serialization, evaluation, and MLflow registry.
"""

from __future__ import annotations
import os
import time
import logging
import joblib
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix, classification_report
import mlflow

from app.ml.base import ModelResult, compute_memory_usage, get_model_size_mb, measure_inference_time

logger = logging.getLogger(__name__)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class GLU(nn.Module):
    """Gated Linear Unit"""
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.fc = nn.Linear(input_dim, output_dim * 2)
        self.bn = nn.BatchNorm1d(output_dim * 2)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.bn(self.fc(x))
        left, right = torch.chunk(x, 2, dim=-1)
        return left * torch.sigmoid(right)

class FeatureTransformer(nn.Module):
    """Feature Transformer consisting of multiple GLU blocks"""
    def __init__(self, input_dim: int, output_dim: int, n_steps: int = 2):
        super().__init__()
        self.blocks = nn.ModuleList()
        # First block
        self.blocks.append(GLU(input_dim, output_dim))
        # Subsequent blocks
        for _ in range(n_steps - 1):
            self.blocks.append(GLU(output_dim, output_dim))
        self.scale = torch.sqrt(torch.FloatTensor([0.5])).to(DEVICE)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.blocks[0](x)
        for block in self.blocks[1:]:
            x = (x + block(x)) * self.scale
        return x

class AttentiveTransformer(nn.Module):
    """Attentive Transformer to generate feature masks"""
    def __init__(self, input_dim: int, output_dim: int):
        super().__init__()
        self.fc = nn.Linear(input_dim, output_dim)
        self.bn = nn.BatchNorm1d(output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.softmax(self.bn(self.fc(x)), dim=-1)

class TabNet(nn.Module):
    """PyTorch TabNet model for classification"""
    def __init__(self, input_dim: int, output_dim: int, n_d: int = 8, n_a: int = 8, n_steps: int = 3, gamma: float = 1.3):
        super().__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim
        self.n_d = n_d
        self.n_a = n_a
        self.n_steps = n_steps
        self.gamma = gamma

        # Initial batch norm
        self.bn = nn.BatchNorm1d(input_dim)
        
        # Transformers
        self.feature_transformers = nn.ModuleList([FeatureTransformer(input_dim, n_d + n_a) for _ in range(n_steps)])
        self.attentive_transformers = nn.ModuleList([AttentiveTransformer(n_a, input_dim) for _ in range(n_steps)])
        
        # Final classifier
        self.final_mapping = nn.Linear(n_d, output_dim)

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        x = self.bn(x)
        batch_size = x.shape[0]
        prior = torch.ones((batch_size, self.input_dim), device=x.device)
        a = torch.zeros((batch_size, self.n_a), device=x.device)
        out = torch.zeros((batch_size, self.n_d), device=x.device)
        feature_importance = torch.zeros((batch_size, self.input_dim), device=x.device)
        
        for step in range(self.n_steps):
            mask = self.attentive_transformers[step](a) * prior
            prior = prior * (self.gamma - mask)
            feature_importance += mask
            masked_x = x * mask
            transformer_out = self.feature_transformers[step](masked_x)
            d, a = torch.chunk(transformer_out, 2, dim=-1)
            out += torch.relu(d)
            
        logits = self.final_mapping(out)
        return logits, feature_importance

class TabNetClassifier:
    """Wrapper matching scikit-learn API for TabNet training and inference"""
    def __init__(self, input_dim: int, n_d: int = 16, n_a: int = 16, n_steps: int = 3, gamma: float = 1.3, lr: float = 0.01, epochs: int = 30, batch_size: int = 256):
        self.input_dim = input_dim
        self.n_d = n_d
        self.n_a = n_a
        self.n_steps = n_steps
        self.gamma = gamma
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        
        self.model = TabNet(input_dim, 2, n_d, n_a, n_steps, gamma).to(DEVICE)
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr, weight_decay=1e-5)
        self.criterion = nn.CrossEntropyLoss()

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.train()
        dataset = TensorDataset(torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.long))
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True, pin_memory=True)
        
        for epoch in range(self.epochs):
            for batch_x, batch_y in loader:
                batch_x, batch_y = batch_x.to(DEVICE), batch_y.to(DEVICE)
                self.optimizer.zero_grad()
                logits, _ = self.model(batch_x)
                loss = self.criterion(logits, batch_y)
                loss.backward()
                self.optimizer.step()

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        self.model.eval()
        dataset = TensorDataset(torch.tensor(X, dtype=torch.float32))
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)
        probas = []
        with torch.no_grad():
            for batch_x, in loader:
                batch_x = batch_x.to(DEVICE)
                logits, _ = self.model(batch_x)
                probs = torch.softmax(logits, dim=-1)
                probas.append(probs.cpu().numpy())
        return np.concatenate(probas, axis=0)

    def predict(self, X: np.ndarray) -> np.ndarray:
        probas = self.predict_proba(X)
        return np.argmax(probas, axis=1)

    def get_feature_importances(self, X: np.ndarray) -> np.ndarray:
        self.model.eval()
        dataset = TensorDataset(torch.tensor(X, dtype=torch.float32))
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=False)
        importances = []
        with torch.no_grad():
            for batch_x, in loader:
                batch_x = batch_x.to(DEVICE)
                _, masks = self.model(batch_x)
                importances.append(masks.cpu().numpy())
        mean_imp = np.concatenate(importances, axis=0).mean(axis=0)
        return mean_imp / (mean_imp.sum() + 1e-12)

class CreditTabNetTrainer:
    """Trainer for TabNet credit scoring model"""
    def __init__(self, X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray, feature_names: list[str], preprocessor: Any):
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.feature_names = feature_names
        self.preprocessor = preprocessor

    def train(self, hyperparams: dict | None = None) -> ModelResult:
        params = {
            "n_d": 16,
            "n_a": 16,
            "n_steps": 3,
            "gamma": 1.3,
            "lr": 0.01,
            "epochs": 20,
            "batch_size": 256,
        }
        if hyperparams:
            params.update(hyperparams)

        logger.info("[credit] TabNet params=%s", params)
        t0 = time.perf_counter()
        
        tabnet = TabNetClassifier(
            input_dim=self.X_train.shape[1],
            n_d=int(params["n_d"]),
            n_a=int(params["n_a"]),
            n_steps=int(params["n_steps"]),
            gamma=float(params["gamma"]),
            lr=float(params["lr"]),
            epochs=int(params["epochs"]),
            batch_size=int(params["batch_size"])
        )
        
        tabnet.fit(self.X_train, self.y_train)
        train_time = time.perf_counter() - t0

        os.makedirs("trained_models/credit", exist_ok=True)
        joblib.dump(tabnet, "trained_models/credit/tabnet.joblib")
        if self.preprocessor is not None:
            joblib.dump(self.preprocessor, "trained_models/credit/preprocessor.joblib")

        y_pred = tabnet.predict(self.X_test)
        y_proba = tabnet.predict_proba(self.X_test)[:, 1]

        acc = float(accuracy_score(self.y_test, y_pred))
        prec = float(precision_score(self.y_test, y_pred, average="weighted", zero_division=0))
        rec = float(recall_score(self.y_test, y_pred, average="weighted", zero_division=0))
        f1 = float(f1_score(self.y_test, y_pred, average="weighted", zero_division=0))
        auc = float(roc_auc_score(self.y_test, y_proba))

        clf_report = classification_report(self.y_test, y_pred, output_dict=True, zero_division=0)
        cm = confusion_matrix(self.y_test, y_pred).tolist()

        infer_ms = measure_inference_time(tabnet, self.X_test, n_runs=50)
        mem_mb = compute_memory_usage()
        size_mb = get_model_size_mb(tabnet)

        feat_imp_vals = tabnet.get_feature_importances(self.X_test)
        feat_imp = {name: float(val) for name, val in zip(self.feature_names, feat_imp_vals)}

        result = ModelResult(
            model_name="tabnet",
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
            best_hyperparams={str(k): str(v) for k, v in params.items()},
            classification_report=clf_report,
            confusion_matrix=cm,
            feature_importances=feat_imp,
        )

        try:
            mlflow.set_experiment("credit_scoring")
            with mlflow.start_run(run_name="tabnet", nested=True):
                mlflow.set_tags({
                    "model_name": "tabnet",
                    "task_type": "credit_scoring",
                })
                mlflow.log_params({k: str(v) for k, v in params.items()})
                mlflow.log_metrics({
                    "accuracy": acc,
                    "precision": prec,
                    "recall": rec,
                    "f1": f1,
                    "roc_auc": auc,
                    "training_time_sec": train_time,
                    "inference_time_ms": infer_ms,
                    "model_size_mb": size_mb,
                    "memory_usage_mb": mem_mb,
                })
                for feat, imp in feat_imp.items():
                    mlflow.log_metric(f"fi_{feat[:50]}", imp)
        except Exception as exc:
            logger.warning("[credit-tabnet] MLflow logging failed: %s", exc)

        return result
