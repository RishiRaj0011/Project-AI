"""
Automated Import Update Script
Updates admin.py to use consolidated modules
"""

import re

def update_admin_imports():
    """Update all imports in admin.py to use new consolidated modules"""
    
    admin_file = 'd:\\Major-Project-Final-main\\admin.py'
    
    # Read file
    with open(admin_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Track changes
    changes = []
    
    # Update imports
    replacements = [
        # System monitor imports
        ('from system_monitor import system_monitor, get_system_status',
         'from system_health_service import system_health, get_system_status'),
        
        # Location matcher imports
        ('from ai_location_matcher import ai_matcher',
         'from location_matching_engine import location_engine'),
        
        ('from advanced_location_matcher import advanced_matcher',
         'from location_matching_engine import location_engine'),
        
        # Function calls - ai_matcher
        ('ai_matcher.process_new_case',
         'location_engine.process_new_case'),
        
        ('ai_matcher.process_new_footage',
         'location_engine.process_new_footage'),
        
        ('ai_matcher.analyze_footage_for_person',
         'location_engine.analyze_footage_for_person'),
        
        ('ai_matcher.find_nearby_footage',
         'location_engine.find_location_matches'),
        
        # Function calls - advanced_matcher
        ('advanced_matcher.auto_process_approved_case',
         'location_engine.auto_process_approved_case'),
        
        ('advanced_matcher.find_intelligent_matches',
         'location_engine.find_location_matches'),
        
        # System monitor function calls
        ('system_monitor._clear_system_cache',
         'system_health._clear_cache'),
        
        ('system_monitor._cleanup_temporary_files',
         'system_health._cleanup_files'),
        
        ('system_monitor.logger',
         'system_health.logger'),
        
        ('system_monitor.get_performance_trends',
         'system_health.get_performance_trends'),
    ]
    
    # Apply replacements
    for old, new in replacements:
        count = content.count(old)
        if count > 0:
            content = content.replace(old, new)
            changes.append(f"[OK] Replaced '{old}' -> '{new}' ({count} occurrences)")
    
    # Write updated content
    with open(admin_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    # Print summary
    print("=" * 80)
    print("ADMIN.PY IMPORT UPDATE COMPLETE")
    print("=" * 80)
    for change in changes:
        print(change)
    print("=" * 80)
    print(f"Total changes: {len(changes)}")
    print("=" * 80)

if __name__ == '__main__':
    update_admin_imports()
    print("\n[OK] admin.py has been updated to use consolidated modules!")
    print("Next steps:")
    print("1. Test the application: python run_app.py")
    print("2. Verify all features work correctly")
    print("3. Delete old redundant files (see REFACTORING_COMPLETE.md)")
