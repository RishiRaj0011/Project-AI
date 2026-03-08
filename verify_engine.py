"""
Emergency Debug Script - Find and Fix NumPy Crash
"""
import sys
import traceback
import numpy as np
from datetime import datetime

print("=" * 80)
print("EMERGENCY DEBUG SCRIPT - FINDING NUMPY CRASH")
print("=" * 80)

# Step 1: Initialize Flask app context
print("\n[1/5] Initializing Flask app context...")
try:
    from __init__ import create_app, db
    from models import LocationMatch, Case, PersonDetection, SurveillanceFootage
    from location_matching_engine import LocationMatchingEngine
    
    app = create_app()
    app.app_context().push()
    print("SUCCESS: Flask app initialized")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 2: Get test data
print("\n[2/5] Loading test data from database...")
try:
    match = LocationMatch.query.filter_by(id=1).first()
    if not match:
        print("ERROR: No LocationMatch with id=1 found")
        print("Available matches:", [m.id for m in LocationMatch.query.all()])
        sys.exit(1)
    
    case = Case.query.filter_by(id=match.case_id).first()
    if not case:
        print(f"ERROR: No Case with id={match.case_id} found")
        sys.exit(1)
    
    footage = SurveillanceFootage.query.filter_by(id=match.footage_id).first()
    video_path = footage.video_path if footage else "Unknown"
    
    print(f"SUCCESS: Found match #{match.id} for case '{case.person_name}'")
    print(f"  Video: {video_path}")
    print(f"  Status: {match.status}")
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

# Step 3: Run analysis with detailed error tracking
print("\n[3/5] Running LocationMatchingEngine.analyze_footage_for_person()...")
print("  This will show the EXACT line where NumPy crashes...")
try:
    import warnings
    # warnings.filterwarnings('error')  # Disabled - causes SQLAlchemy warnings to crash
    
    engine = LocationMatchingEngine()
    result = engine.analyze_footage_for_person(match_id=1)
    
    print(f"SUCCESS: Analysis completed!")
    print(f"  Result type: {type(result)}")
    print(f"  Result value: {result}")
    
    if isinstance(result, dict) and result.get('detections'):
        print(f"  Detections found: {len(result['detections'])}")
        for i, det in enumerate(result['detections'][:3]):
            print(f"    Detection {i+1}: Frame {det.get('frame_number')}, Confidence {det.get('confidence')}")
    elif result == True:
        print("  Analysis returned True (check database for detections)")
    else:
        print("  WARNING: No detections found or analysis failed")
        
except ValueError as e:
    if "ambiguous" in str(e).lower():
        print("\n" + "!" * 80)
        print("FOUND IT! NumPy Array Ambiguity Error:")
        print("!" * 80)
        print(f"Error: {e}")
        print("\nFull traceback:")
        traceback.print_exc()
        print("\n" + "!" * 80)
        print("ACTION REQUIRED: Check the traceback above for the exact file and line")
        print("!" * 80)
        sys.exit(1)
    else:
        raise
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()

# Step 4: Check database for detections
print("\n[4/5] Checking database for detections...")
try:
    match = LocationMatch.query.get(1)  # Re-fetch match
    if not match:
        print("ERROR: Match not found")
        detections_in_db = []
    else:
        # Check if analysis created any detections
        detections_in_db = PersonDetection.query.filter_by(location_match_id=match.id).all()
    
        if detections_in_db and len(detections_in_db) > 0:
            print(f"SUCCESS: Found {len(detections_in_db)} detection(s) in database!")
            for i, det in enumerate(detections_in_db[:3]):
                print(f"  Detection {i+1}:")
                print(f"    ID: {det.id}")
                print(f"    Timestamp: {det.timestamp}")
                print(f"    Confidence: {det.confidence_score:.2%}")
            
            # Update match status
            match.status = 'completed'
            match.detections_count = len(detections_in_db)
            db.session.commit()
            print(f"  Match status updated to: {match.status}")
        else:
            print("INFO: No detections found in database")
            print("  This means the video was analyzed but no matches were found")
        
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
    db.session.rollback()
    sys.exit(1)

# Step 5: Verification
print("\n[5/5] Final verification...")
try:
    total_detections = PersonDetection.query.filter_by(location_match_id=1).count()
    print(f"SUCCESS: {total_detections} detection(s) in database for match #1")
    
    if total_detections > 0:
        print("\n" + "=" * 80)
        print("MISSION ACCOMPLISHED!")
        print("=" * 80)
        print("The detection should now appear on your dashboard.")
        print("Refresh the page to see the results.")
        print("=" * 80)
    else:
        print("\nINFO: Analysis completed but no matches found in video")
        print("This is normal if the person is not in the footage")
        
except Exception as e:
    print(f"FAILED: {e}")
    traceback.print_exc()
    sys.exit(1)

print("\nScript completed successfully!")
