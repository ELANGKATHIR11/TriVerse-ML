const { app, BrowserWindow } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require('child_process');

let childProcesses = [];

function getProjectRoot() {
  let current = path.resolve(__dirname);
  // Traverse up to 5 levels to locate the root containing 'backend' and 'frontend'
  for (let i = 0; i < 5; i++) {
    if (fs.existsSync(path.join(current, 'backend')) && fs.existsSync(path.join(current, 'frontend'))) {
      return current;
    }
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  return path.resolve(__dirname); // fallback
}

const root = getProjectRoot();

function startServices() {
  console.log("[Electron] Locating project root:", root);
  const backendDir = path.join(root, 'backend', 'unified_api');
  const frontendDir = path.join(root, 'frontend', 'unified_dashboard');
  const mlrunsDir = path.join(root, 'mlruns');
  const condaEnv = "dgpu-aiml";

  // Ensure directories exist
  if (!fs.existsSync(mlrunsDir)) {
    fs.mkdirSync(mlrunsDir, { recursive: true });
  }

  // 1. Start MLflow Tracking Server
  const mlflowArgs = [
    'run', '-n', condaEnv,
    'mlflow', 'server',
    '--host', '127.0.0.1',
    '--port', '5000',
    '--backend-store-uri', `sqlite:///${path.join(mlrunsDir, 'mlflow.db')}`,
    '--default-artifact-root', mlrunsDir
  ];
  console.log("[Electron] Spawning MLflow Server...");
  const mlflowProc = spawn('conda', mlflowArgs, { shell: true, cwd: root });
  childProcesses.push(mlflowProc);

  // 2. Start FastAPI Backend
  const fastapiArgs = [
    'run', '-n', condaEnv,
    'python', '-m', 'uvicorn', 'app.main:app',
    '--host', '127.0.0.1',
    '--port', '8000'
  ];
  console.log("[Electron] Spawning FastAPI Backend...");
  const fastapiProc = spawn('conda', fastapiArgs, { shell: true, cwd: backendDir });
  childProcesses.push(fastapiProc);

  // 3. Start Node Express Gateway Server
  console.log("[Electron] Spawning Express Gateway...");
  const distServerPath = path.join(frontendDir, 'dist', 'server.cjs');
  let gatewayProc;
  if (fs.existsSync(distServerPath)) {
    console.log("[Electron] Starting gateway in production mode...");
    gatewayProc = spawn('node', [distServerPath], {
      shell: true,
      cwd: frontendDir,
      env: { ...process.env, NODE_ENV: 'production' }
    });
  } else {
    console.log("[Electron] Starting gateway in development mode...");
    gatewayProc = spawn('npx', ['tsx', 'server.ts'], {
      shell: true,
      cwd: frontendDir,
      env: { ...process.env, NODE_ENV: 'development' }
    });
  }
  childProcesses.push(gatewayProc);

  // Wire up console outputs for visibility
  for (const proc of childProcesses) {
    proc.stderr.on('data', (data) => {
      console.error(`[Service Stderr]: ${data.toString().trim()}`);
    });
    proc.stdout.on('data', (data) => {
      console.log(`[Service Stdout]: ${data.toString().trim()}`);
    });
  }
}

function stopServices() {
  console.log("[Electron] Terminating all background services...");
  for (const proc of childProcesses) {
    try {
      if (process.platform === 'win32') {
        // Forcefully kill process tree in Windows
        spawn('taskkill', ['/pid', proc.pid, '/f', '/t']);
      } else {
        proc.kill();
      }
    } catch (e) {
      console.error("[Electron] Failed to terminate child process:", e);
    }
  }
  childProcesses = [];
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1400,
    height: 900,
    title: "TriVerse ML",
    icon: path.join(__dirname, 'app_icon.ico'),
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Set menu visibility
  win.setMenuBarVisibility(false);

  // Retry loading URL until local gateway is up
  const loadWithRetry = () => {
    win.loadURL('http://localhost:3000').catch(() => {
      console.log("[Electron] Waiting for local server on port 3000... retrying in 500ms");
      setTimeout(loadWithRetry, 500);
    });
  };
  loadWithRetry();
}

app.whenReady().then(() => {
  startServices();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopServices();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

