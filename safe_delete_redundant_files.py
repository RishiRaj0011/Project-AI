"""
Safe File Deletion Script
Removes redundant/evolutionary detector files after verification
"""
import os
import sys
import subprocess

# Files to delete (redundant person detectors)
REDUNDANT_FILES = [
    'advanced_person_detector.py',
    'ultra_advanced_person_detector.py',
    'professional_person_detector.py',
    'advanced_person_detection.py',
]

def check_imports(filename):
    """Check if file is imported anywhere in codebase"""
    print(f"\nChecking imports for: {filename}")
    
    # Remove .py extension for import search
    module_name = filename.replace('.py', '')
    
    # Search patterns
    patterns = [
        f"from {module_name}",
        f"import {module_name}",
    ]
    
    found_imports = []
    
    for pattern in patterns:
        try:
            result = subprocess.run(
                ['grep', '-r', pattern, '.', '--include=*.py'],
                capture_output=True,
                text=True
            )
            if result.stdout:
                found_imports.append(result.stdout)
        except:
            # Windows fallback - manual search
            for root, dirs, files in os.walk('.'):
                for file in files:
                    if file.endswith('.py'):
                        filepath = os.path.join(root, file)
                        try:
                            with open(filepath, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if pattern in content:
                                    found_imports.append(f"{filepath}: {pattern}")
                        except:
                            pass
    
    return found_imports

def safe_delete():
    """Safely delete redundant files after verification"""
    print("="*70)
    print("SAFE FILE DELETION - REDUNDANT DETECTOR CLEANUP")
    print("="*70)
    
    files_to_delete = []
    files_with_imports = []
    
    for filename in REDUNDANT_FILES:
        if not os.path.exists(filename):
            print(f"⚠️  {filename} - NOT FOUND (already deleted?)")
            continue
        
        imports = check_imports(filename)
        
        if imports:
            print(f"❌ {filename} - HAS IMPORTS (UNSAFE TO DELETE)")
            for imp in imports[:3]:  # Show first 3
                print(f"   {imp}")
            files_with_imports.append(filename)
        else:
            print(f"✅ {filename} - NO IMPORTS (SAFE TO DELETE)")
            files_to_delete.append(filename)
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Safe to delete: {len(files_to_delete)} files")
    print(f"Has imports: {len(files_with_imports)} files")
    
    if files_to_delete:
        print("\nFiles safe to delete:")
        for f in files_to_delete:
            print(f"  - {f}")
        
        response = input("\nProceed with deletion? (yes/no): ")
        
        if response.lower() == 'yes':
            for filename in files_to_delete:
                try:
                    os.remove(filename)
                    print(f"🗑️  Deleted: {filename}")
                except Exception as e:
                    print(f"❌ Failed to delete {filename}: {e}")
            
            print("\n✅ Cleanup completed!")
        else:
            print("\n⏸️  Deletion cancelled")
    else:
        print("\n⚠️  No files safe to delete")
    
    if files_with_imports:
        print("\n⚠️  WARNING: These files still have imports:")
        for f in files_with_imports:
            print(f"  - {f}")
        print("\nUpdate code to remove these imports before deleting.")

if __name__ == "__main__":
    safe_delete()
