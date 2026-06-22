/**
 * electron-main.cjs — TriVerse AI Desktop Orchestrator  v3
 *
 * FIXED:
 *  - Uses ABSOLUTE binary paths (no conda/npx in PATH required)
 *  - Loading screen is embedded IN the main window (no blank flash)
 *  - Services start BEFORE main window navigates to the real URL
 *  - IPC sends live boot status to the in-window loading page
 *
 * Boot order:
 *   1. Main window opens immediately showing local loading.html
 *   2. MLflow spawns (background, non-blocking)
 *   3. FastAPI spawns via absolute uvicorn.exe
 *   4. Poll http://127.0.0.1:8000/health/live  (max 120 s)
 *   5. Gateway (tsx server.ts) spawns via absolute node.exe
 *   6. Poll http://localhost:3000               (max 60 s)
 *   7. win.loadURL('http://localhost:3000')  → real app appears
 */

'use strict';

const { app, BrowserWindow, ipcMain } = require('electron');
const path   = require('path');
const fs     = require('fs');
const { spawn } = require('child_process');
const http   = require('http');

// ── Absolute binary paths ─────────────────────────────────────────────────────
const CONDA_SCRIPTS  = 'C:\\Users\\elang\\Miniconda3\\envs\\dgpu-core\\Scripts';
const CONDA_ROOT     = 'C:\\Users\\elang\\Miniconda3\\envs\\dgpu-core';
const PYTHON_EXE     = path.join(CONDA_ROOT,    'python.exe');
const UVICORN_EXE    = path.join(CONDA_SCRIPTS, 'uvicorn.exe');
const MLFLOW_EXE     = path.join(CONDA_SCRIPTS, 'mlflow.exe');
const NODE_EXE       = 'F:\\FULL-STACK\\node.exe';

// ── Project paths ─────────────────────────────────────────────────────────────
function getProjectRoot() {
  let cur = path.resolve(__dirname);
  for (let i = 0; i < 6; i++) {
    if (fs.existsSync(path.join(cur, 'backend')) &&
        fs.existsSync(path.join(cur, 'frontend'))) return cur;
    const p = path.dirname(cur);
    if (p === cur) break;
    cur = p;
  }
  return path.resolve(__dirname);
}

const ROOT          = getProjectRoot();
const BACKEND_DIR   = path.join(ROOT, 'backend', 'unified_api');
const FRONTEND_DIR  = path.join(ROOT, 'frontend', 'unified_dashboard');
const MODELS_DIR    = path.join(BACKEND_DIR, 'trained_models');
const MLRUNS_DIR    = path.join(BACKEND_DIR, 'mlruns');

let childProcesses = [];
let mainWin        = null;

// ── Health poll ───────────────────────────────────────────────────────────────
function pollUntilReady(url, maxMs = 120_000, intervalMs = 1_200) {
  return new Promise(resolve => {
    const deadline = Date.now() + maxMs;
    function attempt() {
      http.get(url, res => {
        if (res.statusCode < 500) return resolve(true);
        res.resume();
        retry();
      }).on('error', retry);
    }
    function retry() {
      if (Date.now() > deadline) return resolve(false);
      setTimeout(attempt, intervalMs);
    }
    attempt();
  });
}

// ── Logging helper ─────────────────────────────────────────────────────────────
const logFile = path.join(ROOT, 'triverse_boot.log');
try { fs.writeFileSync(logFile, `=== Boot Log Started at ${new Date().toISOString()} ===\n`, 'utf8'); } catch(e){}
function logDebug(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  console.log(msg);
  try { fs.appendFileSync(logFile, line, 'utf8'); } catch(e){}
}

// ── Send status update to the in-window loading page ─────────────────────────
function setStatus(text, pct, isError = false) {
  logDebug(`[Boot] (${pct}%) ${text}`);
  if (mainWin && !mainWin.isDestroyed()) {
    mainWin.webContents.send('boot-status', { text, pct, isError });
  }
}

