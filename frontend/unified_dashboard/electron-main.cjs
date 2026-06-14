/**
 * electron-main.cjs — TriVerse AI Desktop Orchestrator
 *
 * Boot sequence:
 *   1. Show splash screen immediately
 *   2. Spawn MLflow tracking server (conda dgpu-aiml)
 *   3. Spawn FastAPI backend (conda dgpu-aiml)
 *   4. Poll FastAPI /health/live until ready (max 120 s)
 *   5. Spawn Express / tsx gateway (port 3000)
 *   6. Poll gateway until ready (max 60 s)
 *   7. Close splash → open main window
 *
 * Shutdown:
 *   - window-all-closed → taskkill all child processes cleanly
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');
const http = require('http');

let childProcesses = [];
let splashWindow = null;
let mainWindow = null;

// ── Project root discovery ────────────────────────────────────────────────────
function getProjectRoot() {
  let current = path.resolve(__dirname);
  for (let i = 0; i < 6; i++) {
    if (fs.existsSync(path.join(current, 'backend')) &&
        fs.existsSync(path.join(current, 'frontend'))) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return path.resolve(__dirname);
}

const root = getProjectRoot();
const backendDir = path.join(root, 'backend', 'unified_api');
const frontendDir = path.join(root, 'frontend', 'unified_dashboard');
const trainedModelsDir = path.join(backendDir, 'trained_models');
const mlrunsDir = path.join(backendDir, 'mlruns');
const condaEnv = 'dgpu-aiml';

// ── Health poll helper ────────────────────────────────────────────────────────
/**
 * Poll a local URL until it responds with HTTP < 500.
 * @param {string} url  — full URL to GET
 * @param {number} maxMs — maximum wait in milliseconds
 * @param {number} intervalMs — poll interval
 * @returns {Promise<boolean>}
 */
function pollUntilReady(url, maxMs = 120_000, intervalMs = 1_000) {
  return new Promise((resolve) => {
    const start = Date.now();
    function attempt() {
      http.get(url, (res) => {
        if (res.statusCode < 500) {
          resolve(true);
        } else {
          retry();
        }
      }).on('error', retry);
    }
    function retry() {
      if (Date.now() - start > maxMs) {
        resolve(false);
      } else {
        setTimeout(attempt, intervalMs);
      }
    }
    attempt();
  });
}

// ── Splash screen ─────────────────────────────────────────────────────────────
function createSplash() {
  splashWindow = new BrowserWindow({
    width: 520,
    height: 340,
    frame: false,
    alwaysOnTop: true,
    transparent: false,
    resizable: false,
    icon: path.join(__dirname, 'app_icon.ico'),
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
    },
  });

  // Write splash HTML inline so no extra file is needed
  const splashHtml = `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    color: #e0e0ff;
    font-family: 'Segoe UI', sans-serif;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    height: 100vh; overflow: hidden;
    user-select: none;
  }
  .logo { font-size: 2.4rem; font-weight: 700; letter-spacing: 2px;
          background: linear-gradient(90deg, #a855f7, #6366f1);
          -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .sub  { font-size: 0.85rem; opacity: 0.6; margin-top: 4px; }
  .status { margin-top: 32px; font-size: 0.82rem; opacity: 0.8;
            min-height: 1.4em; text-align: center; padding: 0 24px; }
  .bar-track { width: 320px; height: 4px; background: rgba(255,255,255,0.1);
               border-radius: 2px; margin-top: 14px; overflow: hidden; }
  .bar-fill  { height: 100%; width: 0%;
               background: linear-gradient(90deg, #a855f7, #6366f1);
               border-radius: 2px;
               transition: width 0.4s ease; }
  .version { position: absolute; bottom: 14px; font-size: 0.72rem; opacity: 0.35; }
</style>
</head>
<body>
  <div class="logo">TriVerse AI</div>
  <div class="sub">Production ML Platform</div>
  <div class="status" id="status">Initializing services…</div>
  <div class="bar-track"><div class="bar-fill" id="bar"></div></div>
  <div class="version">v2.0.0 · dgpu-aiml</div>
  <script>
    const { ipcRenderer } = require('electron');
    ipcRenderer.on('splash-status', (_, msg) => {
      document.getElementById('status').textContent = msg.text;
      document.getElementById('bar').style.width = msg.pct + '%';
    });
  </script>
</body>
</html>`;

  const splashPath = path.join(__dirname, '_splash.html');
  fs.writeFileSync(splashPath, splashHtml, 'utf8');
  splashWindow.loadFile(splashPath);
}

function setSplashStatus(text, pct) {
  if (splashWindow && !splashWindow.isDestroyed()) {
    splashWindow.webContents.send('splash-status', { text, pct });
  }
  console.log(`[Boot] (${pct}%) ${text}`);
}

