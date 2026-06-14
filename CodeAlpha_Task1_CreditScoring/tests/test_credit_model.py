import os
import sys
from pathlib import Path

# Add task root directory to python path for testing imports
task_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(task_root))

import pytest
import numpy as np
from src.backend.ml_credit.data import CreditDataLoader

def test_data_loader_load():
    loader = CreditDataLoader(random_state=42)
    # Load dataset
    X_train, X_test, y_train, y_test, feature_names, preprocessor = loader.load(dataset="primary")
    
    assert X_train is not None
    assert X_test is not None
    assert len(y_train) == len(X_train)
    assert len(y_test) == len(X_test)
    assert len(feature_names) > 0
    assert preprocessor is not None

def test_data_loader_shapes():
    loader = CreditDataLoader(random_state=42)
    X_train, X_test, y_train, y_test, feature_names, _ = loader.load(dataset="primary")
    
    # Assert column counts match
    assert X_train.shape[1] == len(feature_names)
    assert X_test.shape[1] == len(feature_names)
    assert len(np.unique(y_train)) == 2  # Binary classification
