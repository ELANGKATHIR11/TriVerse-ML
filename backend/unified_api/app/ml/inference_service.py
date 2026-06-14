import base64
import io
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Tuple

import joblib
import numpy as np
import tensorflow as tf
import torch
from PIL import Image

# Import handlers/models to reuse structural code
from app.ml.handwriting.resnet_model import DEVICE as TORCH_DEVICE

# Resolve TRAINED_MODELS_DIR absolutely from this file's location.
# Path: app/ml/inference_service.py → resolve parents[2] = backend/unified_api
BASE_DIR = Path(__file__).resolve().parents[2]  # backend/unified_api
TRAINED_MODELS_DIR = BASE_DIR / "trained_models"

# Safety: also try reading env override (set by Electron launcher)
import os as _os
_env_override = _os.environ.get("TRIVERSE_MODELS_DIR")
if _env_override and Path(_env_override).is_dir():
    TRAINED_MODELS_DIR = Path(_env_override)

class ModelManager:
    """Manages loading, caching, and running ML models for inference."""
    _models: Dict[str, Any] = {}
    _preprocessors: Dict[str, Any] = {}

    @classmethod
    def load_model(cls, task_type: str, model_name: str) -> Any:
        cache_key = f"{task_type}_{model_name}"
        if cache_key in cls._models:
            return cls._models[cache_key]

        model_path = TRAINED_MODELS_DIR / task_type / f"{model_name}.joblib"
        if task_type == "vision":
            if model_name == "cnn":
                model_path = TRAINED_MODELS_DIR / "vision" / "cnn.h5"
                if not model_path.exists():
                    raise FileNotFoundError(f"CNN model file not found at {model_path}")
                model = tf.keras.models.load_model(str(model_path))
                cls._models[cache_key] = model
                return model
            elif model_name == "resnet18":
                model_path = TRAINED_MODELS_DIR / "vision" / "resnet18.pth"
                if not model_path.exists():
                    raise FileNotFoundError(f"ResNet18 weights not found at {model_path}")
                from app.ml.handwriting.resnet_model import ResNet18Trainer
                dummy = np.zeros((1, 28, 28, 1), dtype=np.float32)
                trainer = ResNet18Trainer(dummy, dummy, np.zeros((1,)), np.zeros((1,)), num_classes=10)
                model = trainer.build_model()
                model.load_state_dict(torch.load(str(model_path), map_location=TORCH_DEVICE))
                model.eval()
                cls._models[cache_key] = model
                return model

        # Default joblib loading
        if not model_path.exists():
            raise FileNotFoundError(f"Model {model_name} for task {task_type} not found at {model_path}")
        model = joblib.load(str(model_path))
        cls._models[cache_key] = model
        return model

    @classmethod
    def load_preprocessor(cls, task_type: str) -> Any:
        if task_type in cls._preprocessors:
            return cls._preprocessors[task_type]

        preprocessor_path = TRAINED_MODELS_DIR / task_type / "preprocessor.joblib"
        if not preprocessor_path.exists():
            raise FileNotFoundError(f"Preprocessor not found at {preprocessor_path}")
        preprocessor = joblib.load(str(preprocessor_path))
        cls._preprocessors[task_type] = preprocessor
        return preprocessor


class CreditInferenceService:
    @staticmethod
    def predict(features: Dict[str, float], model_name: str = "random_forest") -> Dict[str, Any]:
        # Supported Models: logistic_regression, decision_tree, random_forest, catboost, mlp
        model_map = {
            "logisticregression": "logistic_regression",
            "decisiontree": "decision_tree",
            "randomforest": "random_forest",
            "catboost": "catboost",
            "mlp": "mlp",
            "logistic regression": "logistic_regression",
            "decision tree": "decision_tree",
            "random forest": "random_forest",
        }
        normalized_name = model_map.get(model_name.lower().replace("_", ""), model_name)

        try:
            preprocessor = ModelManager.load_preprocessor("credit")
            model = ModelManager.load_model("credit", normalized_name)
        except Exception as e:
            raise FileNotFoundError(f"Credit scoring model not loaded: {str(e)}")

        from app.ml.credit.data import GMSC_FEATURE_COLS
        feat_vals = []
        for col in GMSC_FEATURE_COLS:
            feat_vals.append(features.get(col, 0.0))

        X_raw = np.array([feat_vals])
        import pandas as pd
        df_raw = pd.DataFrame(X_raw, columns=GMSC_FEATURE_COLS)
        X_processed = preprocessor.transform(df_raw)

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X_processed)[0][1]
        else:
            pred = model.predict(X_processed)[0]
            proba = 0.99 if pred == 1 else 0.05

        score = int(round(300 + 550 * (1.0 - proba)))

        if score >= 720:
            risk = "Low Risk"
        elif score >= 620:
            risk = "Medium Risk"
        else:
            risk = "High Risk"

        prediction = 1 if proba > 0.5 else 0

        return {
            "prediction": prediction,
            "probability": proba,
            "score": score,
            "risk": risk
        }


