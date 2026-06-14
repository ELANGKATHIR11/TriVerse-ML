@echo off
:: ============================================================
::  TriVerse AI — Main Launcher
::  Starts: MLflow + FastAPI Backend + Next.js Gateway + Electron
::  Conda Environment: dgpu-aiml
:: ============================================================

title TriVerse AI Launcher
set "PROJECT_ROOT=f:\TriVerse-ML-main\TriVerse-ML-main"
set "FRONTEND_DIR=%PROJECT_ROOT%\frontend\unified_dashboard"
set "BACKEND_DIR=%PROJECT_ROOT%\backend\unified_api"
set "CONDA_ENV=dgpu-aiml"

:: Activate conda properly in CMD
call "%USERPROFILE%\Miniconda3\Scripts\activate.bat" %CONDA_ENV%
if errorlevel 1 (
    call "%USERPROFILE%\anaconda3\Scripts\activate.bat" %CONDA_ENV%
)

:: Set models dir for inference service
set "TRIVERSE_MODELS_DIR=%BACKEND_DIR%\trained_models"
set "MLFLOW_TRACKING_URI=http://127.0.0.1:5000"

:: Electron handles all service spawning internally (MLflow, FastAPI, Gateway)
:: Just launch Electron from the frontend directory
cd /d "%FRONTEND_DIR%"
npx electron electron-main.cjs
