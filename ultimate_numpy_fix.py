"""
ULTIMATE NUMPY FIX - Replace ALL problematic patterns
"""

def ultimate_fix(filepath):
    """Apply ALL possible NumPy fixes"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original = content
        fixes = []
        
        # Pattern 1: if not X: where X could be array
        patterns = [
            ('if not face_locations:', 'if face_locations is None or len(face_locations) == 0:'),
            ('if not face_encodings:', 'if face_encodings is None or len(face_encodings) == 0:'),
            ('if not encodings:', 'if encodings is None or len(encodings) == 0:'),
            ('if not target_encodings:', 'if target_encodings is None or len(target_encodings) == 0:'),
            ('if not all_encodings:', 'if all_encodings is None or len(all_encodings) == 0:'),
            ('if not matches:', 'if matches is None or len(matches) == 0:'),
            ('if not distances:', 'if distances is None or len(distances) == 0:'),
        ]
        
        # Pattern 2: if X: where X could be array (positive check)
        positive_patterns = [
            ('if face_locations:', 'if face_locations is not None and len(face_locations) > 0:'),
            ('if face_encodings:', 'if face_encodings is not None and len(face_encodings) > 0:'),
            ('if encodings:', 'if encodings is not None and len(encodings) > 0:'),
            ('if target_encodings:', 'if target_encodings is not None and len(target_encodings) > 0:'),
            ('if all_encodings:', 'if all_encodings is not None and len(all_encodings) > 0:'),
            ('if multi_view_encodings:', 'if multi_view_encodings is not None and len(multi_view_encodings) > 0:'),
            ('if target_profiles:', 'if target_profiles is not None and len(target_profiles) > 0:'),
            ('if matches:', 'if matches is not None and len(matches) > 0:'),
            ('if distances:', 'if distances is not None and len(distances) > 0:'),
        ]
        
        # Apply negative patterns
        for old, new in patterns:
            if old in content:
                content = content.replace(old, new)
                fixes.append(f"Fixed: {old}")
        
        # Apply positive patterns (but avoid already fixed ones)
        for old, new in positive_patterns:
            # Only replace if not already part of a compound condition
            if old in content and ' and ' not in content[content.find(old):content.find(old)+100]:
                content = content.replace(old, new)
                fixes.append(f"Fixed: {old}")
        
        if fixes:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] {filepath}:")
            for fix in fixes:
                print(f"  - {fix}")
            print()
            return True
        else:
            print(f"[SKIP] {filepath}: Already fixed\n")
            return False
            
    except Exception as e:
        print(f"[ERROR] {filepath}: {e}\n")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("ULTIMATE NUMPY FIX - Fixing ALL array checks")
    print("=" * 70 + "\n")
    
    files = ["vision_engine.py", "forensic_vision_engine.py", "location_matching_engine.py", "tasks.py"]
    
    fixed = sum(1 for f in files if ultimate_fix(f))
    
    print("=" * 70)
    print(f"DONE: {fixed}/{len(files)} files modified")
    print("=" * 70)
    print("\n[CRITICAL] Restart Celery:")
    print("celery -A celery_app.celery worker --loglevel=info --pool=solo\n")
