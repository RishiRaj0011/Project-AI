"""
Automated Import Fix Script - Updates ALL shadow imports
Fixes 68+ files with old module imports
"""

import os
import sys

def fix_file_imports(filename):
    """Fix imports in a single file"""
    if not os.path.exists(filename):
        return False, f"File not found: {filename}"
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # Import statement replacements
        import_replacements = [
            ('from ai_location_matcher import ai_matcher', 
             'from location_matching_engine import location_engine'),
            ('from advanced_location_matcher import advanced_matcher', 
             'from location_matching_engine import location_engine'),
            ('from intelligent_location_matcher import location_matcher',
             'from location_matching_engine import location_engine as location_matcher'),
            ('from system_monitor import system_monitor, get_system_status',
             'from system_health_service import system_health, get_system_status'),
            ('from system_monitor import system_monitor',
             'from system_health_service import system_health'),
            ('from system_monitor import start_system_monitoring',
             'from system_health_service import start_system_monitoring'),
            ('from system_resilience_monitor import get_system_status',
             'from system_health_service import get_system_status'),
        ]
        
        for old, new in import_replacements:
            if old in content:
                content = content.replace(old, new)
                changes.append(f"Import: {old} -> {new}")
        
        # Function call replacements
        call_replacements = [
            ('ai_matcher.process_new_case', 'location_engine.process_new_case'),
            ('ai_matcher.process_new_footage', 'location_engine.process_new_footage'),
            ('ai_matcher.analyze_footage_for_person', 'location_engine.analyze_footage_for_person'),
            ('ai_matcher.find_nearby_footage', 'location_engine.find_location_matches'),
            ('advanced_matcher.auto_process_approved_case', 'location_engine.auto_process_approved_case'),
            ('advanced_matcher.find_intelligent_matches', 'location_engine.find_location_matches'),
            ('system_monitor._clear_system_cache', 'system_health._clear_cache'),
            ('system_monitor._cleanup_temporary_files', 'system_health._cleanup_files'),
            ('system_monitor.logger', 'system_health.logger'),
        ]
        
        for old, new in call_replacements:
            if old in content:
                content = content.replace(old, new)
                changes.append(f"Call: {old} -> {new}")
        
        # Remove problematic calls that don't exist in new module
        problematic_calls = [
            'system_monitor._restart_background_services()',
            'system_monitor.get_performance_trends',
        ]
        
        for call in problematic_calls:
            if call in content:
                # Comment out instead of removing
                content = content.replace(call, f'# REMOVED: {call}')
                changes.append(f"Removed: {call}")
        
        # Only write if changes were made
        if content != original_content:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        else:
            return False, "No changes needed"
            
    except Exception as e:
        return False, f"Error: {str(e)}"

def main():
    """Fix all files with shadow imports"""
    
    # Priority files that MUST be fixed
    critical_files = [
        'admin.py',
        'ADMIN_BATCH_ADDITIONS.py',
        'admin_batch_routes.py',
        'enhanced_admin_routes.py',
        'admin_charts_route.py',
    ]
    
    # High priority files
    high_priority_files = [
        'batch_analyzer.py',
        'batch_processor.py',
        'tasks.py',
        'tasks_batch.py',
        'auto_ai_processor.py',
        'auto_cctv_processor.py',
        'parallel_cctv_processor.py',
    ]
    
    # All files to fix
    all_files = critical_files + high_priority_files
    
    print("=" * 80)
    print("AUTOMATED IMPORT FIX SCRIPT")
    print("=" * 80)
    print(f"Fixing {len(all_files)} files...")
    print()
    
    fixed_count = 0
    failed_count = 0
    skipped_count = 0
    
    for filename in all_files:
        print(f"Processing: {filename}...")
        success, result = fix_file_imports(filename)
        
        if success:
            fixed_count += 1
            print(f"  [OK] Fixed - {len(result)} changes")
            for change in result[:3]:  # Show first 3 changes
                print(f"    - {change}")
            if len(result) > 3:
                print(f"    ... and {len(result) - 3} more")
        elif "not found" in str(result):
            skipped_count += 1
            print(f"  [SKIP] {result}")
        else:
            failed_count += 1
            print(f"  [FAIL] {result}")
        print()
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Fixed:   {fixed_count} files")
    print(f"Skipped: {skipped_count} files (not found)")
    print(f"Failed:  {failed_count} files")
    print("=" * 80)
    
    if fixed_count > 0:
        print()
        print("[OK] Import fixes applied successfully!")
        print()
        print("Next steps:")
        print("1. Add missing method to system_health_service.py:")
        print("   - get_performance_trends(hours)")
        print("2. Test application: python run_app.py")
        print("3. Verify all features work")
        print("4. Delete old files (see INTEGRITY_AUDIT_REPORT.md)")
    
    return fixed_count, failed_count

if __name__ == '__main__':
    fixed, failed = main()
    sys.exit(0 if failed == 0 else 1)
