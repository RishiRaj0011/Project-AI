"""
Aggressive NumPy Array Check Scanner
Finds ALL problematic array boolean checks
"""
import re
import os

files_to_scan = [
    'vision_engine.py',
    'forensic_vision_engine.py',
    'location_matching_engine.py',
    'multi_view_forensic_engine.py',
    'tasks.py'
]

print("=" * 80)
print("AGGRESSIVE NUMPY ARRAY CHECK SCANNER")
print("=" * 80)

total_issues = 0

for filename in files_to_scan:
    if not os.path.exists(filename):
        continue
    
    print(f"\n[SCANNING] {filename}")
    print("-" * 80)
    
    with open(filename, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    issues_found = []
    
    for i, line in enumerate(lines, 1):
        # Skip comments
        if line.strip().startswith('#'):
            continue
        
        # Pattern 1: if not array_name:
        if re.search(r'\bif\s+not\s+(face_locations|encodings|face_encodings|matches|distances|target_encodings|all_encodings)\s*:', line):
            if 'len(' not in line and 'is not None' not in line:
                issues_found.append((i, line.rstrip(), 'NEGATIVE CHECK'))
        
        # Pattern 2: if array_name:
        if re.search(r'\bif\s+(face_locations|encodings|face_encodings|matches|distances|target_encodings|all_encodings)\s*:', line):
            if 'len(' not in line and 'is not None' not in line and 'any(' not in line:
                issues_found.append((i, line.rstrip(), 'POSITIVE CHECK'))
    
    if issues_found:
        for line_num, line_content, check_type in issues_found:
            print(f"  Line {line_num} [{check_type}]: {line_content}")
            total_issues += 1
    else:
        print(f"  [OK] No issues found")

print("\n" + "=" * 80)
print(f"TOTAL ISSUES FOUND: {total_issues}")
print("=" * 80)