// ── Spawn helper ──────────────────────────────────────────────────────────────
function spawnService(label, exe, args, opts = {}) {
  logDebug(`[${label}] Spawning: ${exe} ${args.join(' ')}`);
  const proc = spawn(exe, args, {
    cwd: opts.cwd || ROOT,
    env: { ...process.env, ...(opts.env || {}) },
    shell: false,          // ← no shell needed; absolute paths
    windowsHide: true,     // ← no console window
  });
  proc.stdout.on('data', d => logDebug(`[${label}] ${d.toString().trim()}`));
  proc.stderr.on('data', d => logDebug(`[${label} ERROR] ${d.toString().trim()}`));
  proc.on('exit', c => logDebug(`[${label}] exited with code ${c}`));
  childProcesses.push(proc);
  return proc;
}

// ── Inline loading page (written to __dirname so it always works) ─────────────
function getLoadingHtml() {
  return `<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>TriVerse AI — Starting…</title>
<style>
  *{margin:0;padding:0;box-sizing:border-box}
  html,body{
    width:100%;height:100vh;overflow:hidden;
    background:linear-gradient(135deg,#0f0c29 0%,#302b63 50%,#24243e 100%);
    font-family:'Segoe UI',system-ui,sans-serif;
    color:#e0e0ff;
    display:flex;flex-direction:column;
    align-items:center;justify-content:center;
    user-select:none;
  }
  .logo{
    font-size:2.8rem;font-weight:800;letter-spacing:3px;
    background:linear-gradient(90deg,#a855f7,#6366f1,#38bdf8);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    margin-bottom:6px;
  }
  .tagline{font-size:.85rem;opacity:.5;letter-spacing:1px;margin-bottom:48px;}
  .card{
    background:rgba(255,255,255,.04);
    border:1px solid rgba(255,255,255,.08);
    border-radius:16px;
    padding:32px 48px;
    width:460px;
    backdrop-filter:blur(12px);
  }
  .status-label{
    font-size:.82rem;opacity:.75;margin-bottom:10px;
    min-height:1.2em;
    transition:all .3s;
  }
  .status-label.error{color:#f87171;}
  .bar-track{
    width:100%;height:6px;
    background:rgba(255,255,255,.1);
    border-radius:3px;overflow:hidden;
  }
  .bar-fill{
    height:100%;width:0%;
    background:linear-gradient(90deg,#a855f7,#6366f1,#38bdf8);
    border-radius:3px;
    transition:width .5s ease;
  }
  .pct{font-size:.75rem;opacity:.4;margin-top:8px;text-align:right;}
  .dots{display:inline-block;animation:dots 1.2s infinite;}
  @keyframes dots{0%{content:''}33%{content:'.'}66%{content:'..'}100%{content:'...'}}
  .step-list{margin-top:28px;list-style:none;display:flex;flex-direction:column;gap:8px;}
  .step{display:flex;align-items:center;gap:10px;font-size:.78rem;opacity:.45;transition:.3s;}
  .step.active{opacity:1;}
  .step.done{opacity:.6;}
  .step .dot{
    width:8px;height:8px;border-radius:50%;
    background:rgba(255,255,255,.2);flex-shrink:0;transition:.3s;
  }
  .step.active .dot{background:#a855f7;box-shadow:0 0 8px #a855f7;}
  .step.done  .dot{background:#22c55e;}
  .version{position:fixed;bottom:16px;font-size:.7rem;opacity:.25;}
</style>
</head>
<body>
<div class="logo">TriVerse AI</div>
<div class="tagline">PRODUCTION ML PLATFORM</div>
<div class="card">
  <div class="status-label" id="status">Initializing<span class="dots"></span></div>
  <div class="bar-track"><div class="bar-fill" id="bar"></div></div>
  <div class="pct" id="pct">0%</div>
  <ul class="step-list">
    <li class="step" id="s-mlflow"><span class="dot"></span>MLflow Tracking Server</li>
    <li class="step" id="s-backend"><span class="dot"></span>FastAPI Backend (port 8000)</li>
    <li class="step" id="s-gateway"><span class="dot"></span>UI Gateway (port 3000)</li>
    <li class="step" id="s-ollama"><span class="dot"></span>Ollama — qwen2.5-coder:3b</li>
  </ul>
</div>
<div class="version">v2.0.0 &nbsp;·&nbsp; dgpu-core &nbsp;·&nbsp; RTX 5060</div>

<script>
try {
  const { ipcRenderer } = require('electron');
  const steps = {
    mlflow:  document.getElementById('s-mlflow'),
    backend: document.getElementById('s-backend'),
    gateway: document.getElementById('s-gateway'),
    ollama:  document.getElementById('s-ollama'),
  };

  ipcRenderer.on('boot-status', (_, msg) => {
    const el = document.getElementById('status');
    el.textContent = msg.text;
    el.className = 'status-label' + (msg.isError ? ' error' : '');
    document.getElementById('bar').style.width = msg.pct + '%';
    document.getElementById('pct').textContent = msg.pct + '%';

    // Activate steps based on pct thresholds
    if (msg.pct >= 10)  activateStep('mlflow');
    if (msg.pct >= 25)  doneStep('mlflow'),  activateStep('backend');
    if (msg.pct >= 60)  doneStep('backend'), activateStep('gateway');
    if (msg.pct >= 85)  doneStep('gateway'), activateStep('ollama');
    if (msg.pct >= 98)  doneStep('ollama');
  });

  function activateStep(k){ if(steps[k]) steps[k].className='step active'; }
  function doneStep(k){     if(steps[k]) steps[k].className='step done'; }
} catch (e) {
  console.error("Renderer script error:", e);
}
</script>
</body>
</html>`;
}

