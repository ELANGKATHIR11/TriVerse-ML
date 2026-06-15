"""
clear_db.py - Utility to clear old database entries before complete retraining.
"""

import asyncio
import sys
from pathlib import Path

# Setup PYTHONPATH
sys.path.append(str(Path(__file__).resolve().parent))

from app.core.database import init_db, AsyncSessionLocal
from sqlalchemy import text

async def clear_database():
    await init_db()
    async with AsyncSessionLocal() as db:
        print("Clearing database tables...")
        # Tables to truncate
        tables = [
            "experiment_metrics",
            "training_sessions",
            "pipeline_statuses",
            "model_versions",
            "model_registry",
            "prediction_logs",
            "experiments"
        ]
        
        for table in tables:
            try:
                await db.execute(text(f"DELETE FROM {table};"))
                print(f"Cleared table: {table}")
            except Exception as e:
                print(f"Error clearing {table}: {e}")
                
        await db.commit()
        print("Database cleared successfully!")

if __name__ == "__main__":
    asyncio.run(clear_database())
