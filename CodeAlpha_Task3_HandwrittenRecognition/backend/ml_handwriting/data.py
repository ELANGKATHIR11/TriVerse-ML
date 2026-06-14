"""
Handwriting Recognition Data Loaders
Supports MNIST (10 classes) and EMNIST Balanced (47 classes).
Data is normalized to [0, 1] and reshaped for both Keras (NHWC) and PyTorch (NCHW).
"""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

EMNIST_DIR = Path(__file__).resolve().parent.parent.parent / "datasets" / "handwriting" / "emnist"
MNIST_DIR = Path(__file__).resolve().parent.parent.parent / "datasets" / "handwriting" / "mnist"

# EMNIST Balanced class map: digits 0-9 then uppercase A-Z then selected lowercase
_EMNIST_BALANCED_CLASSES: list[str] = [
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
    "A", "B", "C", "D", "E", "F", "G", "H", "I", "J",
    "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T",
    "U", "V", "W", "X", "Y", "Z",
    "a", "b", "d", "e", "f", "g", "h", "n", "q", "r", "t",
]  # 47 classes total


class HandwritingDataLoader:
    """Loads MNIST and EMNIST datasets, returning normalised NumPy arrays."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_mnist(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
        """Load MNIST digits dataset.

        Returns
        -------
        (X_train, X_test, y_train, y_test, class_names)
        X arrays have shape (N, 28, 28, 1) dtype float32, values in [0, 1].
        y arrays have shape (N,) dtype int64.
        class_names is a list of 10 string labels ("0" … "9").
        """
        logger.info("Loading MNIST dataset …")
        try:
            from tensorflow.keras.datasets import mnist  # type: ignore[import]

            MNIST_DIR.mkdir(parents=True, exist_ok=True)
            (x_train, y_train), (x_test, y_test) = mnist.load_data()
        except Exception as exc:
            logger.error("Failed to load MNIST via Keras: %s", exc)
            raise RuntimeError(f"MNIST load failed: {exc}") from exc

        x_train, x_test = self._normalise_keras(x_train), self._normalise_keras(x_test)
        y_train, y_test = y_train.astype(np.int64), y_test.astype(np.int64)
        class_names = [str(i) for i in range(10)]

        logger.info(
            "MNIST loaded: train=%d  test=%d  classes=%d",
            len(x_train),
            len(x_test),
            len(class_names),
        )
        return x_train, x_test, y_train, y_test, class_names

    def load_emnist(self) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
        """Load EMNIST Balanced dataset (47 classes).

        Returns
        -------
        (X_train, X_test, y_train, y_test, class_names)
        X arrays have shape (N, 28, 28, 1) dtype float32, values in [0, 1].
        y arrays have shape (N,) dtype int64.
        class_names is a list of 47 string labels.
        Falls back to MNIST if EMNIST is unavailable.
        """
        logger.info("Loading EMNIST Balanced dataset …")
        try:
            return self._load_emnist_torchvision()
        except Exception as exc:
            logger.warning(
                "EMNIST load failed (%s); falling back to MNIST (10 classes).", exc
            )
            return self.load_mnist()

    def get_sample_images(
        self,
        X: np.ndarray,
        y: np.ndarray,
        class_names: list[str] | None = None,
        n: int = 16,
    ) -> list[dict[str, str]]:
        """Return n random samples as base-64 PNG strings with labels.

        Parameters
        ----------
        X : ndarray of shape (N, 28, 28, 1) or (N, 1, 28, 28), float32
        y : ndarray of shape (N,), int64
        class_names : optional list mapping label index -> string
        n : number of samples to return

        Returns
        -------
        List of dicts  {"image_b64": <str>, "label": <str>}
        """
        try:
            from PIL import Image  # type: ignore[import]
        except ImportError:
            Image = None  # type: ignore[assignment]

        indices = np.random.choice(len(X), size=min(n, len(X)), replace=False)
        results: list[dict[str, str]] = []

        for idx in indices:
            img_array = X[idx]

            # Normalise shape to (28, 28)
            if img_array.ndim == 3:
                if img_array.shape[0] == 1:  # NCHW -> HW
                    img_array = img_array[0]
                else:  # HWC -> HW
                    img_array = img_array[:, :, 0]

            # Scale to uint8
            img_uint8 = (img_array * 255).clip(0, 255).astype(np.uint8)

            # Encode to base64 PNG
            b64 = self._array_to_b64_png(img_uint8, Image)

            label_idx = int(y[idx])
            label = (
                class_names[label_idx]
                if class_names is not None and label_idx < len(class_names)
                else str(label_idx)
            )
            results.append({"image_b64": b64, "label": label})

        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_emnist_torchvision(
        self,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list[str]]:
        """Load EMNIST Balanced using torchvision."""
        import torch  # type: ignore[import]
        import torchvision  # type: ignore[import]
        import torchvision.transforms as transforms  # type: ignore[import]

        EMNIST_DIR.mkdir(parents=True, exist_ok=True)
        root = str(EMNIST_DIR.parent)

        transform = transforms.Compose([transforms.ToTensor()])

        train_ds = torchvision.datasets.EMNIST(
            root=root,
            split="balanced",
            train=True,
            download=True,
            transform=transform,
        )
        test_ds = torchvision.datasets.EMNIST(
            root=root,
            split="balanced",
            train=False,
            download=True,
            transform=transform,
        )

        x_train, y_train = self._torchvision_ds_to_numpy(train_ds)
        x_test, y_test = self._torchvision_ds_to_numpy(test_ds)

        # EMNIST images from torchvision are transposed; fix orientation
        x_train = np.transpose(x_train, (0, 2, 3, 1))  # NCHW -> NHWC
        x_test = np.transpose(x_test, (0, 2, 3, 1))

        # Apply the canonical EMNIST transpose (images are stored sideways)
        x_train = np.transpose(x_train, (0, 2, 1, 3))
        x_test = np.transpose(x_test, (0, 2, 1, 3))

        class_names = _EMNIST_BALANCED_CLASSES
        logger.info(
            "EMNIST Balanced loaded: train=%d  test=%d  classes=%d",
            len(x_train),
            len(x_test),
            len(class_names),
        )
        return x_train, x_test, y_train, y_test, class_names

    @staticmethod
    def _torchvision_ds_to_numpy(
        dataset: Any,
    ) -> tuple[np.ndarray, np.ndarray]:
        """Extract tensors from a torchvision dataset into float32 numpy arrays."""
        import torch  # type: ignore[import]
        from torch.utils.data import DataLoader  # type: ignore[import]

        loader = DataLoader(dataset, batch_size=8192, shuffle=False, num_workers=0)
        xs, ys = [], []
        for x_batch, y_batch in loader:
            xs.append(x_batch.numpy().astype(np.float32))
            ys.append(y_batch.numpy().astype(np.int64))

        x_all = np.concatenate(xs, axis=0)  # (N, 1, 28, 28)
        y_all = np.concatenate(ys, axis=0)  # (N,)
        return x_all, y_all

    @staticmethod
    def _normalise_keras(x: np.ndarray) -> np.ndarray:
        """Normalise uint8 image array to float32 [0, 1] with NHWC shape."""
        x = x.astype(np.float32) / 255.0
        if x.ndim == 3:  # (N, H, W) -> (N, H, W, 1)
            x = x[..., np.newaxis]
        return x

    @staticmethod
    def _array_to_b64_png(img_uint8: np.ndarray, Image: Any) -> str:
        """Encode a 2-D uint8 array to a base64-encoded PNG string."""
        buf = io.BytesIO()
        if Image is not None:
            pil_img = Image.fromarray(img_uint8, mode="L")
            pil_img.save(buf, format="PNG")
        else:
            # Minimal fallback: raw bytes as base64 (consumers must handle)
            buf.write(img_uint8.tobytes())
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
