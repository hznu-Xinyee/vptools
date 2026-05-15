"""
Migration script to add tts_timestamps column to video_translation_tasks table.
Run this script: python add_tts_timestamps_column.py
"""
from sqlalchemy import text
from app.core.database import engine


def add_tts_timestamps_column():
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) as count
            FROM information_schema.columns
            WHERE table_name = 'video_translation_tasks'
            AND column_name = 'tts_timestamps'
        """))
        column_exists = result.fetchone()[0] > 0
        if column_exists:
            print("Column 'tts_timestamps' already exists in video_translation_tasks table")
            return

        conn.execute(text("""
            ALTER TABLE video_translation_tasks
            ADD COLUMN tts_timestamps TEXT
        """))
        conn.commit()
        print("Successfully added 'tts_timestamps' column to video_translation_tasks table")


if __name__ == "__main__":
    add_tts_timestamps_column()
