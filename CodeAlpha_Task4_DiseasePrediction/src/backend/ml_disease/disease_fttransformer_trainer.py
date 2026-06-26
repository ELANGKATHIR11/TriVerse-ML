"""
disease_fttransformer_trainer.py

FT-Transformer (Feature Tokenizer + Transformer) model implemented in PyTorch for disease classification.
Supports GPU acceleration, model serialization, evaluation, and MLflow logging.
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

class FeatureTokenizer(nn.Module):
    """Maps continuous numerical features to tokens"""
    def __init__(self, num_features: int, token_dim: int):
        super().__init__()
        # Each numerical feature has its own weight and bias
        self.weights = nn.Parameter(torch.randn(num_features, token_dim))
        self.biases = nn.Parameter(torch.zeros(num_features, token_dim))

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # Input shape: (batch_size, num_features)
        # Weight shape: (num_features, token_dim)
        # Returns shape: (batch_size, num_features, token_dim)
        return x.unsqueeze(-1) * self.weights.unsqueeze(0) + self.biases.unsqueeze(0)

class FTTransformer(nn.Module):
    """FT-Transformer architecture for tabular classification"""
    def __init__(self, num_features: int, output_dim: int = 2, token_dim: int = 32, n_heads: int = 4, depth: int = 3, dropout: float = 0.1):
        super().__init__()
        self.tokenizer = FeatureTokenizer(num_features, token_dim)
        
        # CLS token embedding
        self.cls_token = nn.Parameter(torch.randn(1, 1, token_dim))
        
        # Transformer blocks
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=token_dim,
            nhead=n_heads,
            dim_feedforward=token_dim * 4,
            dropout=dropout,
            batch_first=True
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=depth)
        
        # Layer norm and classification head
        self.ln = nn.LayerNorm(token_dim)
        self.head = nn.Linear(token_dim, output_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        batch_size = x.shape[0]
        # Tokenize features: (batch, num_features, token_dim)
        tokens = self.tokenizer(x)
        
        # Prepend CLS token: (batch, num_features + 1, token_dim)
        cls_tokens = self.cls_token.expand(batch_size, -1, -1)
        tokens = torch.cat([cls_tokens, tokens], dim=1)
        
        # Transformer forward: (batch, num_features + 1, token_dim)
        trans_out = self.transformer(tokens)
        
        # Classification using CLS token
        cls_out = self.ln(trans_out[:, 0, :])
        logits = self.head(cls_out)
        return logits

class FTTransformerClassifier:
    """Wrapper matching scikit-learn API for FT-Transformer training and inference"""
    def __init__(self, num_features: int, token_dim: int = 32, n_heads: int = 4, depth: int = 3, dropout: float = 0.1, lr: float = 0.001, epochs: int = 30, batch_size: int = 64):
        self.num_features = num_features
        self.token_dim = token_dim
        self.n_heads = n_heads
        self.depth = depth
        self.dropout = dropout
        self.lr = lr
        self.epochs = epochs
        self.batch_size = batch_size
        
        self.model = FTTransformer(
            num_features=num_features,
            output_dim=2,
            token_dim=token_dim,
            n_heads=n_heads,
            depth=depth,
            dropout=dropout
        ).to(DEVICE)
        
        self.optimizer = optim.Adam(self.model.parameters(), lr=lr, weight_decay=1e-4)
        self.criterion = nn.CrossEntropyLoss()

    def fit(self, X: np.ndarray, y: np.ndarray):
        self.model.train()
        dataset = TensorDataset(torch.tensor(X, dtype=torch.float32), torch.tensor(y, dtype=torch.long))
        loader = DataLoader(dataset, batch_size=self.batch_size, shuffle=True, pin_memory=True)
        
        for epoch in range(self.epochs):
            for batch_x, batch_y in loader:
                batch_x, batch_y = batch_x.to(DEVICE), batch_y.to(DEVICE)
                self.optimizer.zero_grad()
                logits = self.model(batch_x)
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
                logits = self.model(batch_x)
                probs = torch.softmax(logits, dim=-1)
                probas.append(probs.cpu().numpy())
        return np.concatenate(probas, axis=0)

    def predict(self, X: np.ndarray) -> np.ndarray:
        probas = self.predict_proba(X)
        return np.argmax(probas, axis=1)

    def get_feature_importances(self, X: np.ndarray) -> np.ndarray:
        # Estimate importance using attention weights if needed, 
        # or use simple tokenizer weights magnitude as a reliable proxy.
        self.model.eval()
        with torch.no_grad():
            w = self.model.tokenizer.weights.cpu().numpy()
            norms = np.linalg.norm(w, axis=1)
        return norms / (norms.sum() + 1e-12)

class DiseaseFTTransformerTrainer:
    """Trainer for FT-Transformer disease model"""
    def __init__(self, X_train: np.ndarray, X_test: np.ndarray, y_train: np.ndarray, y_test: np.ndarray, feature_names: list[str], dataset_name: str):
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test
        self.feature_names = feature_names
        self.dataset_name = dataset_name

    def train(self, hyperparams: dict | None = None) -> ModelResult:
        params = {
            "token_dim": 32,
            "n_heads": 4,
            "depth": 2,
            "dropout": 0.1,
            "lr": 0.001,
            "epochs": 30,
            "batch_size": 64
        }
        if hyperparams:
            params.update(hyperparams)

        logger.info("[disease/%s] FT-Transformer params=%s", self.dataset_name, params)
        t0 = time.perf_counter()
        
        ftt = FTTransformerClassifier(
            num_features=self.X_train.shape[1],
            token_dim=int(params["token_dim"]),
            n_heads=int(params["n_heads"]),
            depth=int(params["depth"]),
            dropout=float(params["dropout"]),
            lr=float(params["lr"]),
            epochs=int(params["epochs"]),
            batch_size=int(params["batch_size"])
        )
        
        ftt.fit(self.X_train, self.y_train)
        train_time = time.perf_counter() - t0

        # Create directories and save model
        os.makedirs("trained_models/disease", exist_ok=True)
        joblib.dump(ftt, f"trained_models/disease/ft_transformer_{self.dataset_name}.joblib")

        # Predictions and metrics
        y_pred = ftt.predict(self.X_test)
        y_proba = ftt.predict_proba(self.X_test)[:, 1]

        acc = float(accuracy_score(self.y_test, y_pred))
        prec = float(precision_score(self.y_test, y_pred, average="weighted", zero_division=0))
        rec = float(recall_score(self.y_test, y_pred, average="weighted", zero_division=0))
        f1 = float(f1_score(self.y_test, y_pred, average="weighted", zero_division=0))
        auc = float(roc_auc_score(self.y_test, y_proba))

        clf_report = classification_report(self.y_test, y_pred, output_dict=True, zero_division=0)
        cm = confusion_matrix(self.y_test, y_pred).tolist()

        infer_ms = measure_inference_time(ftt, self.X_test, n_runs=50)
        mem_mb = compute_memory_usage()
        size_mb = get_model_size_mb(ftt)

        feat_imp_vals = ftt.get_feature_importances(self.X_test)
        feat_imp = {name: float(val) for name, val in zip(self.feature_names, feat_imp_vals)}

        result = ModelResult(
            model_name="ft_transformer",
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
            best_hyperparams={str(k): str(v) for k, v in params.items()},
            classification_report=clf_report,
            confusion_matrix=cm,
            feature_importances=feat_imp,
        )

        # Log to MLflow
        try:
            mlflow.set_experiment(f"disease_prediction_{self.dataset_name}")
            with mlflow.start_run(run_name="ft_transformer", nested=True):
                mlflow.set_tags({
                    "model_name": "ft_transformer",
                    "task_type": f"disease_prediction_{self.dataset_name}",
                    "dataset": self.dataset_name
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
            logger.warning("[disease-ftt] MLflow logging failed: %s", exc)

        return result