// ── Spawn a child process with logging ────────────────────────────────────────
function spawnService(label, cmd, args, opts) {
  const proc = spawn(cmd, args, { shell: true, ...opts });
  proc.stdout.on('data', d => console.log(`[${label}] ${d.toString().trim()}`));
  proc.stderr.on('data', d => console.error(`[${label}] ${d.toString().trim()}`));
  proc.on('exit', (code) => console.log(`[${label}] exited with code ${code}`));
  childProcesses.push(proc);
  return proc;
}

// ── Main boot sequence ────────────────────────────────────────────────────────
async function startServices() {
  // Ensure directories exist
  fs.mkdirSync(mlrunsDir, { recursive: true });
  fs.mkdirSync(trainedModelsDir, { recursive: true });

  setSplashStatus('Starting MLflow tracking server…', 10);
  spawnService('MLflow', 'conda', [
    'run', '-n', condaEnv,
    'mlflow', 'server',
    '--host', '127.0.0.1',
    '--port', '5000',
    '--backend-store-uri', `sqlite:///${path.join(mlrunsDir, 'mlflow.db')}`,
    '--default-artifact-root', mlrunsDir,
  ], { cwd: root });

  // Give MLflow a head-start (it's not a hard dependency for initial load)
  await new Promise(r => setTimeout(r, 1500));

  setSplashStatus('Starting FastAPI backend…', 25);
  const envVars = {
    ...process.env,
    TRIVERSE_MODELS_DIR: trainedModelsDir,
    MLFLOW_TRACKING_URI: 'http://127.0.0.1:5000',
  };
  spawnService('FastAPI', 'conda', [
    'run', '-n', condaEnv,
    'python', '-m', 'uvicorn', 'app.main:app',
    '--host', '127.0.0.1',
    '--port', '8000',
    '--log-level', 'warning',
  ], { cwd: backendDir, env: envVars });

  setSplashStatus('Waiting for backend to be ready…', 40);
  const backendReady = await pollUntilReady('http://127.0.0.1:8000/health/live', 120_000);
  if (!backendReady) {
    setSplashStatus('⚠ Backend timeout — continuing anyway…', 55);
    await new Promise(r => setTimeout(r, 2000));
  } else {
    setSplashStatus('Backend ready ✓', 55);
  }

  setSplashStatus('Starting UI gateway…', 65);
  const distServerPath = path.join(frontendDir, 'dist', 'server.cjs');
  if (fs.existsSync(distServerPath)) {
    spawnService('Gateway', 'node', [distServerPath], {
      cwd: frontendDir,
      env: { ...process.env, NODE_ENV: 'production' },
    });
  } else {
    spawnService('Gateway', 'npx', ['tsx', 'server.ts'], {
      cwd: frontendDir,
      env: { ...process.env, NODE_ENV: 'development' },
    });
  }

  setSplashStatus('Waiting for UI gateway…', 78);
  const gatewayReady = await pollUntilReady('http://localhost:3000', 60_000);
  if (!gatewayReady) {
    setSplashStatus('⚠ Gateway timeout — opening anyway…', 90);
    await new Promise(r => setTimeout(r, 1500));
  } else {
    setSplashStatus('All systems online ✓  — launching…', 95);
    await new Promise(r => setTimeout(r, 600));
  }
}

// ── Main window ────────────────────────────────────────────────────────────────
function createMainWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    title: 'TriVerse AI',
    icon: path.join(__dirname, 'app_icon.ico'),
    show: false,   // shown after splash closes
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  mainWindow.setMenuBarVisibility(false);

  const loadWithRetry = () => {
    mainWindow.loadURL('http://localhost:3000').catch(() => {
      console.log('[Electron] Retrying UI load in 500 ms…');
      setTimeout(loadWithRetry, 500);
    });
  };
  loadWithRetry();

  mainWindow.once('ready-to-show', () => {
    if (splashWindow && !splashWindow.isDestroyed()) {
      splashWindow.close();
    }
    mainWindow.show();
  });
}

// ── Shutdown ──────────────────────────────────────────────────────────────────
function stopServices() {
  console.log('[Electron] Shutting down all services…');
  for (const proc of childProcesses) {
    try {
      if (process.platform === 'win32') {
        spawn('taskkill', ['/pid', String(proc.pid), '/f', '/t'], { shell: true });
      } else {
        proc.kill('SIGTERM');
      }
    } catch (e) {
      console.error('[Electron] Kill error:', e.message);
    }
  }
  childProcesses = [];
  // Clean up temp splash file
  try {
    const sp = path.join(__dirname, '_splash.html');
    if (fs.existsSync(sp)) fs.unlinkSync(sp);
  } catch (_) {}
}

// ── Entry point ───────────────────────────────────────────────────────────────
app.whenReady().then(async () => {
  createSplash();
  await startServices();
  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
  });
});

app.on('window-all-closed', () => {
  stopServices();
  if (process.platform !== 'darwin') app.quit();
});
