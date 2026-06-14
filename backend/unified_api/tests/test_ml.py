"""Tests for ML pipeline utilities."""
import pytest
import numpy as np
from pathlib import Path
import pandas as pd


@pytest.mark.asyncio
async def test_credit_data_loader():
    """Test credit scoring data loads correctly."""
    from app.ml.credit.data import CreditDataLoader

    loader = CreditDataLoader()
    result = loader.load(dataset="primary")
    X_train, X_test, y_train, y_test, feature_names, preprocessor = result

    assert X_train.shape[0] > 0
    assert X_test.shape[0] > 0
    assert len(feature_names) > 0
    assert set(np.unique(y_train)).issubset({0, 1})


@pytest.mark.asyncio
async def test_disease_data_loader_heart():
    """Test heart disease data loads correctly."""
    from app.ml.disease.data import DiseaseDataLoader

    loader = DiseaseDataLoader()
    X_train, X_test, y_train, y_test, feature_names, preprocessor = loader.load(dataset="heart")

    assert X_train.shape[0] > 0
    assert set(np.unique(y_train)).issubset({0, 1})


@pytest.mark.asyncio
async def test_disease_data_loader_diabetes():
    """Test diabetes data loads correctly."""
    from app.ml.disease.data import DiseaseDataLoader

    loader = DiseaseDataLoader()
    X_train, X_test, y_train, y_test, feature_names, preprocessor = loader.load(dataset="diabetes")
    assert X_train.shape[0] > 0


@pytest.mark.asyncio
async def test_disease_data_loader_breast_cancer():
    """Test breast cancer data loads correctly."""
    from app.ml.disease.data import DiseaseDataLoader

    loader = DiseaseDataLoader()
    X_train, X_test, y_train, y_test, feature_names, preprocessor = loader.load(
        dataset="breast_cancer"
    )
    assert X_train.shape[0] > 0


@pytest.mark.asyncio
async def test_system_monitor():
    """Test system monitor returns valid stats."""
    from app.monitoring.system_monitor import SystemMonitor

    monitor = SystemMonitor()
    stats = monitor.get_stats()

    assert 0 <= stats["cpu_percent"] <= 100
    assert 0 <= stats["ram_percent"] <= 100
    assert stats["ram_total_gb"] > 0
    assert "timestamp" in stats


@pytest.mark.asyncio
async def test_leaderboard_scoring():
    """Test weighted leaderboard score calculation."""
    # Mock metrics
    metrics = {
        "accuracy": 0.95,
        "precision_score": 0.93,
        "recall_score": 0.92,
        "inference_time_ms": 1.5,
        "training_time_sec": 120,
    }

    # weighted_score = accuracy*0.4 + precision*0.2 + recall*0.2 + speed*0.1 + time*0.1
    # speed_score = 1 / (1 + inference_ms/100)
    # time_score = 1 / (1 + training_sec/3600)
    speed_score = 1 / (1 + metrics["inference_time_ms"] / 100)
    time_score = 1 / (1 + metrics["training_time_sec"] / 3600)

    weighted = (
        metrics["accuracy"] * 0.4
        + metrics["precision_score"] * 0.2
        + metrics["recall_score"] * 0.2
        + speed_score * 0.1
        + time_score * 0.1
    )

    assert 0 < weighted <= 1.0
    assert weighted > 0.8  # High quality metrics should score well
