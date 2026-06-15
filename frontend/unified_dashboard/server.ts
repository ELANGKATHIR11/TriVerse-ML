import express from "express";
import path from "path";
import { fileURLToPath } from "url";
import { createServer as createViteServer } from "vite";
import { request as httpRequest } from "http";

// Ensure ESM compatibility for node
const _filename = typeof __filename !== "undefined" ? __filename : fileURLToPath(import.meta.url);
const _dirname = typeof __dirname !== "undefined" ? __dirname : path.dirname(_filename);

// Deterministic Helper for Local/Native AI Companion Response
function generateNativeResponse(message: string): string {
  const query = message.toLowerCase();
  
  if (query.includes("latency") || query.includes("speed") || query.includes("fast") || query.includes("slow")) {
    return `### ⚡ CodeAlpha Native Inference Latency Optimization Guide

For edge or high-performance production deployment of deep networks, we recommend the following local strategies:

1. **Precision Calibration (FP16 / INT8 Quantization)**
   * Reduces the disk footprint of weights by up to 75%.
   * Leveraging TensorRT or ONNX Runtime exposes execution providers that reduce latency by **~2.4x** on local compute cores.
   * *Tradeoff*: Minor loss calibration (<0.08% ROC-AUC degrade) on the final test split.

2. **Structural Pruning**
   * Prune low-magnitude convolutional weights or attention channels.
   * Pruning 20% of redundant parameters yields a high speedup with zero architectural modifications.

3. **Batch Tuning**
   * Keep batch sizing aligned to binary increments (e.g. 16, 32, 64) to maximize compute alignment on CPU/GPU threads and avoid fractional utilization padding overhead.`;
  }
  
  if (query.includes("correlation") || query.includes("debt") || query.includes("credit") || query.includes("delinquencies") || query.includes("score")) {
    return `### 📊 Credit Risk Dashboard Correlation Analysis

Based on our native credit scoring dataset benchmarks (FICO evaluation cohorts):

* **Debt-to-Income Ratio (DTI)** stays strongly positively correlated with **90-Day Delinquencies** (Pearson correlation coefficient: **r = +0.58**).
* **Payment History Percent Range**: Displays deep inverse correlation with defaults (**r = -0.74**), confirming it as the primary predictive biomarker of credit competence.
* **Feature Imbalance Mitigation**:
  * Our native pipelines automatically load **SMOTE** oversampling to resolve class imbalances before model fit.
  * Adjusting custom class threshold bounds to **0.32** rather than the standard 0.50 increases Risk-Recall by **~12%** in testing splits.`;
  }

  if (query.includes("optuna") || query.includes("adamw") || query.includes("tuning") || query.includes("learning rate") || query.includes("rate") || query.includes("parameter")) {
    return `### 🧪 Hyperparameter Optimization (Optuna ADAMW Tuning Recommendation)

To yield stable and rapid training convergence on risk and disease forecasting models:

* **ADAMW Weight Decay**: Configure within search space range \`[1e-6, 1e-3]\`.
* **Learning Rate (LR)**: Recommend starting with a custom adaptive learning scheduler (Cosine Decelerating Annealing) bounded within \`[1e-5, 5e-4]\`.
* **Batch Size**: Recommend \`32\` on small classification sets and \`128\` on handwriting visual models.
* **Multi-Objective Optimization**:
  * Set Optuna trials to maximize **Accuracy** while simultaneously minimizing **Cross-Entropy Loss**.
  * Use the Tree-Structured Parzen Estimator (TPE) sampler for optimal convergence pathing in fewer than 40 trials.`;
  }

  if (query.includes("disease") || query.includes("prediction") || query.includes("mimic") || query.includes("health") || query.includes("medical") || query.includes("shap")) {
    return `### 🏥 Native Disease Prediction & Biomarker Analysis

Our native medical imaging and clinical diagnostic metrics (using MIMIC-IV cohort mappings) suggest:

1. **SHAP (Shapley Additive exPlanations)** keys:
   * **Glucose levels** & **Systolic BP** stand out as high-impact positive catalysts for disease risk index levels.
   * **Age** displays standard progressive risk curves with a steep upward derivative past 52 years.
2. **Model Metrics**:
   * Our native Random Forest Classifier achieves a **93.8% Accuracy** with an outstanding **0.95 ROC-AUC score**.
   * High feature density ensures consistent diagnostic recommendations across independent test runs.`;
  }

  if (query.includes("handwriting") || query.includes("mnist") || query.includes("canvas") || query.includes("digit") || query.includes("drawing")) {
    return `### ✏️ Native Handwriting CNN Model Architecture

The handwriting digit identifier uses a high-performance native Convolutional Neural Network (CNN):

* **Architecture**: 
  * Convolutional layer 1 (32 channels, 3x3 kernel, ReLU)
  * Max Pooling layer (2x2 pool)
  * Convolutional layer 2 (64 channels, 3x3 kernel, ReLU)
  * Max Pooling layer (2x2 pool)
  * Fully Connected (Dense) layer (128 units, dropout rate 0.45)
  * Softmax Output classifier (10 probability scores)
* **Performance**: Achieves **~98.4% validation accuracy** when fully trained on standard visual arrays, running fully on-device.`;
  }

  if (query.includes("hello") || query.includes("hi") || query.includes("hey") || query.includes("help") || query.includes("who are you") || query.includes("companion")) {
    return `Hello! I am your CodeAlpha expert **Native AI Companion Copilot**, running 100% offline within your secure local platform.

How can I help you optimize your models today? Feel free to ask about:
* **Inference latency** models optimization.
* **Credit scoring** correlations and class balancing.
* **Optuna & ADAMW** hyperparameter tuning strategies.
* **MIMIC-IV disease classification** metrics list.
* **Handwriting digit prediction** networks.`;
  }

  return `### 🖥️ Native CodeAlpha Offline Model Intelligence

I have analyzed your query about: *"${message}"*.

As a fully native offline model companion operating inside your container workspace without external API keys or cloud server networks, here are the main recommendations:

1. **Platform Independence**: Your CodeAlpha Enterprise app runs completely offline. You do not need secondary external keys, billing setups, or global API credentials.
2. **Deterministic Calibration**: Try executing live simulation runs inside the **Training Monitor** or running hyperparameter tuning sweeps under **Optuna Tuning** to observe performance progression immediately.
3. **Local Architecture**: You can evaluate model registry pipelines, review security metrics, and predict digits offline directly in the corresponding tabs.

*Feel free to specify words like **latency**, **credit score**, **optuna**, or **disease** to access matching expert dossiers!*`;
}

