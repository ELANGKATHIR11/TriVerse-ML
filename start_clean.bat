@echo off
SET CONDA_ENV=dgpu-core
SET PROJECT_DIR=%~dp0
SET BACKEND_DIR=%PROJECT_DIR%backend\unified_api
SET FRONTEND_DIR=%PROJECT_DIR%frontend\unified_dashboard
SET MLRUNS_DIR=%PROJECT_DIR%mlruns

echo Starting MLflow...
start "MLflow Server" cmd /k "conda activate %CONDA_ENV% && mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///%PROJECT_DIR%mlruns/mlflow.db --default-artifact-root %MLRUNS_DIR%"

echo Starting Backend...
start "FastAPI Backend" cmd /k "conda activate %CONDA_ENV% && cd /d %BACKEND_DIR% && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info"

echo Starting Frontend...
start "Next.js Frontend" cmd /k "cd /d %FRONTEND_DIR% && npm run dev"

echo Services started!
