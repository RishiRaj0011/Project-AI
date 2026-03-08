"""
FINAL NUMPY FIX - Find and fix ALL remaining issues
"""
import re

def scan_and_fix(filepath):
    """Scan file for ALL NumPy array issues and fix them"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        fixed_lines = []
        fixes = 0
        
        for i, line in enumerate(lines):
            original = line
            
            # Fix 1: if not face_locations:
            if 'if not face_locations:' in line:
                line = line.replace('if not face_locations:', 'if face_locations is None or len(face_locations) == 0:')
                fixes += 1
                print(f"[FIX] Line {i+1}: face_locations check")
            
            # Fix 2: if not face_encodings:
            if 'if not face_encodings:' in line:
                line = line.replace('if not face_encodings:', 'if face_encodings is None or len(face_encodings) == 0:')
                fixes += 1
                print(f"[FIX] Line {i+1}: face_encodings check")
            
            # Fix 3: if not encodings:
            if 'if not encodings:' in line and 'face_encodings' not in line:
                line = line.replace('if not encodings:', 'if encodings is None or len(encodings) == 0:')
                fixes += 1
                print(f"[FIX] Line {i+1}: encodings check")
            
            # Fix 4: if multi_view_encodings:
            if 'if multi_view_encodings:' in line and 'or' not in line:
                line = line.replace('if multi_view_encodings:', 'if multi_view_encodings is not None and len(multi_view_encodings) > 0:')
                fixes += 1
                print(f"[FIX] Line {i+1}: multi_view_encodings check")
            
            # Fix 5: if target_profiles:
            if 'if target_profiles:' in line and 'not' not in line:
                line = line.replace('if target_profiles:', 'if target_profiles is not None and len(target_profiles) > 0:')
                fixes += 1
                print(f"[FIX] Line {i+1}: target_profiles check")
            
            # Fix 6: if all_encodings:
            if 'if all_encodings:' in line:
                line = line.replace('if all_encodings:', 'if all_encodings is not None and len(all_encodings) > 0:')
                fixes += 1
                print(f"[FIX] Line {i+1}: all_encodings check")
            
            fixed_lines.append(line)
        
        if fixes > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(fixed_lines)
            print(f"[OK] {filepath}: {fixes} fixes applied\n")
            return True
        else:
            print(f"[SKIP] {filepath}: No issues found\n")
            return False
            
    except Exception as e:
        print(f"[ERROR] {filepath}: {e}\n")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("COMPREHENSIVE NUMPY FIX - Scanning all files...")
    print("=" * 60 + "\n")
    
    files = [
        "vision_engine.py",
        "forensic_vision_engine.py", 
        "location_matching_engine.py",
        "tasks.py"
    ]
    
    total_fixed = 0
    for filepath in files:
        if scan_and_fix(filepath):
            total_fixed += 1
    
    print("=" * 60)
    print(f"COMPLETE: {total_fixed}/{len(files)} files fixed")
    print("=" * 60)
    print("\n[ACTION] Restart Celery NOW:")
    print("celery -A celery_app.celery worker --loglevel=info --pool=solo")
