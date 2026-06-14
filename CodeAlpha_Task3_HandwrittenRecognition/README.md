# CodeAlpha Task 3: Handwritten Character Recognition using Deep Learning

An enterprise-grade computer vision classification module designed to recognize handwritten characters from dynamic drawings or uploaded image files.

---

## 1. Project Objective & Description
Implement high-performance deep learning visual classification models to recognize handwritten characters from images. The application processes user sketches on a dynamic canvas or uploaded files, resizes and normalizes them, and runs them through either a custom Convolutional Neural Network (CNN) built in TensorFlow/Keras or a modified ResNet18 model built in PyTorch (GPU accelerated). It supports digits from the MNIST dataset and balanced character layouts from the EMNIST dataset (47 classes).

---

## 2. Methodology
The vision pipeline consists of the following modular phases:
* **Canvas Drawing / Ingestion**: User draws a character on an interactive HTML5 Canvas. The canvas outputs a high-resolution base64 data URL.
* **Pre-processing**:
  * Decodes the base64 string into raw binary image buffers.
  * Resizes the image to 28x28 grayscale using `Pillow`.
  * Normalizes pixel intensities to the range `[0, 1]` and converts to float32.
  * Reshapes values to matching channel formats: channel-last `(1, 28, 28, 1)` for Keras, and channel-first `(1, 1, 28, 28)` for PyTorch.
* **Model Inference**:
  * **Custom CNN (Keras)**: Lightweight 2D Convolution layers, MaxPooling, Dropout, and a Dense Softmax classifier.
  * **ResNet18 (PyTorch)**: A modified ResNet18 backbone with a single input channel, trained with GPU CUDA acceleration.
* **Optimization & Telemetry**: Fits hyperparameters (e.g. learning rate, dropout coefficients) using Optuna, logging parameter convergence to MLflow.

---

## 3. Tech Stack
* **Language**: Python 3.11
* **Deep Learning Frameworks**: PyTorch 2.2.0, TensorFlow/Keras 2.15.0, Pillow 10.3.0, NumPy 1.26.0
* **HPO & MLOps**: Optuna 3.6.0, MLflow 2.12.0 (local tracking server)
* **API Framework**: FastAPI 0.115.0, Uvicorn 0.30.0
* **Frontend Dashboard**: React 19, Vite, HTML5 Canvas API, TailwindCSS

---

## 4. Setup & Installation

### Step 1: Clone the Repo
```bash
git clone https://github.com/ELANGKATHIR11/TriVerse-ML.git
cd TriVerse-ML/CodeAlpha_Task3_HandwrittenRecognition
```

### Step 2: Install Dependencies
Create/activate your environment and install Python packages:
```bash
pip install -r requirements.txt
```

### Step 3: Run the Application
You can run the global startup scripts or launch individual parts:
```bash
# Navigate to the source folder
cd src/backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

---

## 5. Model Performance Comparison
Benchmarks logged during training trials on MNIST dataset:

| Model | Test Accuracy | Categorical Cross-Entropy Loss | Optimizer | Epochs | Training Time | GPU Memory |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **ResNet18 (PyTorch)** | **99.45%** | 0.015 | AdamW | 10 | 18 min | ~1.2 GB |
| **Custom CNN (Keras)** | 98.40% | 0.045 | Adam | 8 | 6 min | ~0.8 GB |

---

## 6. Verification Checklist
- [x] **PEP 8 Compliance**: Code formatted via `black` and checked via `flake8`.
- [x] **Reproducibility**: Run tests locally via `pytest tests/`.
- [x] **Documentation Video**: [Watch the Technical Explanation on LinkedIn](https://www.linkedin.com/feed/update/urn:li:activity:7205128493721010176/)
