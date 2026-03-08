"""
Fix Existing Database Paths - Convert Backslashes to Forward Slashes
Run this ONCE to fix all existing paths in the database
"""
import sqlite3
import os

def fix_existing_paths():
    db_path = os.path.join('instance', 'app.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("FIXING EXISTING DATABASE PATHS")
    print("=" * 60)
    
    # Fix target_image paths
    print("\nFixing target_image table...")
    cursor.execute("SELECT id, image_path FROM target_image WHERE image_path LIKE '%\\%'")
    images = cursor.fetchall()
    
    fixed_images = 0
    for img_id, img_path in images:
        new_path = img_path.replace('\\', '/')
        cursor.execute("UPDATE target_image SET image_path = ? WHERE id = ?", (new_path, img_id))
        print(f"  Fixed: {img_path} -> {new_path}")
        fixed_images += 1
    
    # Fix search_video paths
    print("\nFixing search_video table...")
    cursor.execute("SELECT id, video_path FROM search_video WHERE video_path LIKE '%\\%'")
    videos = cursor.fetchall()
    
    fixed_videos = 0
    for vid_id, vid_path in videos:
        new_path = vid_path.replace('\\', '/')
        cursor.execute("UPDATE search_video SET video_path = ? WHERE id = ?", (new_path, vid_id))
        print(f"  Fixed: {vid_path} -> {new_path}")
        fixed_videos += 1
    
    # Fix surveillance_footage paths (if exists)
    try:
        print("\nFixing surveillance_footage table...")
        cursor.execute("SELECT id, video_path FROM surveillance_footage WHERE video_path LIKE '%\\%'")
        footage = cursor.fetchall()
        
        fixed_footage = 0
        for footage_id, footage_path in footage:
            new_path = footage_path.replace('\\', '/')
            cursor.execute("UPDATE surveillance_footage SET video_path = ? WHERE id = ?", (new_path, footage_id))
            print(f"  Fixed: {footage_path} -> {new_path}")
            fixed_footage += 1
    except sqlite3.OperationalError:
        print("  surveillance_footage table not found (skipping)")
        fixed_footage = 0
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Fixed {fixed_images} image paths")
    print(f"Fixed {fixed_videos} video paths")
    print(f"Fixed {fixed_footage} footage paths")
    print(f"Total: {fixed_images + fixed_videos + fixed_footage} paths fixed")
    print("\nAll paths now use forward slashes (/)")
    print("=" * 60)

if __name__ == "__main__":
    fix_existing_paths()
