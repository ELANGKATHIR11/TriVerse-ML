@echo off
TITLE TriVerse ML Setup & Launcher
color 0A

echo ==========================================================
echo         TriVerse ML Native App Installer & Launcher
echo ==========================================================
echo.

:: 1. Check if Conda is installed
where conda >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] conda command not found!
    echo Please install Miniconda or Anaconda first:
    echo https://docs.anaconda.com/miniconda/
    echo.
    echo Press any key to open the Miniconda download page and exit...
    pause >nul
    start https://docs.anaconda.com/miniconda/
    exit /b
)

:: 2. Check if dgpu-core environment exists
echo Checking for conda environment 'dgpu-core'...
conda env list | findstr "dgpu-core" >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [INFO] Environment 'dgpu-core' not found. Creating it now...
    conda create -y -n dgpu-core python=3.11
    if %ERRORLEVEL% NEQ 0 (
        echo [ERROR] Failed to create conda environment!
        pause
        exit /b
    )
) else (
    echo [OK] Conda environment 'dgpu-core' detected.
)

:: 3. Install/Update python requirements
echo Installing/updating Python dependencies...
conda run -n dgpu-core pip install -r backend\unified_api\requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install Python requirements!
    pause
    exit /b
)

:: 4. Install/Update Node requirements
echo Installing/updating Node.js dependencies...
cd /d %~dp0frontend\unified_dashboard
call npm install
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to install Node requirements!
    pause
    exit /b
)
cd /d %~dp0

:: 5. Verify Ollama status
echo Checking Ollama local status...
curl -s http://localhost:11434/api/tags > nul 2>&1
if %ERRORLEVEL% EQU 0 (
    echo [OK] Ollama is online and active.
) else (
    echo [WARNING] Ollama is offline or not installed.
    echo The AI Assistant runs in fallback mode. To enable full LLM capabilities:
    echo 1. Download and run Ollama: https://ollama.com/
    echo 2. Run: ollama pull qwen2.5-coder:3b
    echo.
)

:: 5. Launch the Application
:: Check if the compiled Electron app exists
if exist "frontend\unified_dashboard\dist-electron\TriVerse ML-win32-x64\TriVerse ML.exe" (
    echo Launching native TriVerse ML app...
    start "" "frontend\unified_dashboard\dist-electron\TriVerse ML-win32-x64\TriVerse ML.exe"
) else (
    echo Packaged executable not found. Starting in development mode...
    cd frontend\unified_dashboard
    start npm run electron
)

echo.
echo Setup and launch sequence complete.
