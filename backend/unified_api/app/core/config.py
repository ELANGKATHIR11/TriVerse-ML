"""Application configuration using Pydantic Settings."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    APP_NAME: str = "TriVerse ML"
    APP_VERSION: str = "2.0.0"
    DEBUG: bool = False

    # Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent.parent
    DATASETS_DIR: Path = BASE_DIR.parent / "datasets"
    ARTIFACTS_DIR: Path = BASE_DIR.parent / "artifacts"
    REPORTS_DIR: Path = BASE_DIR.parent / "reports"
    TRAINED_MODELS_DIR: Path = BASE_DIR.parent / "trained_models"
    MLRUNS_DIR: Path = BASE_DIR.parent / "mlruns"
    CHROMA_DIR: Path = BASE_DIR.parent / "chroma_db"

    # Database
    DATABASE_URL: str = f"sqlite+aiosqlite:///./codealpha.db"

    # JWT
    SECRET_KEY: str = "codealpha-super-secret-key-change-in-production-2025"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # MLflow
    MLFLOW_TRACKING_URI: str = "http://localhost:5000"
    MLFLOW_EXPERIMENT_PREFIX: str = "codealpha"

    # Optuna
    OPTUNA_STORAGE: str = "sqlite:///./optuna.db"
    OPTUNA_N_TRIALS: int = 30

    # Ollama
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "qwen2.5-coder:3b"
    OLLAMA_EMBED_MODEL: str = "nomic-embed-text"

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    # GPU
    USE_GPU: bool = True
    GPU_DEVICE: str = "cuda"

    # Admin seed
    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@codealpha.ai"
    ADMIN_PASSWORD: str = "admin123"


settings = Settings()
