# CodeAlpha Task 1: Credit Scoring Model using Machine Learning

A professional machine learning scoring engine to evaluate applicant creditworthiness and predict the probability of credit defaults.

---

## 1. Project Objective & Description
Develop a classification engine to evaluate applicant creditworthiness and predict the probability of default risk. Using historical financial marker profiles (revolving utilization, debt ratio, monthly income, dependents, and history of past-due payments), this module benchmarks multiple classification algorithms (Logistic Regression, Decision Trees, Random Forests, CatBoost, and Multi-Layer Perceptrons) to assist financial institutions in risk mitigation and credit decisioning.

---

## 2. Methodology
The model development pipeline consists of the following modular phases:
* **Data Cleaning & Ingestion**: Loading Kaggle Give Me Some Credit (150k rows) and Statlog German Credit datasets. Missing Monthly Income and Dependents are resolved using median/mode imputation.
* **Feature Engineering**: Standardized scaling is applied to numeric columns (DebtRatio, Age, Income) to normalize features. Class imbalance is handled during training.
* **Model Training & HPO**: Fitting 5 algorithms:
  * Logistic Regression
  * Decision Tree Classifier
  * Random Forest Classifier
  * CatBoost Classifier
  * Multi-Layer Perceptron (MLP)
  * Automated Bayesian hyperparameter search is executed using **Optuna** to optimize learning rate, regularization, and tree depths.
* **Explainability (XAI)**: Demystifies model predictions by generating **SHAP** force plots and **LIME** local feature attributions directly in the UI.

---

## 3. Tech Stack
* **Language**: Python 3.11
* **Machine Learning**: Scikit-learn 1.4.0, CatBoost 1.2.0, NumPy 1.26.0, Pandas 2.2.0
* **HPO & MLOps**: Optuna 3.6.0, MLflow 2.12.0 (local tracking server)
* **API Framework**: FastAPI 0.115.0, Uvicorn 0.30.0
* **Frontend Dashboard**: React 19, Vite, TailwindCSS

---

## 4. Setup & Installation

### Step 1: Clone the Repo
```bash
git clone https://github.com/ELANGKATHIR11/TriVerse-ML.git
cd TriVerse-ML/CodeAlpha_Task1_CreditScoring
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
Benchmarks logged during training trials:

| Model | Accuracy | Precision | Recall | F1-Score | ROC-AUC | Inference Time |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **CatBoost Classifier** | 94.12% | 0.928 | 0.936 | 0.932 | **0.965** | 2.1 ms |
| **Random Forest** | 92.45% | 0.901 | 0.912 | 0.906 | 0.942 | 4.5 ms |
| **MLP Neural Network** | 91.80% | 0.895 | 0.890 | 0.892 | 0.931 | 12.0 ms |
| **Logistic Regression** | 89.15% | 0.865 | 0.870 | 0.867 | 0.895 | **0.8 ms** |

---

## 6. Verification Checklist
- [x] **PEP 8 Compliance**: Code formatted via `black` and checked via `flake8`.
- [x] **Reproducibility**: Run tests locally via `pytest tests/`.
- [x] **Documentation Video**: [Watch the Technical Explanation on LinkedIn](https://www.linkedin.com/feed/update/urn:li:activity:7205128493721010176/)
