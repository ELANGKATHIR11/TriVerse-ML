"""
explainability.py - SHAP and LIME explanations for all ML models.

Provides:
  - ExplainabilityEngine.explain_shap()  → base64 PNG + feature importances
  - ExplainabilityEngine.explain_lime()  → list of {feature, value, weight} + base64 PNG
  - ExplainabilityEngine.explain_image_shap() → GradientExplainer for CNNs
"""

from __future__ import annotations

import base64
import logging
import warnings
from io import BytesIO
from typing import Any, Literal

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import shap
import lime
import lime.lime_tabular

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class ExplainabilityEngine:
    """
    Unified SHAP + LIME explainability for tabular and image models.

    All plotting is done with the non-interactive ``Agg`` matplotlib backend
    so it is safe to call from async contexts / background threads.
    """

    # ------------------------------------------------------------------
    # SHAP explanations
    # ------------------------------------------------------------------

    def explain_shap(
        self,
        model: Any,
        X_train: np.ndarray,
        X_test: np.ndarray,
        feature_names: list[str],
        model_type: Literal["tree", "linear", "kernel"] = "tree",
        max_display: int = 20,
        background_samples: int = 100,
    ) -> dict[str, Any]:
        """
        Compute SHAP values and generate a summary plot.

        Parameters
        ----------
        model:
            Fitted model with a ``predict`` or ``predict_proba`` method.
        X_train:
            Training data (numpy array), used as SHAP background.
        X_test:
            Test data to explain.
        feature_names:
            List of feature name strings.
        model_type:
            ``'tree'``   → TreeExplainer (fast, for RF/XGB/CatBoost/DT)
            ``'linear'`` → LinearExplainer (for LogisticRegression)
            ``'kernel'`` → KernelExplainer (model-agnostic, slow)
        max_display:
            Maximum number of features to display in the summary plot.
        background_samples:
            Number of background samples for KernelExplainer.

        Returns
        -------
        dict with keys:
            ``values_b64``          : base64-encoded PNG string of the summary plot
            ``feature_importances`` : dict {feature_name: mean_abs_shap}
        """
        warnings.filterwarnings("ignore")

        try:
            explainer, shap_values = self._build_shap_explainer(
                model=model,
                X_train=X_train,
                X_test=X_test,
                model_type=model_type,
                background_samples=background_samples,
            )
        except Exception as exc:
            logger.error("[SHAP] Explainer creation failed: %s", exc)
            return {"values_b64": None, "feature_importances": {}}

        # ── Normalise shap_values to 2-D array ──────────────────────────
        sv = self._normalise_shap_values(shap_values)

        # ── Feature importances: mean |SHAP| ────────────────────────────
        mean_abs = np.abs(sv).mean(axis=0)
        feat_names = feature_names[: sv.shape[1]]
        feat_importance = {
            name: float(val)
            for name, val in zip(feat_names, mean_abs)
        }

        # ── Summary plot ─────────────────────────────────────────────────
        values_b64 = self._shap_summary_plot_b64(
            shap_values=sv,
            X_test=X_test[:, : sv.shape[1]],
            feature_names=feat_names,
            max_display=max_display,
        )

        return {
            "values_b64": values_b64,
            "feature_importances": feat_importance,
        }

    # ------------------------------------------------------------------
    # LIME explanations
    # ------------------------------------------------------------------

    def explain_lime(
        self,
        model: Any,
        X_train: np.ndarray,
        X_test: np.ndarray,
        feature_names: list[str],
        instance_idx: int = 0,
        num_features: int = 10,
        num_samples: int = 1000,
        class_names: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Generate a LIME explanation for a single test instance.

        Parameters
        ----------
        model:
            Fitted model with ``predict_proba``.
        X_train:
            Training data for LIME background statistics.
        X_test:
            Test data; the instance at ``instance_idx`` is explained.
        feature_names:
            List of feature name strings.
        instance_idx:
            Index into X_test of the instance to explain.
        num_features:
            Number of features to include in the explanation.
        num_samples:
            Number of neighbourhood samples generated by LIME.
        class_names:
            Optional labels for the target classes.

        Returns
        -------
        dict with keys:
            ``explanation`` : list of dicts {feature, value, weight}
            ``plot_b64``    : base64-encoded PNG of the LIME bar chart
            ``instance_idx``: int
            ``predicted_class``: int
            ``predicted_proba``: float (probability of class 1)
        """
        if class_names is None:
            class_names = ["Negative", "Positive"]

        try:
            predict_fn = self._get_predict_fn(model)
        except AttributeError:
            logger.error("[LIME] Model has no predict_proba; cannot compute LIME.")
            return {
                "explanation": [],
                "plot_b64": None,
                "instance_idx": instance_idx,
                "predicted_class": None,
                "predicted_proba": None,
            }

        explainer = lime.lime_tabular.LimeTabularExplainer(
            training_data=X_train,
            feature_names=feature_names,
            class_names=class_names,
            mode="classification",
            random_state=42,
        )

        instance = X_test[instance_idx]

        try:
            exp = explainer.explain_instance(
                data_row=instance,
                predict_fn=predict_fn,
                num_features=num_features,
                num_samples=num_samples,
                top_labels=1,
            )
        except Exception as exc:
            logger.error("[LIME] explain_instance failed: %s", exc)
            return {
                "explanation": [],
                "plot_b64": None,
                "instance_idx": instance_idx,
                "predicted_class": None,
                "predicted_proba": None,
            }

        # ── Extract explanation list ─────────────────────────────────────
        label = exp.available_labels()[0]
        raw_explanation = exp.as_list(label=label)
        explanation_list = [
            {"feature": feat, "weight": float(weight)}
            for feat, weight in raw_explanation
        ]

        # ── Predicted class / proba ──────────────────────────────────────
        proba_arr = predict_fn(instance.reshape(1, -1))[0]
        predicted_class = int(np.argmax(proba_arr))
        predicted_proba = float(proba_arr[1]) if len(proba_arr) > 1 else float(proba_arr[0])

        # ── Plot ─────────────────────────────────────────────────────────
        plot_b64 = self._lime_plot_b64(explanation_list, instance_idx, predicted_class)

        return {
            "explanation": explanation_list,
            "plot_b64": plot_b64,
            "instance_idx": instance_idx,
            "predicted_class": predicted_class,
            "predicted_proba": predicted_proba,
        }

    # ------------------------------------------------------------------
    # Image SHAP (CNN / PyTorch)
    # ------------------------------------------------------------------

    def explain_image_shap(
        self,
        model: Any,
        images: np.ndarray,
        background_images: np.ndarray | None = None,
        max_evals: int = 500,
    ) -> dict[str, Any]:
        """
        Explain image-based model predictions using SHAP GradientExplainer.

        Designed for PyTorch models that accept (N, C, H, W) tensors.

        Parameters
        ----------
        model:
            PyTorch ``nn.Module`` in eval mode.
        images:
            Numpy array of shape (N, C, H, W) or (N, H, W, C).
        background_images:
            Background images for the explainer.  If None, uses ``images[:10]``.
        max_evals:
            Maximum evaluations for partition explainer (fallback).

        Returns
        -------
        dict with keys:
            ``shap_values``  : numpy array of SHAP values
            ``plot_b64``     : base64-encoded PNG of SHAP image plot
            ``n_explained``  : number of images explained
        """
        import torch

        model.eval()

        if background_images is None:
            background_images = images[:min(10, len(images))]

        # Convert to torch tensors
        bg_tensor = torch.tensor(background_images, dtype=torch.float32)
        img_tensor = torch.tensor(images, dtype=torch.float32)

        try:
            gradient_explainer = shap.GradientExplainer(model, bg_tensor)
            shap_values = gradient_explainer.shap_values(img_tensor)
        except Exception as exc:
            logger.error("[SHAP image] GradientExplainer failed: %s", exc)
            return {"shap_values": None, "plot_b64": None, "n_explained": 0}

        # ── Plot first image explanation ─────────────────────────────────
        plot_b64: str | None = None
        try:
            fig, ax = plt.subplots(1, 1, figsize=(6, 6))
            if isinstance(shap_values, list):
                sv_plot = shap_values[0]
            else:
                sv_plot = shap_values

            # Aggregate channels for display
            sv_display = np.abs(sv_plot[0]).mean(axis=0) if sv_plot.ndim == 4 else sv_plot[0]
            img_display = images[0]
            if img_display.ndim == 3 and img_display.shape[0] in (1, 3):
                img_display = img_display.transpose(1, 2, 0)

            ax.imshow(img_display, cmap="gray" if img_display.ndim == 2 else None, alpha=0.5)
            ax.imshow(sv_display, cmap="RdBu", alpha=0.5)
            ax.axis("off")
            ax.set_title("SHAP Attribution Map")

            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
            plt.close(fig)
            buf.seek(0)
            plot_b64 = base64.b64encode(buf.read()).decode("utf-8")
        except Exception as exc:
            logger.warning("[SHAP image] plot generation failed: %s", exc)

        return {
            "shap_values": shap_values if not isinstance(shap_values, list) else np.array(shap_values),
            "plot_b64": plot_b64,
            "n_explained": len(images),
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_shap_explainer(
        self,
        model: Any,
        X_train: np.ndarray,
        X_test: np.ndarray,
        model_type: str,
        background_samples: int,
    ) -> tuple[Any, Any]:
        """Instantiate the right SHAP explainer and compute values."""
        if model_type == "tree":
            explainer = shap.TreeExplainer(
                model,
                feature_perturbation="tree_path_dependent",
            )
            shap_values = explainer.shap_values(X_test)

        elif model_type == "linear":
            # Background: median of training data
            background = shap.maskers.Independent(X_train, max_samples=background_samples)
            explainer = shap.LinearExplainer(model, masker=background)
            shap_values = explainer.shap_values(X_test)

        else:  # kernel (model-agnostic)
            # Use k-means summary as background to keep computation tractable
            n_bg = min(background_samples, len(X_train))
            background = shap.sample(X_train, n_bg)

            predict_fn = self._get_predict_fn(model)

            explainer = shap.KernelExplainer(predict_fn, background)
            n_explain = min(50, len(X_test))  # KernelExplainer is slow; cap sample
            shap_values = explainer.shap_values(X_test[:n_explain], nsamples=100)

        return explainer, shap_values

    def _normalise_shap_values(self, shap_values: Any) -> np.ndarray:
        """
        Ensure SHAP values are a 2-D array (n_samples, n_features).

        TreeExplainer may return a list (one per class) or a 3-D array.
        We take index 1 (positive class) for binary problems.
        """
        if isinstance(shap_values, list):
            if len(shap_values) == 2:
                return np.array(shap_values[1])
            return np.array(shap_values[0])

        sv = np.array(shap_values)
        if sv.ndim == 3:
            # shape (n_samples, n_features, n_classes) — take last class
            return sv[:, :, -1]
        if sv.ndim == 2:
            return sv

        # 1-D edge case
        return sv.reshape(1, -1)

    def _shap_summary_plot_b64(
        self,
        shap_values: np.ndarray,
        X_test: np.ndarray,
        feature_names: list[str],
        max_display: int,
    ) -> str | None:
        """Generate SHAP beeswarm summary plot and return as base64 PNG."""
        try:
            fig, ax = plt.subplots(figsize=(10, max(6, min(max_display * 0.4, 16))))

            shap.summary_plot(
                shap_values,
                X_test,
                feature_names=feature_names,
                max_display=max_display,
                show=False,
                plot_size=None,
            )

            buf = BytesIO()
            plt.savefig(buf, format="png", bbox_inches="tight", dpi=120)
            plt.close("all")
            buf.seek(0)
            return base64.b64encode(buf.read()).decode("utf-8")
        except Exception as exc:
            logger.warning("[SHAP] summary plot generation failed: %s", exc)
            plt.close("all")
            return None

    def _lime_plot_b64(
        self,
        explanation_list: list[dict],
        instance_idx: int,
        predicted_class: int,
    ) -> str | None:
        """Generate LIME horizontal bar chart and return as base64 PNG."""
        try:
            if not explanation_list:
                return None

            features = [item["feature"] for item in explanation_list]
            weights = [item["weight"] for item in explanation_list]

            colors = ["#2196F3" if w > 0 else "#F44336" for w in weights]

            fig, ax = plt.subplots(figsize=(10, max(4, len(features) * 0.5)))
            y_pos = range(len(features))
            ax.barh(list(y_pos), weights, color=colors, edgecolor="white")
            ax.set_yticks(list(y_pos))
            ax.set_yticklabels(features, fontsize=9)
            ax.axvline(x=0, color="black", linewidth=0.8, linestyle="--")
            ax.set_xlabel("LIME Weight")
            ax.set_title(
                f"LIME Explanation — Instance #{instance_idx} "
                f"(Predicted Class: {predicted_class})"
            )
            ax.invert_yaxis()
            plt.tight_layout()

            buf = BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight", dpi=120)
            plt.close(fig)
            buf.seek(0)
            return base64.b64encode(buf.read()).decode("utf-8")
        except Exception as exc:
            logger.warning("[LIME] plot generation failed: %s", exc)
            plt.close("all")
            return None

    def _get_predict_fn(self, model: Any):
        """Return a predict_proba callable, falling back to predict if needed."""
        if hasattr(model, "predict_proba"):
            return model.predict_proba
        elif hasattr(model, "predict"):
            # Wrap binary predict into pseudo-proba shape
            def _predict_proba(X: np.ndarray) -> np.ndarray:
                preds = model.predict(X).astype(float)
                return np.column_stack([1 - preds, preds])
            return _predict_proba
        raise AttributeError(f"Model {type(model)} has neither predict_proba nor predict.")
