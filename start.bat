@echo off
TITLE TriVerse ML Platform
color 0B
echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                     TriVerse ML Platform                     ║
echo  ║                   Starting All Services...                   ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

SET CONDA_ENV=dgpu-core
SET PROJECT_DIR=%~dp0
SET BACKEND_DIR=%PROJECT_DIR%backend\unified_api
SET FRONTEND_DIR=%PROJECT_DIR%frontend\unified_dashboard
SET MLRUNS_DIR=%PROJECT_DIR%mlruns

echo [1/4] Starting MLflow Tracking Server on port 5000...
start "MLflow Server" cmd /k "conda activate %CONDA_ENV% && mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri sqlite:///%PROJECT_DIR%mlruns/mlflow.db --default-artifact-root %MLRUNS_DIR%"
timeout /t 3 /nobreak > nul

echo [2/4] Starting FastAPI Backend on port 8000...
start "FastAPI Backend" cmd /k "conda activate %CONDA_ENV% && cd /d %BACKEND_DIR% && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload --log-level info"
timeout /t 3 /nobreak > nul

echo [3/4] Checking Ollama status...
curl -s http://localhost:11434/api/tags > nul 2>&1
IF %ERRORLEVEL% EQU 0 (
    echo      [OK] Ollama is running
) ELSE (
    echo      [WARNING] Ollama not detected. AI Assistant will use fallback mode.
    echo      To enable full AI features, run: ollama serve
    echo      Then pull a model: ollama pull qwen2.5:7b
)
timeout /t 2 /nobreak > nul

echo [4/4] Starting Next.js Frontend on port 3000...
start "Next.js Frontend" cmd /k "cd /d %FRONTEND_DIR% && npm run dev"
timeout /t 5 /nobreak > nul

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                    ALL SERVICES STARTED                      ║
echo  ║                                                              ║
echo  ║  Frontend:  http://localhost:3000                            ║
echo  ║  Backend:   http://localhost:8000                            ║
echo  ║  API Docs:  http://localhost:8000/docs                       ║
echo  ║  MLflow:    http://localhost:5000                            ║
echo  ║                                                              ║
echo  ║  Default Login: admin / admin123                             ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.
echo Opening the platform in your browser in 3 seconds...
timeout /t 3 > nul
start http://localhost:3000
