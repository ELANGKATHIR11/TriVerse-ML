"""
generate_disease_preprocessor.py
Regenerates the disease/preprocessor.joblib by running the DiseaseDataLoader.
Run from: backend/unified_api/
"""
import sys
from pathlib import Path

# Add backend/unified_api to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.ml.disease.data import DiseaseDataLoader
import joblib

loader = DiseaseDataLoader()
X_train, X_test, y_train, y_test, feat_names, preprocessor = loader.load("heart")

out_dir = Path(__file__).resolve().parent / "trained_models" / "disease"
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "preprocessor.joblib"
joblib.dump(preprocessor, str(out_path))
print(f"[OK] Disease preprocessor saved: {out_path}  ({out_path.stat().st_size} bytes)")
print(f"[OK] Preprocessor type: {type(preprocessor).__name__}")
