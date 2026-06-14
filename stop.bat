@echo off
echo Stopping all CodeAlpha platform services...
taskkill /FI "WINDOWTITLE eq MLflow Server*" /F > nul 2>&1
taskkill /FI "WINDOWTITLE eq FastAPI Backend*" /F > nul 2>&1
taskkill /FI "WINDOWTITLE eq Next.js Frontend*" /F > nul 2>&1
echo All services stopped.
