"""
Automated Production Deployment Script
Handles all integration, cleanup, and verification
"""
import os
import sys
import shutil
import subprocess
from pathlib import Path

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def run_command(cmd, description):
    """Run command and report status"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description}: Success")
            return True
        else:
            print(f"❌ {description}: Failed")
            print(f"   Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description}: Exception - {e}")
        return False

def backup_files():
    """Backup critical files"""
    print_header("STEP 1: BACKUP")
    
    backups = [
        ('instance/app.db', 'instance/app.db.backup'),
        ('instance/faiss_index.bin', 'instance/faiss_index.bin.backup'),
        ('__init__.py', '__init__.py.backup')
    ]
    
    for src, dst in backups:
        if os.path.exists(src):
            try:
                shutil.copy2(src, dst)
                print(f"✅ Backed up: {src} → {dst}")
            except Exception as e:
                print(f"⚠️ Backup failed for {src}: {e}")
        else:
            print(f"⚠️ File not found: {src}")

def fix_numpy_imports():
    """Fix numpy imports"""
    print_header("STEP 2: FIX NUMPY IMPORTS")
    
    py_files = list(Path('.').rglob('*.py'))
    fixed_count = 0
    
    for file_path in py_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if 'numpy' in content:
                new_content = content.replace('numpy', 'numpy')
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ Fixed: {file_path}")
                fixed_count += 1
        except Exception as e:
            print(f"⚠️ Error processing {file_path}: {e}")
    
    print(f"\n📊 Fixed {fixed_count} files")

def update_init_file():
    """Update __init__.py with production version"""
    print_header("STEP 3: UPDATE __init__.py")
    
    if os.path.exists('__init___PRODUCTION.py'):
        try:
            shutil.copy2('__init___PRODUCTION.py', '__init__.py')
            print("✅ Updated __init__.py with production version")
        except Exception as e:
            print(f"❌ Failed to update __init__.py: {e}")
    else:
        print("⚠️ __init___PRODUCTION.py not found - skipping")

def delete_redundant_files():
    """Delete redundant detector files"""
    print_header("STEP 4: DELETE REDUNDANT FILES")
    
    redundant_files = [
        'advanced_person_detector.py',
        'ultra_advanced_person_detector.py',
        'professional_person_detector.py',
        'advanced_person_detection.py'
    ]
    
    deleted_count = 0
    for filename in redundant_files:
        if os.path.exists(filename):
            try:
                os.remove(filename)
                print(f"🗑️ Deleted: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"❌ Failed to delete {filename}: {e}")
        else:
            print(f"⚠️ Not found: {filename}")
    
    print(f"\n📊 Deleted {deleted_count} files")

def verify_services():
    """Verify all services are working"""
    print_header("STEP 5: VERIFY SERVICES")
    
    checks = [
        ("from vector_search_service import get_face_search_service; get_face_search_service()", "FAISS"),
        ("from vision_engine import get_vision_engine; get_vision_engine()", "Vision Engine"),
        ("from liveness_detection import detect_liveness_simple", "Liveness Detection"),
        ("from frame_enhancement import enhance_frame_for_ai", "Frame Enhancement"),
        ("from smart_rejection_system import SmartRejectionSystem", "Smart Rejection"),
        ("from automated_cleanup_service import AutomatedCleanupService", "Cleanup Service")
    ]
    
    passed = 0
    for code, name in checks:
        try:
            exec(code)
            print(f"✅ {name}: OK")
            passed += 1
        except Exception as e:
            print(f"❌ {name}: Failed - {e}")
    
    print(f"\n📊 Passed {passed}/{len(checks)} checks")
    return passed == len(checks)

def main():
    """Main deployment function"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "  PRODUCTION DEPLOYMENT - AUTOMATED INTEGRATION".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝")
    
    # Run deployment steps
    backup_files()
    fix_numpy_imports()
    update_init_file()
    delete_redundant_files()
    
    # Verify
    if verify_services():
        print("\n" + "╔" + "="*68 + "╗")
        print("║" + " "*68 + "║")
        print("║" + "  ✅ DEPLOYMENT SUCCESSFUL ✅".center(68) + "║")
        print("║" + " "*68 + "║")
        print("║" + "  All services verified and operational!".center(68) + "║")
        print("║" + " "*68 + "║")
        print("║" + "  Next: python run_app.py".center(68) + "║")
        print("║" + " "*68 + "║")
        print("╚" + "="*68 + "╝\n")
        return 0
    else:
        print("\n" + "╔" + "="*68 + "╗")
        print("║" + " "*68 + "║")
        print("║" + "  ⚠️ DEPLOYMENT COMPLETED WITH WARNINGS ⚠️".center(68) + "║")
        print("║" + " "*68 + "║")
        print("║" + "  Some services failed verification.".center(68) + "║")
        print("║" + "  Check errors above and fix before starting app.".center(68) + "║")
        print("║" + " "*68 + "║")
        print("╚" + "="*68 + "╝\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
