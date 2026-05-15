#!/usr/bin/env python3
"""
Migration script to add multi-language auto translation columns to video_translation_tasks table
"""
import os
from pathlib import Path

from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_database_url():
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"]

    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            if key.strip() == "DATABASE_URL":
                return value.strip().strip('"').strip("'")

    raise RuntimeError("DATABASE_URL is not set and was not found in backend/.env")


def migrate():
    """Add multi-language auto translation columns to video_translation_tasks table"""
    try:
        database_url = get_database_url()
        engine = create_engine(database_url)

        columns = {
            "target_languages": "TEXT",
            "language_results_json": "TEXT",
            "charged_points": "INTEGER DEFAULT 0 NOT NULL",
            "points_refunded": "BOOLEAN DEFAULT FALSE NOT NULL",
            "refunded_at": "TIMESTAMP",
        }

        with engine.connect() as conn:
            for column_name, column_type in columns.items():
                result = conn.execute(text("""
                    SELECT column_name
                    FROM information_schema.columns
                    WHERE table_name = 'video_translation_tasks'
                    AND column_name = :column_name
                """), {"column_name": column_name})
                column_exists = result.fetchone() is not None

                if column_exists:
                    logger.info("Column '%s' already exists in video_translation_tasks table", column_name)
                    continue

                logger.info("Adding '%s' column to video_translation_tasks table...", column_name)
                conn.execute(text(f"ALTER TABLE video_translation_tasks ADD COLUMN {column_name} {column_type}"))

            conn.commit()
            logger.info("Migration completed successfully")

    except Exception as e:
        logger.error("Migration failed: %s", str(e))
        raise


if __name__ == "__main__":
    migrate()
