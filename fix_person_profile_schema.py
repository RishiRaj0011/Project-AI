"""
Fix person_profile table schema - Add missing columns
Run this ONCE before starting the application
"""
import sqlite3
import os

def fix_person_profile_table():
    db_path = os.path.join('instance', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if person_profile table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='person_profile'")
    if not cursor.fetchone():
        print("person_profile table doesn't exist yet. Will be created on first run.")
        conn.close()
        return
    
    # Columns to add
    columns = [
        ('front_encodings', 'TEXT'),
        ('left_profile_encodings', 'TEXT'),
        ('right_profile_encodings', 'TEXT'),
        ('video_encodings', 'TEXT'),
        ('total_encodings', 'INTEGER DEFAULT 0'),
        ('age_progression_data', 'TEXT'),
        ('dominant_colors', 'TEXT'),
        ('clothing_patterns', 'TEXT'),
        ('seasonal_category', 'VARCHAR(30)'),
        ('texture_features', 'TEXT'),
        ('body_measurements', 'TEXT'),
        ('build_type', 'VARCHAR(30)'),
        ('height_estimation', 'FLOAT'),
        ('biometric_confidence', 'FLOAT DEFAULT 0.0'),
        ('recognition_threshold', 'FLOAT DEFAULT 0.6')
    ]
    
    print("Fixing person_profile table schema...")
    
    for col_name, col_type in columns:
        try:
            cursor.execute(f"ALTER TABLE person_profile ADD COLUMN {col_name} {col_type}")
            print(f"Added column: {col_name}")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e).lower():
                print(f"Column {col_name} already exists")
            else:
                print(f"Error adding {col_name}: {e}")
    
    conn.commit()
    conn.close()
    print("Database schema fixed successfully!")

if __name__ == "__main__":
    fix_person_profile_table()
