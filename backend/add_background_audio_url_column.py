"""
Migration script to add background_audio_url column to video_translation_tasks table
Run this script: python add_background_audio_url_column.py
"""
from sqlalchemy import text
from app.core.database import engine

def add_background_audio_url_column():
    """Add background_audio_url column to video_translation_tasks table"""
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'video_translation_tasks' 
            AND column_name = 'background_audio_url'
        """))
        column_exists = result.fetchone()[0] > 0
        
        if column_exists:
            print("Column 'background_audio_url' already exists in video_translation_tasks table")
            return
        
        # Add the column
        conn.execute(text("""
            ALTER TABLE video_translation_tasks 
            ADD COLUMN background_audio_url VARCHAR(255)
        """))
        conn.commit()
        print("Successfully added 'background_audio_url' column to video_translation_tasks table")

if __name__ == "__main__":
    add_background_audio_url_column()
