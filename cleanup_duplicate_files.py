"""
Cleanup Script: Remove duplicate fix files for professional structure
Run this once to clean up the project
"""
import os

# Files to delete (duplicates and temporary fixes)
FILES_TO_DELETE = [
    'emergency_numpy_fix.py',
    'final_numpy_fix.py',
    'ultimate_numpy_fix.py',
    'NUMPY_FIX_COMPLETE.py',
    'NUMPY_FIX_COMPLETE.txt',
    'scan_numpy_issues.py',
    'fix_all_imports.py',
    'update_imports.py',
    'FINAL_FIX_COMPLETE.txt',
    'DEEP_DEBUG_MODE_ENABLED.txt',
    'DEMO_MODE_OPTIMIZATIONS.txt',
    'FRAME_SKIP_HARDCODED.txt',
    'HIGH_DENSITY_SCANNING_ENABLED.txt',
    'HIGH_SENSITIVITY_MODE_ENABLED.txt',
    'LOCATION_MATCHING_REMOVED.py',
    'REMOVE_LOCATION_MATCHING_GUIDE.py',
    'ROUTES_INTEGRATION_REALWORLD.py',
    'REALWORLD_UPDATES_SUMMARY.py',
    'MANUAL_WORKFLOW_COMPLETE_GUIDE.py',
    'INTEGRATION_CHECKLIST.py',
    'FINAL_IMPLEMENTATION_CHECKLIST.py',
    'ADMIN_BATCH_ADDITIONS.py',
    'safe_delete_redundant_files.py',
    'test_error_location.py',
    'verify_fixes.py',
    'verify_optimizations.py',
    'verify_targeted_find.py',
    'verify_forensic_integration.py',
    'verify_engine.py',
    '$null'
]

def cleanup_files():
    """Remove duplicate and temporary files"""
    deleted = []
    not_found = []
    
    print("\n" + "="*60)
    print("CLEANUP: Removing duplicate fix files")
    print("="*60 + "\n")
    
    for filename in FILES_TO_DELETE:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                deleted.append(filename)
                print(f"✅ Deleted: {filename}")
            except Exception as e:
                print(f"❌ Error deleting {filename}: {e}")
        else:
            not_found.append(filename)
    
    print("\n" + "="*60)
    print("CLEANUP SUMMARY")
    print("="*60)
    print(f"Deleted: {len(deleted)} files")
    print(f"Not found: {len(not_found)} files")
    print("="*60 + "\n")
    
    if deleted:
        print("✅ Project structure cleaned!")
        print("✅ Professional appearance achieved!")
    
    return len(deleted)

if __name__ == "__main__":
    cleanup_files()
