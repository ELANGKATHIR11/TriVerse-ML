Set WshShell = CreateObject("WScript.Shell")

' 1. Start Ollama if not running
WshShell.Run "cmd /c netstat -ano | findstr :11434 || start /b ollama serve", 0, False

' 2. Start MLflow tracking server
WshShell.Run "cmd /c conda activate dgpu-aiml && mlflow server --host 0.0.0.0 --port 5000 --backend-store-uri ""sqlite:///F:/TriVerse ML/mlruns/mlflow.db"" --default-artifact-root ""F:/TriVerse ML/mlruns""", 0, False

' 3. Start FastAPI backend
WshShell.Run "cmd /c cd /d ""F:\TriVerse ML\backend\unified_api"" && conda activate dgpu-aiml && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000", 0, False

' 4. Start Next.js/Vite frontend dev server
WshShell.Run "cmd /c cd /d ""F:\TriVerse ML\frontend\unified_dashboard"" && npm run dev", 0, False

' 5. Wait 6 seconds for startup, then launch as a standalone desktop app using Electron
WScript.Sleep 6000
WshShell.Run "cmd /c cd /d ""F:\TriVerse ML\frontend\unified_dashboard"" && npm run electron", 0, False