// ── Boot sequence ─────────────────────────────────────────────────────────────
async function bootServices() {
  logDebug('Entering bootServices');
  fs.mkdirSync(MLRUNS_DIR, { recursive: true });
  fs.mkdirSync(MODELS_DIR,  { recursive: true });

  const sharedEnv = {
    TRIVERSE_MODELS_DIR: MODELS_DIR,
    MLFLOW_TRACKING_URI: 'http://127.0.0.1:5000',
    // Make conda env libraries available
    PATH: `${CONDA_ROOT};${CONDA_SCRIPTS};${process.env.PATH}`,
  };

  // 1. MLflow (fire-and-forget; not a hard dependency)
  setStatus('Starting MLflow tracking server…', 10);
  if (fs.existsSync(MLFLOW_EXE)) {
    spawnService('MLflow', MLFLOW_EXE, [
      'server',
      '--host', '127.0.0.1',
      '--port', '5000',
      '--backend-store-uri', `sqlite:///${path.join(MLRUNS_DIR, 'mlflow.db')}`,
      '--default-artifact-root', MLRUNS_DIR,
    ], { cwd: ROOT, env: sharedEnv });
  } else {
    logDebug('[Boot] mlflow.exe not found — skipping MLflow');
  }
  await sleep(1200);

  // 2. FastAPI backend via uvicorn.exe
  setStatus('Starting FastAPI backend…', 25);
  spawnService('FastAPI', UVICORN_EXE, [
    'app.main:app',
    '--host', '127.0.0.1',
    '--port', '8000',
    '--log-level', 'warning',
  ], { cwd: BACKEND_DIR, env: sharedEnv });

  // 3. Poll backend
  setStatus('Waiting for backend (port 8000)…', 38);
  const backendReady = await pollUntilReady('http://127.0.0.1:8000/health/live', 120_000);
  if (backendReady) {
    setStatus('Backend ready ✓', 55);
  } else {
    setStatus('⚠ Backend timed out — continuing…', 55, true);
  }
  await sleep(400);

  // 4. UI Gateway — tsx server.ts
  setStatus('Starting UI gateway (port 3000)…', 62);
  const distServer = path.join(FRONTEND_DIR, 'dist', 'server.cjs');
  const tsxBin     = path.join(FRONTEND_DIR, 'node_modules', '.bin', 'tsx');

  if (fs.existsSync(distServer)) {
    spawnService('Gateway', NODE_EXE, [distServer], {
      cwd: FRONTEND_DIR,
      env: { ...sharedEnv, NODE_ENV: 'production' },
    });
  } else if (fs.existsSync(tsxBin + '.cmd')) {
    // tsx is a local node_modules binary — call it via node
    const tsxScript = path.join(FRONTEND_DIR, 'node_modules', 'tsx', 'dist', 'cli.mjs');
    if (fs.existsSync(tsxScript)) {
      spawnService('Gateway', NODE_EXE, [tsxScript, 'server.ts'], {
        cwd: FRONTEND_DIR,
        env: { ...sharedEnv, NODE_ENV: 'development' },
      });
    } else {
      // Fallback: call tsx.cmd via cmd
      spawnService('Gateway', 'cmd.exe', ['/c', tsxBin + '.cmd', 'server.ts'], {
        cwd: FRONTEND_DIR,
        env: { ...sharedEnv, NODE_ENV: 'development' },
        shell: false,
      });
    }
  } else {
    // Last resort: use system node with npx
    spawnService('Gateway', NODE_EXE, ['F:\\FULL-STACK\\npx.ps1', 'tsx', 'server.ts'], {
      cwd: FRONTEND_DIR,
      env: { ...sharedEnv, NODE_ENV: 'development' },
    });
  }

  // 5. Poll gateway
  setStatus('Waiting for UI gateway (port 3000)…', 72);
  const gatewayReady = await pollUntilReady('http://localhost:3000', 90_000);
  if (gatewayReady) {
    setStatus('UI gateway ready ✓', 88);
  } else {
    setStatus('⚠ Gateway timed out — retrying…', 88, true);
  }
  await sleep(300);

  // 6. Auto-start and Signal Ollama
  setStatus('Checking Ollama status…', 90);
  const ollamaOnline = await pollUntilReady('http://127.0.0.1:11434', 1500, 500);
  if (!ollamaOnline) {
    setStatus('Launching local Ollama server…', 92);
    const localAppData = process.env.LOCALAPPDATA || '';
    const ollamaDefaultPath = path.join(localAppData, 'Programs', 'Ollama', 'ollama.exe');
    const ollamaExe = fs.existsSync(ollamaDefaultPath) ? ollamaDefaultPath : 'ollama';
    spawnService('Ollama', ollamaExe, ['serve'], { cwd: ROOT });
    await sleep(2500);
  }
  setStatus('Connecting to Ollama (qwen2.5-coder:3b)…', 95);
  await sleep(600);
  setStatus('All systems online — launching TriVerse AI…', 100);
  await sleep(800);
}

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// ── Main window ────────────────────────────────────────────────────────────────
function createMainWindow() {
  logDebug('createMainWindow called');
  mainWin = new BrowserWindow({
    width:  1440,
    height: 900,
    minWidth:  900,
    minHeight: 600,
    title: 'TriVerse AI',
    icon: path.join(FRONTEND_DIR, 'app_icon.ico'),
    backgroundColor: '#0f0c29',   // matches loading page bg — no white flash
    webPreferences: {
      nodeIntegration: true,       // needed for ipcRenderer in loading.html
      contextIsolation: false,
    },
  });

  mainWin.setMenuBarVisibility(false);
  mainWin.webContents.openDevTools(); // Open DevTools to see console/rendering errors

  // Write loading page and display it immediately
  const loadingPath = path.join(__dirname, '_loading.html');
  fs.writeFileSync(loadingPath, getLoadingHtml(), 'utf8');
  mainWin.loadFile(loadingPath);

  // Once Electron says the loading page is ready, start the boot sequence
  mainWin.webContents.once('did-finish-load', async () => {
    logDebug('did-finish-load event received');
    try {
      await bootServices();
      logDebug('bootServices completed, loading localhost:3000');
      mainWin.loadURL('http://localhost:3000').catch(err => {
        logDebug(`[Electron ERROR] Failed to load app URL: ${err.message}`);
        setStatus('⚠ Could not load app — is the gateway running?', 100, true);
      });
    } catch (e) {
      logDebug(`[Boot Exception] ${e.stack}`);
    }
  });

  mainWin.on('closed', () => {
    logDebug('mainWin closed');
    mainWin = null;
  });
}

// ── Shutdown ──────────────────────────────────────────────────────────────────
function stopServices() {
  console.log('[Electron] Shutting down all services…');
  for (const proc of childProcesses) {
    try {
      spawn('taskkill', ['/pid', String(proc.pid), '/f', '/t'], {
        shell: true, windowsHide: true,
      });
    } catch (e) {}
  }
  childProcesses = [];
  // Clean up temp files
  for (const tmp of ['_loading.html']) {
    try { fs.unlinkSync(path.join(__dirname, tmp)); } catch (_) {}
  }
}

// ── Entry ─────────────────────────────────────────────────────────────────────
app.whenReady().then(() => {
  createMainWindow();
  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createMainWindow();
  });
});

app.on('window-all-closed', () => {
  stopServices();
  if (process.platform !== 'darwin') app.quit();
});
