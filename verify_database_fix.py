"""
Verification Script: Check if all database fixes are applied correctly
"""
import sqlite3
import os

def verify_database_schema():
    """Verify PersonDetection table has all required columns"""
    
    db_path = 'instance/app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(person_detection)")
        columns = {col[1]: col[2] for col in cursor.fetchall()}
        
        print("\n" + "="*60)
        print("VERIFICATION: PersonDetection Table Schema")
        print("="*60)
        
        # Required columns
        required_columns = {
            'matched_view': 'VARCHAR(50)',
            'evidence_number': 'VARCHAR',
            'frame_hash': 'VARCHAR',
            'decision_factors': 'TEXT',
            'feature_weights': 'TEXT',
            'confidence_score': 'FLOAT',
            'frame_path': 'VARCHAR'
        }
        
        all_present = True
        
        for col_name, col_type in required_columns.items():
            if col_name in columns:
                print(f"✅ {col_name:25} {columns[col_name]:20} PRESENT")
            else:
                print(f"❌ {col_name:25} {col_type:20} MISSING")
                all_present = False
        
        # Count existing detections
        cursor.execute("SELECT COUNT(*) FROM person_detection")
        total_detections = cursor.fetchone()[0]
        
        # Count detections with matched_view
        cursor.execute("SELECT COUNT(*) FROM person_detection WHERE matched_view IS NOT NULL")
        with_matched_view = cursor.fetchone()[0]
        
        print("\n" + "="*60)
        print("DETECTION STATISTICS")
        print("="*60)
        print(f"Total Detections:        {total_detections}")
        print(f"With matched_view:       {with_matched_view}")
        print(f"Without matched_view:    {total_detections - with_matched_view}")
        
        conn.close()
        
        print("\n" + "="*60)
        if all_present:
            print("✅ ALL REQUIRED COLUMNS PRESENT - Database is ready!")
        else:
            print("❌ MISSING COLUMNS - Run: python add_matched_view_column.py")
        print("="*60 + "\n")
        
        return all_present
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

def verify_file_structure():
    """Verify all required files exist"""
    
    print("\n" + "="*60)
    print("VERIFICATION: File Structure")
    print("="*60)
    
    required_files = {
        'models.py': 'Database models',
        'location_matching_engine.py': 'Detection engine',
        'add_matched_view_column.py': 'Migration script',
        'templates/admin/forensic_timeline.html': 'Timeline template',
        'DATABASE_FIX_SUMMARY.md': 'Documentation'
    }
    
    all_present = True
    
    for file_path, description in required_files.items():
        if os.path.exists(file_path):
            print(f"✅ {file_path:45} {description}")
        else:
            print(f"❌ {file_path:45} MISSING")
            all_present = False
    
    print("="*60 + "\n")
    return all_present

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DATABASE FIX VERIFICATION")
    print("="*60)
    
    schema_ok = verify_database_schema()
    files_ok = verify_file_structure()
    
    print("\n" + "="*60)
    print("FINAL RESULT")
    print("="*60)
    
    if schema_ok and files_ok:
        print("✅ ALL CHECKS PASSED - System is ready!")
        print("\nNext steps:")
        print("1. Restart Flask application")
        print("2. Run analysis on a case")
        print("3. Check Eye Button in AI Analysis panel")
    else:
        print("❌ SOME CHECKS FAILED")
        if not schema_ok:
            print("\n⚠️  Run migration: python add_matched_view_column.py")
        if not files_ok:
            print("\n⚠️  Some files are missing - check file structure")
    
    print("="*60 + "\n")
