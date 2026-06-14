"""Main FastAPI application module."""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.core.seed import seed_admin

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
    security
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup sequence
    print("[Startup] Initializing Database...")
    await init_db()
    
    print("[Startup] Seeding default admin user...")
    async with AsyncSessionLocal() as db:
        await seed_admin(db)
        
    # Create required directories if they don't exist
    os.makedirs(settings.REPORTS_DIR, exist_ok=True)
    os.makedirs(settings.ARTIFACTS_DIR, exist_ok=True)
    os.makedirs(settings.TRAINED_MODELS_DIR, exist_ok=True)
    
    yield
    # Shutdown sequence
    print("[Shutdown] Cleaning up services...")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mapping
# Ensure the directories exist before mounting
os.makedirs(settings.REPORTS_DIR, exist_ok=True)
app.mount("/report-static", StaticFiles(directory=str(settings.REPORTS_DIR)), name="reports")

# Include all route routers
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
    """Retrieve system health status."""
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION
    }

@app.get("/", tags=["system"])
async def root():
    """Welcome page index."""
    return {
        "message": f"Welcome to the {settings.APP_NAME} API portal.",
        "documentation": "/docs",
        "status": "online"
    }
