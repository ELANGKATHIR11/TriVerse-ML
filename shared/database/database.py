"""
F:\3ml project\backend\app\core\database.py

SQLAlchemy 2.0 async database engine, session factory,
declarative base, and dependency injection helper.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Database URL
# ---------------------------------------------------------------------------

# Resolve the project root so the DB file lands alongside the backend package
_PROJECT_ROOT = Path(__file__).resolve().parents[3]  # backend/
_DB_FILE = _PROJECT_ROOT / "codealpha.db"
DATABASE_URL = f"sqlite+aiosqlite:///{_DB_FILE}"

# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

engine: AsyncEngine = create_async_engine(
    DATABASE_URL,
    echo=False,                # Set True to log SQL statements during development
    connect_args={
        "check_same_thread": False,   # Required for SQLite with async
        "timeout": 30,
    },
    pool_pre_ping=True,
    pool_recycle=3600,
)

# ---------------------------------------------------------------------------
# Session factory
# ---------------------------------------------------------------------------

AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# ---------------------------------------------------------------------------
# Declarative base
# ---------------------------------------------------------------------------


class Base(DeclarativeBase):
    """Common declarative base shared by all ORM models."""


# ---------------------------------------------------------------------------
# Dependency
# ---------------------------------------------------------------------------


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    Usage::

        @router.get("/items")
        async def list_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ---------------------------------------------------------------------------
# Table initialisation
# ---------------------------------------------------------------------------


async def init_db() -> None:
    """Create all tables defined via :class:`Base` metadata.

    This is idempotent – tables that already exist are not recreated.
    Call once at application startup (e.g. in a lifespan event).
    """
    # Import all models so their metadata is registered on Base before
    # create_all() is called.  The wildcard import is intentional here.
    import app.models  # noqa: F401  – side-effect import

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database tables initialised at: %s", _DB_FILE)
