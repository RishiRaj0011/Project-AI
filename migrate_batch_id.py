"""
Database Migration: Add batch_id to LocationMatch for Multi-Video Batch Analysis
Run this script to update the database schema
"""

from __init__ import create_app, db
from sqlalchemy import text

def migrate_batch_id():
    app = create_app()
    
    with app.app_context():
        try:
            # Check if column already exists
            result = db.session.execute(text(
                "SELECT COUNT(*) FROM pragma_table_info('location_match') WHERE name='batch_id'"
            ))
            exists = result.scalar() > 0
            
            if not exists:
                print("Adding batch_id column to location_match table...")
                db.session.execute(text(
                    "ALTER TABLE location_match ADD COLUMN batch_id VARCHAR(50)"
                ))
                db.session.commit()
                print("✅ Migration completed successfully!")
            else:
                print("✅ batch_id column already exists. No migration needed.")
                
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()

if __name__ == "__main__":
    migrate_batch_id()
