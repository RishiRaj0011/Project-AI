# COMPLETE NUMPY FIX - Apply to vision_engine.py, forensic_vision_engine.py, location_matching_engine.py

# PATTERN 1: Replace all "if not face_locations:" with:
if face_locations is None or len(face_locations) == 0:
    return None

# PATTERN 2: Replace all "if not face_encodings:" with:
if face_encodings is None or len(face_encodings) == 0:
    return None

# PATTERN 3: Replace all distance extraction with:
distances = face_recognition.face_distance([target_encoding], face_encoding)
if distances is None or len(distances) == 0:
    continue
distance = float(distances[0])

# PATTERN 4: Replace compare_faces usage with:
matches = face_recognition.compare_faces(target_encodings, encoding, tolerance=0.6)
match_found = any(matches) if isinstance(matches, (list, np.ndarray)) else bool(matches)
if match_found:

# PATTERN 5: Hardcode threshold:
threshold = 0.80  # FORENSIC THRESHOLD

# PATTERN 6: tasks.py first line:
match = LocationMatch.query.get(match_id)
if not match:
    return {'success': False, 'error': 'Match not found'}

match.status = 'processing'
match.ai_analysis_started = datetime.utcnow()
db.session.commit()  # IMMEDIATE COMMIT
