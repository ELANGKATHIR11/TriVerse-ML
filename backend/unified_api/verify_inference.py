"""
verify_inference.py
Quick smoke-test for all three inference services.
Run from: backend/unified_api/
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import base64
import numpy as np
from PIL import Image
import io

print("=" * 60)
print("TriVerse AI — Inference Smoke Test")
print("=" * 60)

# ── 1. Credit Scoring ──────────────────────────────────────────────────────
print("\n[1] Credit Scoring Inference")
from app.ml.inference_service import CreditInferenceService

features = {
    "RevolvingUtilizationOfUnsecuredLines": 0.5,
    "age": 45,
    "NumberOfTime30-59DaysPastDueNotWorse": 0,
    "DebtRatio": 0.3,
    "MonthlyIncome": 5000,
    "NumberOfOpenCreditLinesAndLoans": 5,
    "NumberOfTimes90DaysLate": 0,
    "NumberRealEstateLoansOrLines": 1,
    "NumberOfTime60-89DaysPastDueNotWorse": 0,
    "NumberOfDependents": 2,
}

for model_name in ["random_forest", "catboost", "logistic_regression"]:
    try:
        res = CreditInferenceService.predict(features, model_name=model_name)
        print(f"  {model_name}: score={res['score']} risk={res['risk']} proba={res['probability']:.4f}")
    except Exception as e:
        print(f"  {model_name}: FAILED — {e}")

# ── 2. Disease Prediction ─────────────────────────────────────────────────
print("\n[2] Disease Prediction Inference")
from app.ml.inference_service import DiseaseInferenceService

heart_features = {
    "age": 55, "sex": 1, "cp": 1, "trestbps": 130,
    "chol": 250, "fbs": 0, "restecg": 1, "thalach": 140,
    "exang": 0, "oldpeak": 1.5, "slope": 1, "ca": 1, "thal": 2
}

for model_name in ["xgboost", "random_forest", "svm", "catboost"]:
    try:
        res = DiseaseInferenceService.predict(heart_features, model_name=model_name)
        print(f"  {model_name}: prediction={res['prediction']} risk={res['risk']} proba={res['probability']:.4f}")
    except Exception as e:
        print(f"  {model_name}: FAILED — {e}")

# ── 3. Handwriting Recognition ────────────────────────────────────────────
print("\n[3] Handwriting (CNN) Inference")
from app.ml.inference_service import HandwritingInferenceService

img = Image.fromarray(np.zeros((28, 28), dtype=np.uint8))
buf = io.BytesIO()
img.save(buf, format="PNG")
img_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

try:
    res = HandwritingInferenceService.predict(img_b64, model_name="cnn")
    print(f"  CNN: predicted_class={res['prediction']} confidence={res['probability']:.4f}")
    print(f"  Top-3: {res['top_predictions']}")
except Exception as e:
    print(f"  CNN: FAILED — {e}")

print("\n" + "=" * 60)
print("Smoke test complete.")
print("=" * 60)
