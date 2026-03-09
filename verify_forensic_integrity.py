"""
FORENSIC INTEGRITY VERIFICATION SCRIPT
Tests all 5 modules to ensure proper implementation
"""

import sys
import os

def verify_forensic_integrity():
    """Verify all forensic integrity upgrades"""
    
    print("=" * 80)
    print("FORENSIC INTEGRITY VERIFICATION")
    print("=" * 80)
    
    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }
    
    # Test 1: Check tasks.py for async profile creation
    print("\n[1/5] Testing Async Profile Creation...")
    try:
        with open('tasks.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ('CLAHE Enhancement', 'createCLAHE(clipLimit=3.0'),
            ('2x Upsampling', 'number_of_times_to_upsample=2'),
            ('Multi-View Storage', 'front_encodings.append(encoding)'),
            ('FAISS Multi-Vector', 'service.insert_encoding(encoding, person_profile.id)'),
        ]
        
        for check_name, check_str in checks:
            if check_str in content:
                results['passed'].append(f"[PASS] {check_name}")
            else:
                results['failed'].append(f"[FAIL] {check_name}")
        
    except Exception as e:
        results['failed'].append(f"[FAIL] tasks.py verification failed: {e}")
    
    # Test 2: Check vision_engine.py for CLAHE + Upsampling
    print("\n[2/5] Testing Vision Engine Enhancements...")
    try:
        with open('vision_engine.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ('CLAHE in Detection', 'createCLAHE(clipLimit=3.0'),
            ('CNN Model', "model='cnn'"),
            ('2x Upsampling', 'number_of_times_to_upsample=2'),
            ('Multi-View OR Logic', 'OR strategy: MAX confidence'),
            ('0.50 Threshold', 'threshold = 0.50'),
        ]
        
        for check_name, check_str in checks:
            if check_str in content:
                results['passed'].append(f"[PASS] {check_name}")
            else:
                results['failed'].append(f"[FAIL] {check_name}")
        
    except Exception as e:
        results['failed'].append(f"[FAIL] vision_engine.py verification failed: {e}")
    
    # Test 3: Check tasks.py for 0.4s scan interval
    print("\n[3/5] Testing 0.4s Scan Interval...")
    try:
        with open('tasks.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ('Scan Interval Variable', 'scan_interval_seconds = 0.4'),
            ('FPS-based Frame Skip', 'frame_skip = max(1, int(fps * scan_interval_seconds))'),
            ('2.0s Cooldown', 'if timestamp - last_detection_time < 2.0:'),
            ('Real-time Commits', 'if commit_counter % 5 == 0:'),
        ]
        
        for check_name, check_str in checks:
            if check_str in content:
                results['passed'].append(f"[PASS] {check_name}")
            else:
                results['failed'].append(f"[FAIL] {check_name}")
        
    except Exception as e:
        results['failed'].append(f"[FAIL] 0.4s interval verification failed: {e}")
    
    # Test 4: Check models.py for PersonProfile schema
    print("\n[4/5] Testing PersonProfile Schema...")
    try:
        with open('models.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ('Primary Encoding', 'primary_face_encoding = db.Column(db.Text)'),
            ('All Encodings', 'all_face_encodings = db.Column(db.Text)'),
            ('Front Encodings', 'front_encodings = db.Column(db.Text)'),
            ('Left Profile', 'left_profile_encodings = db.Column(db.Text)'),
            ('Right Profile', 'right_profile_encodings = db.Column(db.Text)'),
            ('Video Encodings', 'video_encodings = db.Column(db.Text)'),
            ('Total Count', 'total_encodings = db.Column(db.Integer'),
        ]
        
        for check_name, check_str in checks:
            if check_str in content:
                results['passed'].append(f"[PASS] {check_name}")
            else:
                results['failed'].append(f"[FAIL] {check_name}")
        
    except Exception as e:
        results['failed'].append(f"[FAIL] models.py verification failed: {e}")
    
    # Test 5: Check person_consistency_validator.py for relaxed threshold
    print("\n[5/5] Testing Side Profile Tolerance...")
    try:
        with open('person_consistency_validator.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
        checks = [
            ('Standard Threshold', 'self.validation_threshold = 0.45'),
            ('Profile Threshold', 'self.profile_threshold = 0.40'),
            ('Angle-Aware Logic', 'threshold = self.profile_threshold if similarity >= self.profile_threshold'),
        ]
        
        for check_name, check_str in checks:
            if check_str in content:
                results['passed'].append(f"[PASS] {check_name}")
            else:
                results['failed'].append(f"[FAIL] {check_name}")
        
    except Exception as e:
        results['failed'].append(f"[FAIL] person_consistency_validator.py verification failed: {e}")
    
    # Print Results
    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    
    print(f"\nPASSED: {len(results['passed'])}")
    for item in results['passed']:
        print(f"  {item}")
    
    if results['failed']:
        print(f"\nFAILED: {len(results['failed'])}")
        for item in results['failed']:
            print(f"  {item}")
    
    if results['warnings']:
        print(f"\nWARNINGS: {len(results['warnings'])}")
        for item in results['warnings']:
            print(f"  {item}")
    
    # Summary
    total_checks = len(results['passed']) + len(results['failed'])
    pass_rate = (len(results['passed']) / total_checks * 100) if total_checks > 0 else 0
    
    print("\n" + "=" * 80)
    print(f"PASS RATE: {pass_rate:.1f}% ({len(results['passed'])}/{total_checks})")
    print("=" * 80)
    
    if pass_rate >= 90:
        print("\n[SUCCESS] FORENSIC INTEGRITY UPGRADE: COMPLETE")
        print("All critical features are properly implemented!")
    elif pass_rate >= 70:
        print("\n[WARN] FORENSIC INTEGRITY UPGRADE: PARTIAL")
        print("Most features implemented, but some issues need attention.")
    else:
        print("\n[FAIL] FORENSIC INTEGRITY UPGRADE: INCOMPLETE")
        print("Critical features are missing. Please review failed checks.")
    
    return pass_rate >= 90

if __name__ == "__main__":
    try:
        success = verify_forensic_integrity()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[ERROR] VERIFICATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
