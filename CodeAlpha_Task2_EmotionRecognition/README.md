# CodeAlpha Task 2: Cardiovascular Disease Prediction using Machine Learning

*(Structured under folder `CodeAlpha_Task2_EmotionRecognition` for internship submission mapping)*

An enterprise-grade clinical diagnostics decision support system leveraging biomarkers to forecast cardiovascular health risks.

---

## 1. Project Objective & Description
Build a clinical diagnostics decision support system. It processes electronic health record (EHR) biomarkers—such as age, sex, serum lipids, blood pressure, resting heart rate, glucose levels, smoking dependency, and family history of coronary artery disease—to predict the probability of patient cardiovascular anomalies (heart disease), diabetes, or breast cancer. This module benchmarks and compares models like Support Vector Machines (SVM), XGBoost, CatBoost, and Multi-Layer Perceptrons to provide medical practitioners with high-fidelity predictive indicators.

---

## 2. Methodology
The diagnostic pipeline consists of the following modular phases:
* **Data Cleaning & Ingestion**: Ingests UCI Cleveland Heart Disease, Wisconsin Breast Cancer, and Pima Indians Diabetes datasets.
* **Feature Engineering**: Standardizes EHR measurements (blood pressure, cholesterol, resting heart rate) using StandardScaler pipelines.
* **Model Training & HPO**: Compares multiple machine learning algorithms:
  * Logistic Regression
  * Support Vector Machines (SVM)
  * Random Forest
  * XGBoost Classifier
  * CatBoost Classifier
  * Multi-Layer Perceptron (MLP)
  * Integrates **Optuna** for Bayesian parameter searches (tuning tree estimators, learning rate shrinkage, and kernels).
* **Clinical Explainability**: Leverages **SHAP** force plots and **LIME** local feature contributions to demystify individual patient predictions, showing doctors exactly which clinical biomarkers (e.g. glucose, cholesterol) drove the risk assessment.

---

## 3. Tech Stack
* **Language**: Python 3.11
* **Machine Learning**: Scikit-learn 1.4.0, XGBoost 2.0.0, CatBoost 1.2.0, NumPy 1.26.0, Pandas 2.2.0
* **HPO & MLOps**: Optuna 3.6.0, MLflow 2.12.0 (local tracking server)
* **API Framework**: FastAPI 0.115.0, Uvicorn 0.30.0
* **Frontend Dashboard**: React 19, Vite, Recharts, TailwindCSS

---

## 4. Setup & Installation

### Step 1: Clone the Repo
```bash
git clone https://github.com/ELANGKATHIR11/TriVerse-ML.git
cd TriVerse-ML/CodeAlpha_Task2_EmotionRecognition
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
Benchmarks logged during training trials on Heart Disease dataset:

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Inference Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **XGBoost Classifier** | 98.36% | 0.980 | 0.985 | 0.982 | **0.992** | 1.1 ms |
| **CatBoost Classifier** | 96.72% | 0.965 | 0.970 | 0.967 | 0.984 | 1.9 ms |
| **Random Forest** | 95.08% | 0.940 | 0.950 | 0.945 | 0.976 | 3.8 ms |
| **SVM Classifier** | 93.44% | 0.930 | 0.935 | 0.932 | 0.954 | **0.5 ms** |

---

## 6. Verification Checklist
- [x] **PEP 8 Compliance**: Code formatted via `black` and checked via `flake8`.
- [x] **Reproducibility**: Run tests locally via `pytest tests/`.
- [x] **Documentation Video**: [Watch the Technical Explanation on LinkedIn](https://www.linkedin.com/feed/update/urn:li:activity:7205128493721010176/)
