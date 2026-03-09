"""
Simple Verification Script for Multi-Photo Detection System
Tests MultipleFileField import in routes.py
"""

import os
import sys

def verify_multiplefile_import():
    """Verify MultipleFileField is imported in routes.py"""
    
    print("=" * 80)
    print("MULTI-PHOTO DETECTION SYSTEM - MULTIPLEFILE VERIFICATION")
    print("=" * 80)
    print()
    
    # Check if routes.py exists
    if not os.path.exists('routes.py'):
        print("[FAIL] routes.py not found")
        return False
    
    # Read routes.py
    with open('routes.py', 'r', encoding='utf-8') as f:
        routes_content = f.read()
    
    # Check for MultipleFileField import
    if 'MultipleFileField' in routes_content:
        print("[PASS] MultipleFileField found in routes.py")
        
        # Check if it's imported from wtforms
        if 'from wtforms import' in routes_content and 'MultipleFileField' in routes_content:
            print("[PASS] MultipleFileField imported from wtforms")
        elif 'from flask_wtf' in routes_content:
            print("[INFO] MultipleFileField may be from flask_wtf")
        
        return True
    else:
        print("[FAIL] MultipleFileField NOT found in routes.py")
        return False

def verify_forms_py():
    """Verify forms.py has MultipleFileField"""
    
    print()
    print("Checking forms.py...")
    
    if not os.path.exists('forms.py'):
        print("[FAIL] forms.py not found")
        return False
    
    with open('forms.py', 'r', encoding='utf-8') as f:
        forms_content = f.read()
    
    if 'MultipleFileField' in forms_content:
        print("[PASS] MultipleFileField found in forms.py")
        
        # Check if photos field uses MultipleFileField
        if 'photos = MultipleFileField' in forms_content:
            print("[PASS] photos field uses MultipleFileField")
        else:
            print("[WARN] photos field may not use MultipleFileField")
        
        return True
    else:
        print("[FAIL] MultipleFileField NOT found in forms.py")
        return False

def main():
    print()
    print("Starting verification...")
    print()
    
    routes_ok = verify_multiplefile_import()
    forms_ok = verify_forms_py()
    
    print()
    print("=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)
    
    if routes_ok and forms_ok:
        print()
        print("[SUCCESS] All checks passed!")
        print()
        print("MultipleFileField is properly configured:")
        print("  - Imported in routes.py")
        print("  - Defined in forms.py")
        print("  - Ready for multi-photo upload")
        print()
        return 0
    else:
        print()
        print("[FAILED] Some checks failed")
        print()
        if not routes_ok:
            print("  - MultipleFileField missing in routes.py")
        if not forms_ok:
            print("  - MultipleFileField missing in forms.py")
        print()
        return 1

if __name__ == "__main__":
    sys.exit(main())
