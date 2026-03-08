"""Test to find exact error location"""
import sys
import traceback

try:
    from location_matching_engine import location_engine
    print("[OK] location_matching_engine imported")
    
    # Simulate the analysis call
    print("[TEST] Testing analyze_footage_for_person...")
    
    # This will help us see the exact line
    result = location_engine.analyze_footage_for_person(1)
    print(f"[RESULT] {result}")
    
except Exception as e:
    print(f"[ERROR] {e}")
    print("\n[TRACEBACK]")
    traceback.print_exc()
    
    # Get the exact line
    tb = sys.exc_info()[2]
    while tb.tb_next:
        tb = tb.tb_next
    frame = tb.tb_frame
    print(f"\n[EXACT ERROR]")
    print(f"File: {frame.f_code.co_filename}")
    print(f"Function: {frame.f_code.co_name}")
    print(f"Line: {tb.tb_lineno}")
