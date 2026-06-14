"""Main FastAPI application module."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.core.seed import seed_admin
from app.core.error_manager import register_error_handlers

# Import all routers
from app.api.routes import (
    auth,
    users,
    datasets,
    training,
    metrics,
    mlflow_routes,
    optuna_routes,
    leaderboard,
    models,
    reports,
    predictions,
    assistant,
    digital_twin,
    analytics,
    security,
)
from app.api.routes.health import router as health_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup sequence ──────────────────────────────────────────────────
    print("[Startup] Initializing Database...")
    await init_db()

    print("[Startup] Seeding default admin user...")
    async with AsyncSessionLocal() as db:
        await seed_admin(db)

    # Create required directories
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    os.makedirs(settings.ARTIFACTS_DIR, exist_ok=True)
    os.makedirs(settings.TRAINED_MODELS_DIR, exist_ok=True)

    # ── Pre-flight diagnostics ────────────────────────────────────────────
    print("[Startup] Running platform diagnostics...")
    try:
        from app.core.startup_diagnostics import run_startup_diagnostics
        snapshot = await run_startup_diagnostics()
        print(f"[Startup] Diagnostics complete — platform status: {snapshot['overall'].upper()}")
        for name, check in snapshot["checks"].items():
            icon = "✓" if check["status"] == "ok" else ("⚠" if check["status"] == "warning" else "✗")
            print(f"  {icon} {name}: {check['message']}")
    except Exception as diag_err:
        print(f"[Startup] Diagnostics failed (non-fatal): {diag_err}")

    yield

    # ── Shutdown sequence ─────────────────────────────────────────────────
    print("[Shutdown] Cleaning up services...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# ── Register global error handlers ───────────────────────────────────────────
register_error_handlers(app)

# ── CORS configuration ────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files mapping ──────────────────────────────────────────────────────
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
app.mount("/report-static", StaticFiles(directory=str(settings.REPORTS_DIR)), name="reports")

# ── Include all route routers ─────────────────────────────────────────────────
app.include_router(health_router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(datasets.router)
app.include_router(training.router)
app.include_router(metrics.router)
app.include_router(mlflow_routes.router)
app.include_router(optuna_routes.router)
app.include_router(leaderboard.router)
app.include_router(models.router)
app.include_router(reports.router)
app.include_router(predictions.router)
app.include_router(assistant.router)
app.include_router(digital_twin.router)
app.include_router(analytics.router)
app.include_router(security.router)


@app.get("/health", tags=["system"])
async def health_check():
    """Simple health check — returns 200 when the server is online."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["system"])
async def root():
    """Welcome page index."""
    return {
        "message": f"Welcome to the {settings.APP_NAME} API portal.",
        "documentation": "/docs",
        "status": "online",
    }
