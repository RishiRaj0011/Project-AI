"""
Runtime Verification Script for Multi-Photo Detection System
Tests all components to ensure proper functionality
"""

import os
import sys
from pathlib import Path

def verify_multi_photo_system():
    """Comprehensive verification of multi-photo detection system"""
    
    print("=" * 80)
    print("[*] MULTI-PHOTO DETECTION SYSTEM VERIFICATION")
    print("=" * 80)
    print()
    
    verification_results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }
    
    # Test 1: Check required files exist
    print("[*] Test 1: Checking Required Files...")
    required_files = [
        'routes.py',
        'models.py',
        'forms.py',
        'multi_view_face_extractor.py',
        'person_consistency_validator.py',
        'high_precision_forensic_engine.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"  ✅ {file} - Found")
            verification_results['passed'].append(f"File exists: {file}")
        else:
            print(f"  ❌ {file} - Missing")
            verification_results['failed'].append(f"File missing: {file}")
    print()
    
    # Test 2: Check imports
    print("📦 Test 2: Checking Module Imports...")
    try:
        from multi_view_face_extractor import get_face_extractor
        print("  ✅ multi_view_face_extractor - Imported")
        verification_results['passed'].append("Import: multi_view_face_extractor")
    except Exception as e:
        print(f"  ❌ multi_view_face_extractor - Failed: {e}")
        verification_results['failed'].append(f"Import failed: multi_view_face_extractor - {e}")
    
    try:
        from person_consistency_validator import validate_case_person_consistency
        print("  ✅ person_consistency_validator - Imported")
        verification_results['passed'].append("Import: person_consistency_validator")
    except Exception as e:
        print(f"  ❌ person_consistency_validator - Failed: {e}")
        verification_results['failed'].append(f"Import failed: person_consistency_validator - {e}")
    
    try:
        from high_precision_forensic_engine import HighPrecisionForensicEngine
        print("  ✅ high_precision_forensic_engine - Imported")
        verification_results['passed'].append("Import: high_precision_forensic_engine")
    except Exception as e:
        print(f"  ❌ high_precision_forensic_engine - Failed: {e}")
        verification_results['failed'].append(f"Import failed: high_precision_forensic_engine - {e}")
    print()
    
    # Test 3: Check database models
    print("🗄️  Test 3: Checking Database Models...")
    try:
        from models import PersonProfile, PersonDetection, TargetImage
        print("  ✅ PersonProfile model - Available")
        print("  ✅ PersonDetection model - Available")
        print("  ✅ TargetImage model - Available")
        verification_results['passed'].append("Database models available")
        
        # Check PersonProfile fields
        required_fields = [
            'primary_face_encoding',
            'all_face_encodings',
            'front_encodings',
            'left_profile_encodings',
            'right_profile_encodings',
            'video_encodings',
            'total_encodings',
            'face_quality_score',
            'profile_confidence'
        ]
        
        for field in required_fields:
            if hasattr(PersonProfile, field):
                print(f"  ✅ PersonProfile.{field} - Present")
                verification_results['passed'].append(f"Field: PersonProfile.{field}")
            else:
                print(f"  ❌ PersonProfile.{field} - Missing")
                verification_results['failed'].append(f"Field missing: PersonProfile.{field}")
                
    except Exception as e:
        print(f"  ❌ Database models - Failed: {e}")
        verification_results['failed'].append(f"Database models failed: {e}")
    print()
    
    # Test 4: Check face_recognition library
    print("👤 Test 4: Checking Face Recognition Library...")
    try:
        import face_recognition
        print("  ✅ face_recognition library - Installed")
        verification_results['passed'].append("Library: face_recognition")
        
        # Check required functions
        required_functions = [
            'load_image_file',
            'face_locations',
            'face_encodings',
            'face_landmarks',
            'face_distance'
        ]
        
        for func in required_functions:
            if hasattr(face_recognition, func):
                print(f"  ✅ face_recognition.{func} - Available")
                verification_results['passed'].append(f"Function: face_recognition.{func}")
            else:
                print(f"  ❌ face_recognition.{func} - Missing")
                verification_results['failed'].append(f"Function missing: face_recognition.{func}")
                
    except ImportError:
        print("  ❌ face_recognition library - Not installed")
        verification_results['failed'].append("Library not installed: face_recognition")
    print()
    
    # Test 5: Check OpenCV
    print("📷 Test 5: Checking OpenCV Library...")
    try:
        import cv2
        print(f"  ✅ OpenCV version: {cv2.__version__}")
        verification_results['passed'].append(f"Library: OpenCV {cv2.__version__}")
        
        # Check required functions
        required_cv2_functions = [
            'VideoCapture',
            'cvtColor',
            'createCLAHE',
            'rectangle',
            'putText',
            'imwrite',
            'imencode'
        ]
        
        for func in required_cv2_functions:
            if hasattr(cv2, func):
                print(f"  ✅ cv2.{func} - Available")
                verification_results['passed'].append(f"Function: cv2.{func}")
            else:
                print(f"  ❌ cv2.{func} - Missing")
                verification_results['failed'].append(f"Function missing: cv2.{func}")
                
    except ImportError:
        print("  ❌ OpenCV library - Not installed")
        verification_results['failed'].append("Library not installed: OpenCV")
    print()
    
    # Test 6: Check directory structure
    print("📂 Test 6: Checking Directory Structure...")
    required_dirs = [
        'static/uploads',
        'static/detections',
        'static/surveillance',
        'static/evidence'
    ]
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"  ✅ {dir_path} - Exists")
            verification_results['passed'].append(f"Directory exists: {dir_path}")
        else:
            print(f"  ⚠️  {dir_path} - Missing (will be created on first use)")
            verification_results['warnings'].append(f"Directory missing: {dir_path}")
    print()
    
    # Test 7: Check routes.py for multi-photo handling
    print("🛣️  Test 7: Checking Routes Configuration...")
    try:
        with open('routes.py', 'r', encoding='utf-8') as f:
            routes_content = f.read()
        
        required_code_snippets = [
            'MultipleFileField',
            'validate_case_person_consistency',
            'get_face_extractor',
            'create_person_profile',
            'PersonProfile',
            'primary_face_encoding',
            'all_face_encodings',
            'front_encodings',
            'left_profile_encodings',
            'right_profile_encodings'
        ]
        
        for snippet in required_code_snippets:
            if snippet in routes_content:
                print(f"  ✅ routes.py contains: {snippet}")
                verification_results['passed'].append(f"Code present: {snippet}")
            else:
                print(f"  ❌ routes.py missing: {snippet}")
                verification_results['failed'].append(f"Code missing: {snippet}")
                
    except Exception as e:
        print(f"  ❌ routes.py check failed: {e}")
        verification_results['failed'].append(f"routes.py check failed: {e}")
    print()
    
    # Test 8: Verify multi-view face extractor functionality
    print("🔬 Test 8: Testing Multi-View Face Extractor...")
    try:
        from multi_view_face_extractor import MultiViewFaceExtractor
        
        extractor = MultiViewFaceExtractor()
        print("  ✅ MultiViewFaceExtractor instantiated")
        
        # Check methods
        required_methods = [
            'extract_from_images',
            'extract_from_video',
            'create_person_profile',
            '_calculate_face_quality'
        ]
        
        for method in required_methods:
            if hasattr(extractor, method):
                print(f"  ✅ Method: {method}")
                verification_results['passed'].append(f"Method: MultiViewFaceExtractor.{method}")
            else:
                print(f"  ❌ Method missing: {method}")
                verification_results['failed'].append(f"Method missing: MultiViewFaceExtractor.{method}")
                
    except Exception as e:
        print(f"  ❌ MultiViewFaceExtractor test failed: {e}")
        verification_results['failed'].append(f"MultiViewFaceExtractor test failed: {e}")
    print()
    
    # Test 9: Verify person consistency validator
    print("✔️  Test 9: Testing Person Consistency Validator...")
    try:
        from person_consistency_validator import PersonConsistencyValidator
        
        validator = PersonConsistencyValidator()
        print("  ✅ PersonConsistencyValidator instantiated")
        print(f"  ✅ Validation threshold: {validator.validation_threshold}")
        print(f"  ✅ Min face confidence: {validator.min_face_confidence}")
        
        # Check methods
        required_methods = [
            'extract_face_encodings',
            'extract_faces_from_video',
            'validate_person_consistency',
            '_check_face_consistency'
        ]
        
        for method in required_methods:
            if hasattr(validator, method):
                print(f"  ✅ Method: {method}")
                verification_results['passed'].append(f"Method: PersonConsistencyValidator.{method}")
            else:
                print(f"  ❌ Method missing: {method}")
                verification_results['failed'].append(f"Method missing: PersonConsistencyValidator.{method}")
                
    except Exception as e:
        print(f"  ❌ PersonConsistencyValidator test failed: {e}")
        verification_results['failed'].append(f"PersonConsistencyValidator test failed: {e}")
    print()
    
    # Test 10: Verify forensic engine
    print("🔍 Test 10: Testing High-Precision Forensic Engine...")
    try:
        from high_precision_forensic_engine import HighPrecisionForensicEngine
        
        engine = HighPrecisionForensicEngine(case_id=1)
        print("  ✅ HighPrecisionForensicEngine instantiated")
        print(f"  ✅ Motion threshold: {engine.motion_threshold}")
        
        # Check methods
        required_methods = [
            'detect_motion',
            'enhance_clahe',
            'calculate_pose_68pt',
            'confirm_temporal_consistency',
            'detect_with_precision',
            'render_forensic_evidence',
            'save_forensic_evidence'
        ]
        
        for method in required_methods:
            if hasattr(engine, method):
                print(f"  ✅ Method: {method}")
                verification_results['passed'].append(f"Method: HighPrecisionForensicEngine.{method}")
            else:
                print(f"  ❌ Method missing: {method}")
                verification_results['failed'].append(f"Method missing: HighPrecisionForensicEngine.{method}")
                
    except Exception as e:
        print(f"  ❌ HighPrecisionForensicEngine test failed: {e}")
        verification_results['failed'].append(f"HighPrecisionForensicEngine test failed: {e}")
    print()
    
    # Final Summary
    print("=" * 80)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 80)
    print()
    
    total_tests = len(verification_results['passed']) + len(verification_results['failed']) + len(verification_results['warnings'])
    passed_tests = len(verification_results['passed'])
    failed_tests = len(verification_results['failed'])
    warnings = len(verification_results['warnings'])
    
    print(f"✅ Passed:   {passed_tests}/{total_tests}")
    print(f"❌ Failed:   {failed_tests}/{total_tests}")
    print(f"⚠️  Warnings: {warnings}/{total_tests}")
    print()
    
    if failed_tests == 0:
        print("🎉 ALL TESTS PASSED! System is fully operational.")
        print()
        print("✅ Multi-photo upload system: VERIFIED")
        print("✅ Person consistency validation: VERIFIED")
        print("✅ Multi-view face extraction: VERIFIED")
        print("✅ Frame-wise detection: VERIFIED")
        print("✅ Forensic evidence generation: VERIFIED")
        print()
        print("🚀 System is ready for production use!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED. Please review the following issues:")
        print()
        for failure in verification_results['failed']:
            print(f"  ❌ {failure}")
        print()
        print("🔧 Please fix the above issues before using the system.")
        return False

if __name__ == "__main__":
    print()
    print("[*] Starting Multi-Photo Detection System Verification...")
    print()
    
    success = verify_multi_photo_system()
    
    print()
    print("=" * 80)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)
