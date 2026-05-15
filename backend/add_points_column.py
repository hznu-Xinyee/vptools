"""
Migration script to add points column to users table
Run this script: python add_points_column.py
"""
from sqlalchemy import text
from app.core.database import engine

def add_points_column():
    """Add points column to users table"""
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT COUNT(*) as count 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'points'
        """))
        column_exists = result.fetchone()[0] > 0
        
        if column_exists:
            print("Column 'points' already exists in users table")
            return
        
        # Add the column
        conn.execute(text("""
            ALTER TABLE users 
            ADD COLUMN points INTEGER DEFAULT 0 NOT NULL
        """))
        conn.commit()
        print("Successfully added 'points' column to users table")

if __name__ == "__main__":
    add_points_column()
