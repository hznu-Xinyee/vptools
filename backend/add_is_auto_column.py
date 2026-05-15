"""
Migration script to add is_auto column to video_translation_tasks table
Run this script: python add_is_auto_column.py
"""
from sqlalchemy import text
from app.core.database import engine

def add_is_auto_column():
    """Add is_auto column to video_translation_tasks table"""
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'video_translation_tasks' 
            AND column_name = 'is_auto'
        """))
        column_exists = result.fetchone()[0] > 0
        
        if column_exists:
            print("Column 'is_auto' already exists in video_translation_tasks table")
            return
        
        # Add the column
        conn.execute(text("""
            ALTER TABLE video_translation_tasks 
            ADD COLUMN is_auto BOOLEAN DEFAULT FALSE NOT NULL
        """))
        conn.commit()
        print("Successfully added 'is_auto' column to video_translation_tasks table")

if __name__ == "__main__":
    add_is_auto_column()
