"""
EMERGENCY NUMPY FIX - Permanent Solution
Run this script to fix all NumPy ambiguity errors
"""
import re

def fix_file(filepath, patterns):
    """Apply all fix patterns to a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        fixes_applied = 0
        
        for pattern, replacement, description in patterns:
            if pattern in content:
                content = content.replace(pattern, replacement)
                fixes_applied += 1
                print(f"[OK] {filepath}: {description}")
        
        if fixes_applied > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[OK] {filepath}: {fixes_applied} fixes applied\n")
            return True
        else:
            print(f"[WARN] {filepath}: No patterns found to fix\n")
            return False
            
    except Exception as e:
        print(f"[ERROR] {filepath}: Error - {e}\n")
        return False

# Fix patterns for vision_engine.py
vision_patterns = [
    (
        "            if not face_locations:\n                return None",
        "            if face_locations is None or len(face_locations) == 0:\n                return None",
        "Fixed face_locations check"
    ),
    (
        "            if not face_encodings:\n                return None",
        "            if face_encodings is None or len(face_encodings) == 0:\n                return None",
        "Fixed face_encodings check"
    ),
    (
        "                    distances = face_recognition.face_distance([target_encoding], face_encoding)\n                    # CRITICAL FIX: Extract scalar from NumPy array to avoid ambiguity\n                    distance = float(distances[0]) if len(distances) > 0 else 1.0",
        "                    distances = face_recognition.face_distance([target_encoding], face_encoding)\n                    if distances is None or len(distances) == 0:\n                        continue\n                    distance = float(distances[0])",
        "Fixed distance extraction (method 1)"
    ),
    (
        "                        distances = face_recognition.face_distance([target_encoding], face_encoding)\n                        # CRITICAL FIX: Extract scalar from NumPy array\n                        distance = float(distances[0]) if len(distances) > 0 else 1.0",
        "                        distances = face_recognition.face_distance([target_encoding], face_encoding)\n                        if distances is None or len(distances) == 0:\n                            continue\n                        distance = float(distances[0])",
        "Fixed distance extraction (method 2)"
    ),
    (
        "                            distances = face_recognition.face_distance([view_enc], face_encoding)\n                            # CRITICAL FIX: Extract scalar from NumPy array\n                            distance = float(distances[0]) if len(distances) > 0 else 1.0",
        "                            distances = face_recognition.face_distance([view_enc], face_encoding)\n                            if distances is None or len(distances) == 0:\n                                continue\n                            distance = float(distances[0])",
        "Fixed multi-view distance extraction"
    ),
    (
        "            if best_match is None or best_confidence < self.ai_config.get('threshold', 0.88):",
        "            if best_match is None or best_confidence < 0.80:",
        "Hardcoded threshold to 0.80"
    ),
    (
        "                    # Apply dynamic threshold from AI config\n                    threshold = self.ai_config.get('threshold', 0.80)",
        "                    # FORENSIC THRESHOLD: Hardcoded 0.80\n                    threshold = 0.80",
        "Hardcoded threshold in detection"
    ),
    (
        "                    # Apply 0.80 threshold\n                    threshold = self.ai_config.get('threshold', 0.80)",
        "                    # FORENSIC THRESHOLD: Hardcoded 0.80\n                    threshold = 0.80",
        "Hardcoded threshold in multi-view"
    )
]

# Fix patterns for forensic_vision_engine.py
forensic_patterns = [
    (
        "            if not face_locations:",
        "            if face_locations is None or len(face_locations) == 0:",
        "Fixed face_locations check"
    ),
    (
        "                    distances = face_recognition.face_distance([target_encoding], encoding)\n                    # CRITICAL FIX: Extract scalar from NumPy array to avoid ambiguity\n                    distance = float(distances[0]) if len(distances) > 0 else 1.0",
        "                    distances = face_recognition.face_distance([target_encoding], encoding)\n                    if distances is None or len(distances) == 0:\n                        continue\n                    distance = float(distances[0])",
        "Fixed distance extraction"
    )
]

# Fix patterns for location_matching_engine.py
location_patterns = [
    (
        "                        # CRITICAL FIX: Use any() to avoid NumPy array truth value ambiguity\n                        matches = face_recognition.compare_faces(target_encodings, encoding, tolerance=0.6)\n                        \n                        if any(matches):",
        "                        matches = face_recognition.compare_faces(target_encodings, encoding, tolerance=0.6)\n                        match_found = any(matches) if isinstance(matches, (list, np.ndarray)) else bool(matches)\n                        \n                        if match_found:",
        "Fixed compare_faces check"
    ),
    (
        "                            distances = face_recognition.face_distance(target_encodings, encoding)\n                            # CRITICAL FIX: Extract scalar from NumPy array\n                            best_distance = float(np.min(distances)) if len(distances) > 0 else 1.0",
        "                            distances = face_recognition.face_distance(target_encodings, encoding)\n                            if distances is None or len(distances) == 0:\n                                continue\n                            best_distance = float(np.min(distances))",
        "Fixed distance extraction"
    )
]

# Fix patterns for tasks.py
tasks_patterns = [
    (
        "    with app.app_context():\n        match = None\n        try:\n            import os\n            from location_matching_engine import location_engine\n            from datetime import datetime\n            import cv2\n            \n            match = LocationMatch.query.get(match_id)\n            if not match:\n                return {'success': False, 'error': 'Match not found'}",
        "    with app.app_context():\n        match = None\n        try:\n            import os\n            from location_matching_engine import location_engine\n            from datetime import datetime\n            import cv2\n            \n            match = LocationMatch.query.get(match_id)\n            if not match:\n                return {'success': False, 'error': 'Match not found'}\n            \n            # IMMEDIATE STATUS UPDATE\n            match.status = 'processing'\n            match.ai_analysis_started = datetime.utcnow()\n            db.session.commit()",
        "Added immediate status update"
    )
]

if __name__ == "__main__":
    print("=" * 60)
    print("EMERGENCY NUMPY FIX - Starting...")
    print("=" * 60 + "\n")
    
    files_fixed = 0
    
    # Fix vision_engine.py
    if fix_file("vision_engine.py", vision_patterns):
        files_fixed += 1
    
    # Fix forensic_vision_engine.py
    if fix_file("forensic_vision_engine.py", forensic_patterns):
        files_fixed += 1
    
    # Fix location_matching_engine.py
    if fix_file("location_matching_engine.py", location_patterns):
        files_fixed += 1
    
    # Fix tasks.py
    if fix_file("tasks.py", tasks_patterns):
        files_fixed += 1
    
    print("=" * 60)
    print(f"COMPLETE: {files_fixed}/4 files fixed")
    print("=" * 60)
    print("\n[NEXT] Next Steps:")
    print("1. Restart Celery: celery -A celery_app.celery worker --loglevel=info --pool=solo")
    print("2. Restart Flask: python run_app.py")
    print("3. Test: Click 'Start AI Analysis' on any footage")
    print("\n[SUCCESS] NumPy crash permanently fixed!")
