#!/usr/bin/env python3
"""
Migration script to add current_stage column to video_translation_tasks table
"""
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate():
    """Add current_stage column to video_translation_tasks table"""
    try:
        # Create database engine
        database_url = settings.DATABASE_URL.replace("sqlite:///", "sqlite:///") if settings.DATABASE_URL.startswith("sqlite:///") else settings.DATABASE_URL
        engine = create_engine(database_url)
        
        with engine.connect() as conn:
            # Check if column already exists (PostgreSQL syntax)
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'video_translation_tasks' 
                AND column_name = 'current_stage'
            """))
            column_exists = result.fetchone() is not None
            
            if column_exists:
                logger.info("Column 'current_stage' already exists in video_translation_tasks table")
                return
            
            # Add the column
            logger.info("Adding 'current_stage' column to video_translation_tasks table...")
            conn.execute(text("ALTER TABLE video_translation_tasks ADD COLUMN current_stage VARCHAR(255)"))
            conn.commit()
            
            logger.info("Migration completed successfully")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    migrate()
