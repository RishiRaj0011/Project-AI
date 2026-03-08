"""
Database Migration: Add matched_view column to PersonDetection
Run this script to update the database schema
"""
import sqlite3
import os

def migrate_database():
    """Add matched_view column to person_detection table"""
    
    db_path = 'instance/app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column already exists
        cursor.execute("PRAGMA table_info(person_detection)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'matched_view' in columns:
            print("✅ Column 'matched_view' already exists in person_detection table")
            conn.close()
            return True
        
        # Add the column
        print("Adding 'matched_view' column to person_detection table...")
        cursor.execute("""
            ALTER TABLE person_detection 
            ADD COLUMN matched_view VARCHAR(50)
        """)
        
        conn.commit()
        conn.close()
        
        print("✅ Successfully added 'matched_view' column to person_detection table")
        print("✅ Database migration completed!")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    print("="*60)
    print("DATABASE MIGRATION: Add matched_view column")
    print("="*60)
    migrate_database()
