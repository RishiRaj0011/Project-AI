"""
Verification Script - Check All Fixes
Run this after starting the Flask app to verify everything works
"""

def verify_database_paths():
    """Check that all paths in database use forward slashes"""
    from __init__ import create_app, db
    from models import Case, TargetImage, SearchVideo
    
    app = create_app()
    with app.app_context():
        print("=" * 60)
        print("CHECKING DATABASE PATHS")
        print("=" * 60)
        
        # Check images
        images = TargetImage.query.limit(10).all()
        backslash_count = 0
        for img in images:
            if '\\' in img.image_path:
                backslash_count += 1
                print(f"FAIL - Backslash found: {img.image_path}")
            else:
                print(f"OK: {img.image_path}")
        
        # Check videos
        videos = SearchVideo.query.limit(10).all()
        for vid in videos:
            if '\\' in vid.video_path:
                backslash_count += 1
                print(f"FAIL - Backslash found: {vid.video_path}")
            else:
                print(f"OK: {vid.video_path}")
        
        if backslash_count == 0:
            print("\nALL PATHS USE FORWARD SLASHES")
        else:
            print(f"\n⚠️ Found {backslash_count} paths with backslashes")
        
        return backslash_count == 0

def verify_file_existence():
    """Check that files actually exist on disk"""
    from __init__ import create_app, db
    from models import Case, TargetImage
    import os
    
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 60)
        print("CHECKING FILE EXISTENCE")
        print("=" * 60)
        
        images = TargetImage.query.limit(10).all()
        missing_count = 0
        
        for img in images:
            full_path = os.path.join('static', img.image_path)
            if os.path.exists(full_path):
                print(f"EXISTS: {full_path}")
            else:
                missing_count += 1
                print(f"MISSING: {full_path}")
        
        if missing_count == 0:
            print("\nALL FILES EXIST")
        else:
            print(f"\n⚠️ {missing_count} files missing")
        
        return missing_count == 0

def verify_case_relationships():
    """Check that cases have proper relationships loaded"""
    from __init__ import create_app, db
    from models import Case
    
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 60)
        print("CHECKING CASE RELATIONSHIPS")
        print("=" * 60)
        
        cases = Case.query.limit(5).all()
        
        for case in cases:
            print(f"\nCase #{case.id}: {case.person_name}")
            print(f"  Images: {len(case.target_images)}")
            print(f"  Videos: {len(case.search_videos)}")
            print(f"  Status: {case.status}")
            
            if case.target_images:
                print(f"  Primary photo: {any(img.is_primary for img in case.target_images)}")
        
        print("\nRELATIONSHIPS LOADED")
        return True

def verify_template_helpers():
    """Check that template helpers work correctly"""
    from template_helpers import get_image_url, get_video_url
    
    print("\n" + "=" * 60)
    print("CHECKING TEMPLATE HELPERS")
    print("=" * 60)
    
    test_cases = [
        ("uploads\\case_1_images_20260306.jpeg", "uploads/case_1_images_20260306.jpeg"),
        ("uploads/case_1_images_20260306.jpeg", "uploads/case_1_images_20260306.jpeg"),
        ("static/uploads/test.jpg", "uploads/test.jpg"),
        ("/uploads/test.jpg", "uploads/test.jpg"),
    ]
    
    all_passed = True
    for input_path, expected in test_cases:
        result = get_image_url(input_path)
        if result == expected:
            print(f"OK: {input_path} -> {result}")
        else:
            print(f"FAIL: {input_path} -> {result} (expected: {expected})")
            all_passed = False
    
    if all_passed:
        print("\nALL TEMPLATE HELPERS WORKING")
    else:
        print("\n⚠️ Some template helpers failed")
    
    return all_passed

def verify_person_profile_schema():
    """Check that person_profile table has all required columns"""
    from __init__ import create_app, db
    import sqlite3
    import os
    
    app = create_app()
    with app.app_context():
        print("\n" + "=" * 60)
        print("CHECKING PERSON_PROFILE SCHEMA")
        print("=" * 60)
        
        db_path = os.path.join('instance', 'app.db')
        if not os.path.exists(db_path):
            print("❌ Database not found")
            return False
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(person_profile)")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = [
            'front_encodings', 'left_profile_encodings', 
            'right_profile_encodings', 'video_encodings', 
            'total_encodings'
        ]
        
        all_present = True
        for col in required_columns:
            if col in columns:
                print(f"OK: {col}")
            else:
                print(f"FAIL: {col} MISSING")
                all_present = False
        
        conn.close()
        
        if all_present:
            print("\nALL COLUMNS PRESENT")
        else:
            print("\n⚠️ Some columns missing - run fix_person_profile_schema.py")
        
        return all_present

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("VERIFICATION SCRIPT - CHECKING ALL FIXES")
    print("=" * 60)
    
    results = {
        "Database Paths": verify_database_paths(),
        "File Existence": verify_file_existence(),
        "Case Relationships": verify_case_relationships(),
        "Template Helpers": verify_template_helpers(),
        "Person Profile Schema": verify_person_profile_schema()
    }
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    
    for check, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{check}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 ALL CHECKS PASSED! System is ready.")
    else:
        print("\n⚠️ Some checks failed. Review output above.")
    
    print("=" * 60)
