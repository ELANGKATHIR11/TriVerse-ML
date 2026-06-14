"""
credit/data.py - Data loading and preprocessing for credit scoring tasks.

Supports:
  - Give Me Some Credit (primary)  : 150 000 rows, 10 features
  - German Credit (secondary)      :   1 000 rows, 20 features
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

DATASET_PATH = Path(__file__).resolve().parent.parent.parent / "datasets" / "credit_scoring_give_me_some_credit.csv"
GERMAN_PATH = Path(__file__).resolve().parent.parent.parent / "datasets" / "credit_scoring_german.csv"

# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------

# Give Me Some Credit feature columns (excluding target & row id)
GMSC_FEATURE_COLS: list[str] = [
    "RevolvingUtilizationOfUnsecuredLines",
    "age",
    "NumberOfTime30-59DaysPastDueNotWorse",
    "DebtRatio",
    "MonthlyIncome",
    "NumberOfOpenCreditLinesAndLoans",
    "NumberOfTimes90DaysLate",
    "NumberRealEstateLoansOrLines",
    "NumberOfTime60-89DaysPastDueNotWorse",
    "NumberOfDependents",
]
GMSC_TARGET_COL = "SeriousDlqin2yrs"

# German Credit column names (UCI dataset has no header)
GERMAN_FEATURE_COLS: list[str] = [
    "checking_status",
    "duration",
    "credit_history",
    "purpose",
    "credit_amount",
    "savings_status",
    "employment",
    "installment_commitment",
    "personal_status",
    "other_parties",
    "residence_since",
    "property_magnitude",
    "age",
    "other_payment_plans",
    "housing",
    "existing_credits",
    "job",
    "num_dependents",
    "own_telephone",
    "foreign_worker",
    "class",
]
GERMAN_TARGET_COL = "class"


# ---------------------------------------------------------------------------
# Main loader class
# ---------------------------------------------------------------------------


class CreditDataLoader:
    """
    Loads and preprocesses credit scoring datasets.

    Usage::

        loader = CreditDataLoader()
        X_train, X_test, y_train, y_test, feature_names, preprocessor = loader.load()
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
        dataset: Literal["primary", "german"] = "primary",
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str], Pipeline]:
        """
        Load and preprocess the chosen credit dataset.

        Parameters
        ----------
        dataset:
            ``'primary'`` → Give Me Some Credit (default)
            ``'german'``  → German Credit dataset

        Returns
        -------
        tuple of:
            X_train, X_test, y_train, y_test, feature_names, preprocessor
        """
        self._dataset = dataset

        if dataset == "primary":
            return self._load_give_me_some_credit()
        elif dataset == "german":
            return self._load_german()
        else:
            raise ValueError(f"Unknown dataset '{dataset}'. Choose 'primary' or 'german'.")

    def get_stats(self) -> dict:
        """
        Return descriptive statistics for the last loaded dataset.

        Returns
        -------
        dict with keys:
            row_count, col_count, missing_pct, class_balance, feature_stats
        """
        if self._raw_df is None:
            raise RuntimeError("Call load() before get_stats().")

        df = self._raw_df

        # Determine target column
        if self._dataset == "primary":
            target_col = GMSC_TARGET_COL
            feature_cols = GMSC_FEATURE_COLS
        else:
            target_col = GERMAN_TARGET_COL
            feature_cols = [c for c in GERMAN_FEATURE_COLS if c != GERMAN_TARGET_COL]

        total_cells = df.shape[0] * df.shape[1]
        missing_cells = df.isnull().sum().sum()

        class_counts = df[target_col].value_counts(normalize=True).to_dict()

        feature_stats: dict[str, dict] = {}
        for col in feature_cols:
            if col not in df.columns:
                continue
            s = df[col]
            feature_stats[col] = {
                "mean": float(s.mean()) if pd.api.types.is_numeric_dtype(s) else None,
                "std": float(s.std()) if pd.api.types.is_numeric_dtype(s) else None,
                "min": float(s.min()) if pd.api.types.is_numeric_dtype(s) else None,
                "max": float(s.max()) if pd.api.types.is_numeric_dtype(s) else None,
                "missing_count": int(s.isnull().sum()),
                "dtype": str(s.dtype),
            }

        return {
            "row_count": int(df.shape[0]),
            "col_count": int(df.shape[1]),
            "missing_pct": float(missing_cells / total_cells * 100),
            "class_balance": {str(k): float(v) for k, v in class_counts.items()},
            "feature_stats": feature_stats,
        }

    # ------------------------------------------------------------------
    # Private loaders
    # ------------------------------------------------------------------

    def _load_give_me_some_credit(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str], Pipeline]:
        logger.info("Loading Give Me Some Credit from %s", DATASET_PATH)
        df = pd.read_csv(DATASET_PATH, index_col=0)
        self._raw_df = df.copy()

        # ── Feature engineering ──────────────────────────────────────────
        # 1. Clip extreme outliers in utilisation (> 1 means over-limit)
        df["RevolvingUtilizationOfUnsecuredLines"] = df[
            "RevolvingUtilizationOfUnsecuredLines"
        ].clip(upper=1.0)

        # 2. Cap past-due counts at realistic maximum (cap at 98th percentile)
        for col in [
            "NumberOfTime30-59DaysPastDueNotWorse",
            "NumberOfTimes90DaysLate",
            "NumberOfTime60-89DaysPastDueNotWorse",
        ]:
            cap = df[col].quantile(0.98)
            df[col] = df[col].clip(upper=cap)

        # 3. Log-transform right-skewed monetary columns
        df["MonthlyIncome_log"] = np.log1p(df["MonthlyIncome"].fillna(0))
        df["DebtRatio_log"] = np.log1p(df["DebtRatio"].clip(upper=df["DebtRatio"].quantile(0.99)))

        # 4. Age bins (one-hot encoded)
        df["age_bin"] = pd.cut(
            df["age"],
            bins=[0, 25, 35, 50, 65, 200],
            labels=["18-25", "26-35", "36-50", "51-65", "65+"],
        )
        age_dummies = pd.get_dummies(df["age_bin"], prefix="age_bin", drop_first=True)
        df = pd.concat([df, age_dummies], axis=1)

        # 5. Total late payments
        df["total_late_payments"] = (
            df["NumberOfTime30-59DaysPastDueNotWorse"]
            + df["NumberOfTimes90DaysLate"]
            + df["NumberOfTime60-89DaysPastDueNotWorse"]
        )

        # ── Build feature list ───────────────────────────────────────────
        engineered_features = [
            "RevolvingUtilizationOfUnsecuredLines",
            "age",
            "NumberOfTime30-59DaysPastDueNotWorse",
            "DebtRatio",
            "MonthlyIncome",
            "NumberOfOpenCreditLinesAndLoans",
            "NumberOfTimes90DaysLate",
            "NumberRealEstateLoansOrLines",
            "NumberOfTime60-89DaysPastDueNotWorse",
            "NumberOfDependents",
            "MonthlyIncome_log",
            "DebtRatio_log",
            "total_late_payments",
        ] + list(age_dummies.columns)

        # Keep only features that exist in df
        feature_names = [f for f in engineered_features if f in df.columns]

        X = df[feature_names].values.astype(np.float32)
        y = df[GMSC_TARGET_COL].values.astype(np.int32)

        # ── Preprocessing pipeline ───────────────────────────────────────
        preprocessor = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])

        # ── Train / test split (stratified 80/20) ───────────────────────
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.20,
            random_state=self._random_state,
            stratify=y,
        )

        # Fit preprocessor on train only
        X_train = preprocessor.fit_transform(X_train).astype(np.float32)
        X_test = preprocessor.transform(X_test).astype(np.float32)

        logger.info(
            "GMSC loaded: train=%d test=%d features=%d positive_rate=%.3f",
            len(X_train),
            len(X_test),
            len(feature_names),
            y.mean(),
        )
        return X_train, X_test, y_train, y_test, feature_names, preprocessor

    def _load_german(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str], Pipeline]:
        """
        Load German Credit dataset.

        The file may or may not have a header row; we handle both cases.
        Target column: 'class' (1 = Good → 0, 2 = Bad → 1) — binarised
        so that 1 = default risk.
        """
        logger.info("Loading German Credit from %s", GERMAN_PATH)

        # Try reading with header first
        df_probe = pd.read_csv(GERMAN_PATH, nrows=1)
        if df_probe.columns[0] == "checking_status":
            # File has a proper header
            df = pd.read_csv(GERMAN_PATH)
        else:
            # No header — assign our column names
            df = pd.read_csv(GERMAN_PATH, header=None, names=GERMAN_FEATURE_COLS, sep=r"\s+")

        self._raw_df = df.copy()

        # Binarise target: original 1=Good (no default), 2=Bad (default)
        # We want 1 = default risk
        df["target"] = (df[GERMAN_TARGET_COL] == 2).astype(int)

        # Categorical features → ordinal encoding (simple label)
        cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
        cat_cols = [c for c in cat_cols if c not in [GERMAN_TARGET_COL, "target"]]
        for col in cat_cols:
            df[col] = pd.Categorical(df[col]).codes

        feature_cols = [c for c in df.columns if c not in [GERMAN_TARGET_COL, "target"]]
        feature_names = feature_cols

        X = df[feature_names].values.astype(np.float32)
        y = df["target"].values.astype(np.int32)

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
            "German Credit loaded: train=%d test=%d features=%d",
            len(X_train), len(X_test), len(feature_names),
        )
        return X_train, X_test, y_train, y_test, feature_names, preprocessor
