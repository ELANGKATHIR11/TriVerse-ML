"""
generate_credit_preprocessor.py
Regenerates the credit/preprocessor.joblib by running the CreditDataLoader (primary/GMSC).
Run from: backend/unified_api/
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.ml.credit.data import CreditDataLoader
import joblib

loader = CreditDataLoader()
X_train, X_test, y_train, y_test, feat_names, preprocessor = loader.load("primary")

print(f"Feature count: {len(feat_names)}")
print(f"Feature names: {feat_names}")

out_dir = Path(__file__).resolve().parent / "trained_models" / "credit"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "preprocessor.joblib"
joblib.dump(preprocessor, str(out_path))
print(f"[OK] Credit preprocessor saved: {out_path}  ({out_path.stat().st_size} bytes)")
print(f"[OK] Preprocessor type: {type(preprocessor).__name__}")
