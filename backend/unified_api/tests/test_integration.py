import os
import subprocess
import time
import httpx
import pytest
import sqlite3
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
DB_FILE = BASE_DIR / "test_codealpha.db"
DB_URL = f"sqlite+aiosqlite:///{DB_FILE.as_posix()}"

@pytest.fixture(scope="module")
def run_servers():
    # Remove existing test db
    for suffix in ["", "-wal", "-shm"]:
        p = Path(str(DB_FILE) + suffix)
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    # Start backend
    backend_env = os.environ.copy()
    backend_env["DATABASE_URL"] = DB_URL
    
    # Use the same python executable running pytest
    python_exe = os.sys.executable
    
    backend_proc = subprocess.Popen(
        [python_exe, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        cwd=str(BASE_DIR),
        env=backend_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for backend to be healthy
    backend_ready = False
    for _ in range(30):
        try:
            resp = httpx.get("http://127.0.0.1:8000/health", timeout=1.0)
            if resp.status_code == 200:
                backend_ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)
        
    if not backend_ready:
        backend_proc.terminate()
        stdout, stderr = backend_proc.communicate()
        raise RuntimeWarning(f"Backend failed to start. Stdout:\n{stdout}\nStderr:\n{stderr}")

    # Start frontend Express server
    frontend_dir = BASE_DIR.parent.parent / "frontend" / "unified_dashboard"
    frontend_env = os.environ.copy()
    
    # Run server.ts using tsx (we can run it with npx tsx server.ts)
    # On Windows, we use shell=True
    frontend_proc = subprocess.Popen(
        "npx tsx server.ts",
        cwd=str(frontend_dir),
        env=frontend_env,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for frontend to be healthy
    frontend_ready = False
    for _ in range(30):
        try:
            resp = httpx.get("http://127.0.0.1:3000/api/health", timeout=1.0)
            if resp.status_code == 200:
                frontend_ready = True
                break
        except Exception:
            pass
        time.sleep(0.5)
        
    if not frontend_ready:
        backend_proc.terminate()
        frontend_proc.terminate()
        raise RuntimeWarning("Frontend failed to start.")

    yield

    # Shutdown backend and frontend
    backend_proc.terminate()
    backend_proc.wait()
    
    # Since we ran frontend on Windows with shell=True, we might need taskkill or just terminating the process group
    if os.name == 'nt':
        subprocess.run(f"taskkill /F /T /PID {frontend_proc.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        frontend_proc.terminate()
        frontend_proc.wait()

    # Clean up test database
    for suffix in ["", "-wal", "-shm"]:
        p = Path(str(DB_FILE) + suffix)
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass


@pytest.mark.integration
def test_frontend_backend_integration(run_servers):
    # Test 1: Query Frontend Direct Endpoint
    resp = httpx.get("http://127.0.0.1:3000/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

    # Test 2: Perform Login via Frontend Proxy to Backend
    login_resp = httpx.post(
        "http://127.0.0.1:3000/api/auth/login",
        data={"username": "admin", "password": "admin123"}
    )
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    token_data = login_resp.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Test 3: Retrieve Users via Frontend Proxy with JWT Auth
    headers = {"Authorization": f"Bearer {token}"}
    users_resp = httpx.get("http://127.0.0.1:3000/api/users", headers=headers)
    assert users_resp.status_code == 200
    users_data = users_resp.json()
    assert "users" in users_data
    assert users_data["total"] >= 1
    
    # Verify the admin user exists in the returned list
    usernames = [u["username"] for u in users_data["users"]]
    assert "admin" in usernames

    # Test 4: Verify Database State directly using sqlite3
    db_conn = sqlite3.connect(DB_FILE)
    cursor = db_conn.cursor()
    cursor.execute("SELECT username, email, role FROM users WHERE username = 'admin'")
    row = cursor.fetchone()
    db_conn.close()
    
    assert row is not None
    assert row[0] == "admin"
    assert row[1] == "admin@codealpha.ai"
    assert row[2].upper() == "ADMIN"
