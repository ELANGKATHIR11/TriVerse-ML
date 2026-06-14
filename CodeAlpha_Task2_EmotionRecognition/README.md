# CodeAlpha Task 2: Disease Prediction & Clinical Diagnostics

*(Note: Structured under folder `CodeAlpha_Task2_EmotionRecognition` for internship submission mapping)*

## Project Objective
Build an enterprise-grade clinical diagnostics decision support system. It processes electronic health record (EHR) biomarkers—such as biological age, sex, serum lipids, blood pressure, resting heart rate, glucose levels, smoking dependency, and family history of coronary artery disease—to predict the probability of patient cardiovascular anomalies (heart disease), diabetes, or breast cancer. This module benchmarks and compares models like Support Vector Machines (SVM), XGBoost, CatBoost, and Multi-Layer Perceptrons to provide medical practitioners with high-fidelity predictive indicators.

## Technologies Used
- **Machine Learning**: Scikit-learn, XGBoost, CatBoost, NumPy, Pandas.
- **HPO & MLOps**: Optuna, MLflow.
- **Backend Service**: FastAPI (Python), Uvicorn.
- **Frontend Dashboard**: React, Vite, Recharts, TailwindCSS.

## Folder Structure
- `backend/`: FastAPI Python application with endpoint handlers, database storage, and model trainers.
- `datasets/`: UCI Cleveland Heart Disease, Pima Indians Diabetes, and Wisconsin Breast Cancer datasets.
- `frontend/`: React components, charts, patient entry forms, and care recommendation sheets.
- `screenshots/`: Task execution and evaluation interface screenshots.
- `report.pdf`: Comprehensive Task 2 report and clinical benchmark analysis.
- `architecture.png`: Module architectural layout schematic.

## How to Run

### 1. Backend Service
1. Navigate to the backend directory:
   ```bash
   cd CodeAlpha_Task2_EmotionRecognition/backend
   ```
2. Activate your conda environment (e.g. `dgpu-aiml`):
   ```bash
   conda activate dgpu-aiml
   ```
3. Run the uvicorn API:
   ```bash
   python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

### 2. Frontend Interface
1. Navigate to the frontend directory in a separate terminal:
   ```bash
   cd CodeAlpha_Task2_EmotionRecognition/frontend
   ```
2. Install npm dependencies:
   ```bash
   npm install
   ```
3. Launch the development server:
   ```bash
   npm run dev
   ```
4. Access the diagnostic console at `http://localhost:3000`.
