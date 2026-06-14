import os
import sys
from pathlib import Path

# Add task root directory to python path for testing imports
task_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(task_root))

import pytest
import numpy as np
from src.backend.ml_handwriting.data import HandwritingDataLoader

def test_mnist_loader_load():
    loader = HandwritingDataLoader()
    # Load MNIST
    X_train, X_test, y_train, y_test, class_names = loader.load_mnist()
    
    assert X_train is not None
    assert X_test is not None
    assert len(y_train) == len(X_train)
    assert len(y_test) == len(X_test)
    assert len(class_names) == 10
    
    # Assert dimensions (N, 28, 28, 1)
    assert X_train.shape[1:] == (28, 28, 1)
    assert X_test.shape[1:] == (28, 28, 1)
    assert X_train.dtype == np.float32

def test_emnist_loader_load():
    loader = HandwritingDataLoader()
    # Load EMNIST
    X_train, X_test, y_train, y_test, class_names = loader.load_emnist()
    
    assert X_train is not None
    assert X_test is not None
    assert len(y_train) == len(X_train)
    assert len(y_test) == len(X_test)
    
    # Assert EMNIST contains 47 classes (or falls back to MNIST 10 classes)
    assert len(class_names) in [10, 47]
    assert X_train.shape[1:] == (28, 28, 1)