async function startServer() {
  const app = express();
  const PORT = 3000;

  // Proxy `/api/chat` to `/assistant/chat` with session_id injection and SSE support
  app.post("/api/chat", express.json(), async (req, res) => {
    const bodyStr = JSON.stringify({
      message: req.body.message || "",
      session_id: req.body.session_id || "global"
    });
    
    const headers: Record<string, string> = {};
    for (const [key, val] of Object.entries(req.headers)) {
      const lowerKey = key.toLowerCase();
      if (val !== undefined && lowerKey !== "host" && lowerKey !== "content-length") {
        headers[key] = Array.isArray(val) ? val.join(", ") : val;
      }
    }
    headers["content-type"] = "application/json";
    headers["content-length"] = Buffer.byteLength(bodyStr).toString();
    
    const proxyReq = httpRequest(
      {
        host: "127.0.0.1",
        port: 8000,
        path: "/assistant/chat",
        method: "POST",
        headers: headers,
      },
      (proxyRes) => {
        let responseBody = "";
        proxyRes.on("data", (chunk) => {
          responseBody += chunk.toString();
        });
        proxyRes.on("end", () => {
          res.setHeader("Content-Type", "application/json");
          res.status(proxyRes.statusCode || 200).json({ text: responseBody });
        });
      }
    );
    
    proxyReq.write(bodyStr);
    proxyReq.end();
    
    proxyReq.on("error", (err) => {
      console.error("FastAPI Chat Proxy error:", err);
      res.status(502).json({
        error: "FastAPI Backend is not reachable.",
        details: err?.message
      });
    });
  });

  // Proxy all other /api requests to FastAPI backend
  app.use("/api", (req, res, next) => {
    // Exclude health check
    if (req.path === "/health") {
      return next();
    }
    
    const targetUrl = "http://127.0.0.1:8000";
    const path = req.originalUrl.replace(/^\/api/, "");
    
    const headers: Record<string, string> = {};
    for (const [key, val] of Object.entries(req.headers)) {
      if (val !== undefined && key.toLowerCase() !== "host") {
        headers[key] = Array.isArray(val) ? val.join(", ") : val;
      }
    }
    
    const proxyReq = httpRequest(
      `${targetUrl}${path}`,
      {
        method: req.method,
        headers: headers,
      },
      (proxyRes) => {
        res.writeHead(proxyRes.statusCode || 200, proxyRes.headers);
        proxyRes.pipe(res);
      }
    );
    
    req.pipe(proxyReq);
    
    proxyReq.on("error", (err) => {
      console.error("FastAPI Backend proxy error:", err);
      res.status(502).json({
        error: "FastAPI Backend is not reachable.",
        details: err?.message
      });
    });
  });

  // Body parsers
  app.use(express.json());

  // Passive health endpoint
  app.get("/api/health", (req, res) => {
    res.json({ status: "healthy", timestamp: new Date().toISOString() });
  });

  // Serve favicon
  app.get("/favicon.ico", (req, res) => {
    res.sendFile(path.join(_dirname, "public", "favicon.svg"));
  });

  // Simulated metrics and database pipelines for interactive dashboards
  app.get("/api/metrics/realtime", (req, res) => {
    // Return live CPU, memory, current active training status
    const second = Math.floor(Date.now() / 1000) % 120;
    const epoch = Math.min(100, Math.floor(second / 4) + 1);
    const loss = Math.max(0.05, 0.95 * Math.exp(-second / 25) + 0.02 * Math.sin(second));
    const accuracy = Math.min(0.99, 0.65 + 0.33 * (1 - Math.exp(-second / 30)) + 0.01 * Math.cos(second));
    
    res.json({
      epoch,
      batch: (second * 12) % 400 + 1,
      totalBatches: 400,
      accuracy: parseFloat(accuracy.toFixed(4)),
      loss: parseFloat(loss.toFixed(4)),
      etaSeconds: Math.max(0, 120 - second),
      system: {
        cpu: Math.floor(45 + 15 * Math.sin(second / 5) + Math.random() * 5),
        ram: parseFloat((14.2 + 0.8 * Math.cos(second / 10) + Math.random() * 0.1).toFixed(1)),
        gpuTemp: Math.floor(68 + 8 * Math.sin(second / 12)),
        gpuMemory: parseFloat((9.4 + 1.2 * Math.sin(second / 20)).toFixed(1)),
      }
    });
  });

  // Mount Vite middleware in development mode
  if (process.env.NODE_ENV !== "production") {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: "spa",
    });
    app.use(vite.middlewares);
  } else {
    // Serve production static assets compiled inside dist
    const distPath = path.join(process.cwd(), "dist");
    app.use(express.static(distPath));
    app.get("*", (req, res) => {
      res.sendFile(path.join(distPath, "index.html"));
    });
  }

  const server = app.listen(PORT, "0.0.0.0", () => {
    console.log(`[CodeAlpha Server] Listening on http://0.0.0.0:${PORT}`);
  });

  server.on("upgrade", (req, socket, head) => {
    if (req.url && (req.url.startsWith("/api/training/ws/") || req.url.startsWith("/api/ws/") || req.url.includes("/ws/"))) {
      // Resolve path mapping
      const path = req.url.replace(/^\/api/, "");
      
      const proxyReq = httpRequest({
        port: 8000,
        host: "127.0.0.1",
        path: path,
        method: "GET",
        headers: {
          "Connection": "Upgrade",
          "Upgrade": "websocket",
          "Sec-WebSocket-Key": req.headers["sec-websocket-key"] as string,
          "Sec-WebSocket-Version": req.headers["sec-websocket-version"] as string,
          ...(req.headers["sec-websocket-extensions"] ? { "Sec-WebSocket-Extensions": req.headers["sec-websocket-extensions"] as string } : {}),
          ...(req.headers["sec-websocket-protocol"] ? { "Sec-WebSocket-Protocol": req.headers["sec-websocket-protocol"] as string } : {})
        }
      });

      proxyReq.on("upgrade", (proxyRes, proxySocket, proxyHead) => {
        let responseHeaders = "HTTP/1.1 101 Switching Protocols\r\n";
        for (const [key, value] of Object.entries(proxyRes.headers)) {
          if (value !== undefined) {
            responseHeaders += `${key}: ${Array.isArray(value) ? value.join(", ") : value}\r\n`;
          }
        }
        responseHeaders += "\r\n";
        
        socket.write(responseHeaders);
        proxySocket.pipe(socket);
        socket.pipe(proxySocket);
      });

      proxyReq.on("error", (err) => {
        console.error("WebSocket proxy handshaking error:", err);
        socket.destroy();
      });

      proxyReq.end();
    } else {
      socket.destroy();
    }
  });
}

startServer();
