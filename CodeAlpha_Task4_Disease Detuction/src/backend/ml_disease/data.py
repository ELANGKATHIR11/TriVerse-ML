"""
disease/data.py - Data loading and preprocessing for disease prediction.

Supports three datasets:
  - heart        : UCI Cleveland Heart Disease (303 rows, 13 features, binary)
  - diabetes     : Pima Indians Diabetes (768 rows, 8 features, binary)
  - breast_cancer: Breast Cancer Wisconsin (569 rows, 30 features, binary)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dataset paths
# ---------------------------------------------------------------------------

HEART_PATH = Path(__file__).resolve().parent.parent.parent.parent / "datasets" / "disease_prediction_heart.csv"
DIABETES_PATH = Path(__file__).resolve().parent.parent.parent.parent / "datasets" / "disease_prediction_diabetes.csv"
BREAST_PATH = Path(__file__).resolve().parent.parent.parent.parent / "datasets" / "disease_prediction_breast_cancer.csv"

# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------

# UCI Cleveland Heart Disease — no header in file
HEART_COLS: list[str] = [
    "age", "sex", "cp", "trestbps", "chol",
    "fbs", "restecg", "thalach", "exang",
    "oldpeak", "slope", "ca", "thal", "target",
]

# Breast Cancer Wisconsin — no header in file
BREAST_COLS: list[str] = [
    "id", "diagnosis",
    "radius_mean", "texture_mean", "perimeter_mean", "area_mean",
    "smoothness_mean", "compactness_mean", "concavity_mean",
    "concave_points_mean", "symmetry_mean", "fractal_dimension_mean",
    "radius_se", "texture_se", "perimeter_se", "area_se",
    "smoothness_se", "compactness_se", "concavity_se",
    "concave_points_se", "symmetry_se", "fractal_dimension_se",
    "radius_worst", "texture_worst", "perimeter_worst", "area_worst",
    "smoothness_worst", "compactness_worst", "concavity_worst",
    "concave_points_worst", "symmetry_worst", "fractal_dimension_worst",
]

# Diabetes columns are already in the CSV header
DIABETES_TARGET_COL = "Outcome"

# ---------------------------------------------------------------------------
# Loader class
# ---------------------------------------------------------------------------


class DiseaseDataLoader:
    """
    Loads and preprocesses one of the three disease prediction datasets.

    Usage::

        loader = DiseaseDataLoader()
        X_train, X_test, y_train, y_test, feature_names, preprocessor = loader.load('heart')
        stats = loader.get_stats()
    """

    def __init__(self, random_state: int = 42) -> None:
        self._random_state = random_state
        self._raw_df: pd.DataFrame | None = None
        self._dataset: str | None = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(
        self,
        dataset: Literal["heart", "diabetes", "breast_cancer"] = "heart",
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str], Pipeline]:
        """
        Load and preprocess the chosen disease dataset.

        Parameters
        ----------
        dataset:
            One of ``'heart'``, ``'diabetes'``, ``'breast_cancer'``.

        Returns
        -------
        tuple of:
            X_train, X_test, y_train, y_test, feature_names, preprocessor
        """
        self._dataset = dataset

        if dataset == "heart":
            return self._load_heart()
        elif dataset == "diabetes":
            return self._load_diabetes()
        elif dataset == "breast_cancer":
            return self._load_breast_cancer()
        else:
            raise ValueError(
                f"Unknown dataset '{dataset}'. Choose from 'heart', 'diabetes', 'breast_cancer'."
            )

    def get_stats(self) -> dict:
        """
        Return descriptive statistics for the last loaded dataset.

        Returns
        -------
        dict with keys:
            row_count, col_count, missing_pct, class_balance, feature_stats, dataset_name
        """
        if self._raw_df is None:
            raise RuntimeError("Call load() before get_stats().")

        df = self._raw_df

        if self._dataset == "heart":
            target_col = "target"
        elif self._dataset == "diabetes":
            target_col = DIABETES_TARGET_COL
        else:
            target_col = "diagnosis"

        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()

        feature_cols = [c for c in df.columns if c != target_col]
        feature_stats: dict[str, dict] = {}
        for col in feature_cols:
            s = df[col]
            feature_stats[col] = {
                "mean": float(s.mean()) if pd.api.types.is_numeric_dtype(s) else None,
                "std": float(s.std()) if pd.api.types.is_numeric_dtype(s) else None,
                "min": float(s.min()) if pd.api.types.is_numeric_dtype(s) else None,
                "max": float(s.max()) if pd.api.types.is_numeric_dtype(s) else None,
                "missing_count": int(s.isnull().sum()),
                "dtype": str(s.dtype),
            }

        class_counts = df[target_col].value_counts(normalize=True).to_dict()

        return {
            "dataset_name": self._dataset,
            "row_count": int(df.shape[0]),
            "col_count": int(df.shape[1]),
            "missing_pct": float(missing_cells / max(total_cells, 1) * 100),
            "class_balance": {str(k): float(v) for k, v in class_counts.items()},
            "feature_stats": feature_stats,
        }

    # ------------------------------------------------------------------
    # Private loaders
    # ------------------------------------------------------------------

    def _load_heart(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str], Pipeline]:
        """
        Load the UCI Cleveland Heart Disease dataset.

        The CSV file has no header — we assign HEART_COLS.
        Target: 'target' (0 = no disease, 1–4 → binarised to 1 = disease).
        Missing values coded as '?' are imputed with median.
        """
        logger.info("Loading Heart Disease from %s", HEART_PATH)

        # Try reading with/without header
        probe = pd.read_csv(HEART_PATH, nrows=1)
        if probe.columns[0].lower() in ("age", "0", "63", "63.0"):
            if probe.columns[0].lower() == "age":
                df = pd.read_csv(HEART_PATH)
                # Ensure target column
                if "target" not in df.columns and "num" in df.columns:
                    df.rename(columns={"num": "target"}, inplace=True)
            else:
                # No header
                df = pd.read_csv(HEART_PATH, header=None, names=HEART_COLS, na_values="?")
        else:
            df = pd.read_csv(HEART_PATH, header=None, names=HEART_COLS, na_values="?")

        self._raw_df = df.copy()

        # Binarise multi-class target (0 = no disease, else = disease)
        df["target"] = (df["target"] > 0).astype(int)

        feature_names = [c for c in HEART_COLS if c != "target"]
        X = df[feature_names].values.astype(np.float32)
        y = df["target"].values.astype(np.int32)

        return self._split_and_preprocess(X, y, feature_names)

    def _load_diabetes(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str], Pipeline]:
        """
        Load Pima Indians Diabetes dataset.

        Target: 'Outcome' (0 = no diabetes, 1 = diabetes).
        Zeros in Glucose, BloodPressure, SkinThickness, Insulin, BMI are
        physiologically invalid and are replaced with NaN before imputation.
        """
        logger.info("Loading Diabetes from %s", DIABETES_PATH)
        df = pd.read_csv(DIABETES_PATH)
        self._raw_df = df.copy()

        # Replace zero-values with NaN for biological validity
        zero_invalid_cols = [
            "Glucose", "BloodPressure", "SkinThickness", "Insulin", "BMI"
        ]
        for col in zero_invalid_cols:
            if col in df.columns:
                df[col] = df[col].replace(0, np.nan)

        feature_names = [c for c in df.columns if c != DIABETES_TARGET_COL]
        X = df[feature_names].values.astype(np.float32)
        y = df[DIABETES_TARGET_COL].values.astype(np.int32)

        return self._split_and_preprocess(X, y, feature_names)

    def _load_breast_cancer(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str], Pipeline]:
        """
        Load Breast Cancer Wisconsin dataset.

        The CSV may lack a header.  Target: 'diagnosis' (M=1, B=0).
        Drop the 'id' column (non-informative).
        """
        logger.info("Loading Breast Cancer from %s", BREAST_PATH)

        # Probe for header
        probe = pd.read_csv(BREAST_PATH, nrows=1)
        if probe.columns[0].lower() in ("id", "842302"):
            if probe.columns[0].lower() == "id":
                df = pd.read_csv(BREAST_PATH)
            else:
                df = pd.read_csv(BREAST_PATH, header=None, names=BREAST_COLS)
        else:
            df = pd.read_csv(BREAST_PATH, header=None, names=BREAST_COLS)

        self._raw_df = df.copy()

        # Encode target: M → 1, B → 0
        df["diagnosis"] = df["diagnosis"].map({"M": 1, "B": 0})
        # Handle numeric targets (some versions encode M=1 already)
        df["diagnosis"] = pd.to_numeric(df["diagnosis"], errors="coerce").fillna(0).astype(int)

        # Drop id column
        feature_names = [
            c for c in df.columns
            if c not in ("id", "diagnosis", "842302")
        ]

        X = df[feature_names].values.astype(np.float32)
        y = df["diagnosis"].values.astype(np.int32)

        return self._split_and_preprocess(X, y, feature_names)

    # ------------------------------------------------------------------
    # Shared preprocessing
    # ------------------------------------------------------------------

    def _split_and_preprocess(
        self,
        X: np.ndarray,
        y: np.ndarray,
        feature_names: list[str],
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str], Pipeline]:
        """Stratified 80/20 split + impute + scale."""
        preprocessor = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.20,
            random_state=self._random_state,
            stratify=y,
        )

        X_train = preprocessor.fit_transform(X_train).astype(np.float32)
        X_test = preprocessor.transform(X_test).astype(np.float32)

        logger.info(
            "[%s] train=%d test=%d features=%d positive_rate=%.3f",
            self._dataset, len(X_train), len(X_test), len(feature_names), y.mean(),
        )
        return X_train, X_test, y_train, y_test, feature_names, preprocessor