class DiseaseInferenceService:
    @staticmethod
    def predict(features: Dict[str, float], model_name: str = "xgboost") -> Dict[str, Any]:
        # Supported Models: logistic_regression, svm, random_forest, xgboost, catboost, mlp
        model_map = {
            "logisticregression": "logistic_regression",
            "svm": "svm",
            "randomforest": "random_forest",
            "xgboost": "xgboost",
            "catboost": "catboost",
            "mlp": "mlp",
            "logistic regression": "logistic_regression",
            "random forest": "random_forest",
        }
        normalized_name = model_map.get(model_name.lower().replace("_", ""), model_name)

        try:
            preprocessor = ModelManager.load_preprocessor("disease")
            model = ModelManager.load_model("disease", normalized_name)
        except Exception as e:
            raise FileNotFoundError(f"Disease prediction model not loaded: {str(e)}")

        from app.ml.disease.data import HEART_COLS
        default_features = {
            "age": 50.0,
            "sex": 1.0,
            "cp": 0.0,
            "trestbps": 120.0,
            "chol": 200.0,
            "fbs": 0.0,
            "restecg": 0.0,
            "thalach": 150.0,
            "exang": 0.0,
            "oldpeak": 0.0,
            "slope": 1.0,
            "ca": 0.0,
            "thal": 1.0
        }
        
        merged_features = {**default_features}
        for k, v in features.items():
            if k in HEART_COLS:
                merged_features[k] = v

        feature_cols = [c for c in HEART_COLS if c != "target"]
        feat_vals = [merged_features[col] for col in feature_cols]

        X_raw = np.array([feat_vals])
        import pandas as pd
        df_raw = pd.DataFrame(X_raw, columns=feature_cols)
        X_processed = preprocessor.transform(df_raw)

        if hasattr(model, "predict_proba"):
            proba = model.predict_proba(X_processed)[0][1]
        else:
            pred = model.predict(X_processed)[0]
            proba = 0.99 if pred == 1 else 0.05

        prediction = 1 if proba > 0.5 else 0

        if proba >= 0.7:
            risk = "High Risk"
        elif proba >= 0.4:
            risk = "Moderate Risk"
        else:
            risk = "Low Risk"

        return {
            "prediction": prediction,
            "probability": proba,
            "risk": risk
        }


class HandwritingInferenceService:
    @staticmethod
    def predict(image_b64: str, model_name: str = "cnn") -> Dict[str, Any]:
        if "," in image_b64:
            image_b64 = image_b64.split(",")[1]
        
        image_bytes = base64.b64decode(image_b64)
        img = Image.open(io.BytesIO(image_bytes)).convert("L")
        img = img.resize((28, 28))
        
        img_array = np.array(img, dtype=np.float32) / 255.0
        
        norm_model_name = model_name.lower()
        try:
            model = ModelManager.load_model("vision", norm_model_name)
        except Exception as e:
            raise FileNotFoundError(f"Vision model not loaded: {str(e)}")

        if norm_model_name == "cnn":
            X = np.expand_dims(img_array, axis=(0, -1))
            probs = model.predict(X, verbose=0)[0]
        else:
            X = np.expand_dims(img_array, axis=(0, -1))
            from app.ml.handwriting.resnet_model import ResNet18Trainer
            tensor = ResNet18Trainer._to_3channel_tensor(X).to(TORCH_DEVICE)
            with torch.no_grad():
                logits = model(tensor)
                probs = torch.softmax(logits, dim=1).cpu().numpy()[0]

        probs_list = [float(p) for p in probs]
        predicted_class_idx = int(np.argmax(probs_list))
        
        top_indices = np.argsort(probs_list)[-3:][::-1]
        top_predictions = []
        for idx in top_indices:
            top_predictions.append({
                "class": str(idx),
                "probability": float(probs_list[idx])
            })
            
        return {
            "prediction": str(predicted_class_idx),
            "probability": float(probs_list[predicted_class_idx]),
            "top_predictions": top_predictions,
            "probabilities": probs_list
        }
