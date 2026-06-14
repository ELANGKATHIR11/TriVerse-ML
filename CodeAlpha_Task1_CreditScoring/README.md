# CodeAlpha Task 1: Credit Scoring Model

## Project Objective
Develop a professional machine learning scoring engine to evaluate applicant creditworthiness and predict the probability of credit defaults (default risk). Using historical financial marker profiles (revolving utilization, debt ratio, monthly income, dependents, and history of past-due payments), this module benchmarks multiple classification algorithms (Logistic Regression, Decision Trees, Random Forests, CatBoost, and Multi-Layer Perceptrons) to assist financial institutions in risk mitigation and credit decisioning.

## Technologies Used
- **Machine Learning**: Scikit-learn, CatBoost, NumPy, Pandas.
- **HPO & MLOps**: Optuna (Bayesian parameter sweeps), MLflow (experiment and run logging).
- **Explainability (XAI)**: SHAP (Shapley Additive exPlanations) and LIME.
- **Backend Service**: FastAPI (Python), Uvicorn.
- **Frontend Dashboard**: React, Vite, TailwindCSS, Lucide-react.

## Folder Structure
- `backend/`: Python FastAPI source code, endpoints, database schemas, and model definitions.
- `datasets/`: Kaggle Give Me Some Credit (primary) and German Credit (secondary) datasets.
- `frontend/`: React components, hooks, UI controls, and models comparison dashboard.
- `screenshots/`: Task execution and evaluation interface screenshots.
- `report.pdf`: Comprehensive Task 1 report and benchmark analysis.
- `architecture.png`: Module architectural design schematic.

## How to Run

### 1. Backend Service
1. Navigate to the backend directory:
   ```bash
   cd CodeAlpha_Task1_CreditScoring/backend
   ```
2. Activate your conda environment (e.g. `dgpu-aiml`):
   ```bash
   conda activate dgpu-aiml
   ```
3. Run the uvicorn API portal:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### 2. Frontend Interface
1. Navigate to the frontend directory in a separate terminal:
   ```bash
   cd CodeAlpha_Task1_CreditScoring/frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Launch the development server:
   ```bash
   npm run dev
   ```
4. Access the task portal in your browser at `http://localhost:3000`.
