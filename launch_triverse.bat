@echo off
:: ============================================================
::  TriVerse AI — Main Launcher
::  Uses local electron binary (no npx/conda PATH needed)
:: ============================================================

set "FRONTEND_DIR=f:\TriVerse-ML-main\TriVerse-ML-main\frontend\unified_dashboard"
set "ELECTRON_BIN=%FRONTEND_DIR%\node_modules\.bin\electron.cmd"
set "ENTRY=%FRONTEND_DIR%\electron-main.cjs"

cd /d "%FRONTEND_DIR%"

:: Use the locally installed electron binary
if exist "%ELECTRON_BIN%" (
    "%ELECTRON_BIN%" "%ENTRY%"
) else (
    :: Fallback: try node_modules electron directly
    set "ELECTRON_EXE=%FRONTEND_DIR%\node_modules\electron\dist\electron.exe"
    if exist "%ELECTRON_EXE%" (
        "%ELECTRON_EXE%" "%ENTRY%"
    ) else (
        echo [ERROR] Electron not found. Run: cd frontend\unified_dashboard ^&^& npm install
        pause
    )
)
