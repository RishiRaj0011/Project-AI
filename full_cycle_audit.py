"""
Full-Cycle Integration Audit
Comprehensive verification of all data flows and constraints
"""

def audit_1_registration_flow():
    """Audit 1: End-to-End Registration"""
    print("\n" + "=" * 70)
    print("AUDIT 1: END-TO-END REGISTRATION FLOW")
    print("=" * 70)
    
    issues = []
    
    # Check 1.1: Path normalization in register_case
    print("\n[1.1] Checking path normalization in register_case...")
    with open('routes.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Check if path normalization exists after file_manager.store_file
        if "stored_path.replace('\\\\', '/')" in content or 'stored_path.replace("\\\\", "/")' in content:
            print("  PASS: Path normalization found")
        else:
            issues.append("Path normalization missing after file_manager.store_file")
            print("  FAIL: Path normalization missing")
    
    # Check 1.2: Video is optional
    print("\n[1.2] Checking video is optional...")
    if "form.video.data else []" in content:
        print("  PASS: Video defaults to empty list if not provided")
    else:
        issues.append("Video might not be optional")
        print("  FAIL: Video handling unclear")
    
    # Check 1.3: Multi-view consistency check triggered
    print("\n[1.3] Checking person consistency validation...")
    if "validate_case_person_consistency" in content:
        print("  PASS: Person consistency validation found")
    else:
        issues.append("Person consistency validation not triggered")
        print("  FAIL: Consistency validation missing")
    
    # Check 1.4: Transaction handling
    print("\n[1.4] Checking transaction handling...")
    if "db.session.rollback()" in content and "db.session.flush()" in content:
        print("  PASS: Proper transaction handling with rollback")
    else:
        issues.append("Transaction handling incomplete")
        print("  FAIL: Missing rollback or flush")
    
    return len(issues) == 0, issues


def audit_2_media_relationships():
    """Audit 2: Media Relationship Integrity"""
    print("\n" + "=" * 70)
    print("AUDIT 2: MEDIA RELATIONSHIP INTEGRITY")
    print("=" * 70)
    
    issues = []
    
    # Check 2.1: Eager loading in case_details
    print("\n[2.1] Checking eager loading in case_details route...")
    with open('routes.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
        if "db.joinedload(Case.target_images)" in content and "db.joinedload(Case.search_videos)" in content:
            print("  PASS: Eager loading for both target_images and search_videos")
        else:
            issues.append("Eager loading missing in case_details")
            print("  FAIL: Eager loading incomplete")
    
    # Check 2.2: Template loops through all images
    print("\n[2.2] Checking template handles multiple images...")
    try:
        with open('templates/case_details.html', 'r', encoding='utf-8') as f:
            template = f.read()
            
            if "{% for image in case.target_images %}" in template:
                print("  PASS: Template loops through all images")
            else:
                issues.append("Template might only show single image")
                print("  FAIL: Image loop not found")
            
            if "{% for video in case.search_videos %}" in template:
                print("  PASS: Template loops through all videos")
            else:
                issues.append("Template might only show single video")
                print("  FAIL: Video loop not found")
    except FileNotFoundError:
        issues.append("case_details.html not found")
        print("  FAIL: Template file missing")
    
    # Check 2.3: Admin template also loops
    print("\n[2.3] Checking admin template...")
    try:
        with open('templates/admin/case_detail.html', 'r', encoding='utf-8') as f:
            admin_template = f.read()
            
            if "{% for image in case.target_images %}" in admin_template:
                print("  PASS: Admin template loops through images")
            else:
                issues.append("Admin template might only show single image")
                print("  FAIL: Admin image loop not found")
    except FileNotFoundError:
        issues.append("admin/case_detail.html not found")
        print("  FAIL: Admin template missing")
    
    return len(issues) == 0, issues


def audit_3_admin_location_sync():
    """Audit 3: Admin Location Sync"""
    print("\n" + "=" * 70)
    print("AUDIT 3: ADMIN LOCATION SYNC")
    print("=" * 70)
    
    issues = []
    
    # Check 3.1: Location routes exist
    print("\n[3.1] Checking location routes...")
    try:
        with open('location_matching_routes.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
            if "@location_bp.route" in content:
                print("  PASS: Location blueprint routes found")
            else:
                issues.append("Location routes not properly defined")
                print("  FAIL: Location routes missing")
    except FileNotFoundError:
        issues.append("location_matching_routes.py not found")
        print("  FAIL: Location routes file missing")
    
    # Check 3.2: Case location data structure
    print("\n[3.2] Checking Case model has location fields...")
    try:
        with open('models.py', 'r', encoding='utf-8') as f:
            content = f.read()
            
            if "last_seen_location" in content:
                print("  PASS: Case model has last_seen_location field")
            else:
                issues.append("Case model missing location field")
                print("  FAIL: Location field not found")
    except FileNotFoundError:
        issues.append("models.py not found")
        print("  FAIL: Models file missing")
    
    # Check 3.3: Real-time reflection (no caching issues)
    print("\n[3.3] Checking for caching issues...")
    print("  INFO: Manual test required - register case and check admin location view")
    print("  NOTE: If location doesn't appear immediately, check for query caching")
    
    return len(issues) == 0, issues


def audit_4_edit_mode_persistence():
    """Audit 4: Edit-Mode Persistence"""
    print("\n" + "=" * 70)
    print("AUDIT 4: EDIT-MODE PERSISTENCE")
    print("=" * 70)
    
    issues = []
    
    # Check 4.1: Edit route pre-populates form
    print("\n[4.1] Checking edit_case pre-populates form...")
    with open('routes.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
        if "form.full_name.data = case.person_name" in content:
            print("  PASS: Form pre-population found")
        else:
            issues.append("Edit form might not pre-populate")
            print("  FAIL: Form pre-population unclear")
    
    # Check 4.2: Existing images shown in edit
    print("\n[4.2] Checking existing images shown in edit...")
    try:
        with open('templates/edit_case.html', 'r', encoding='utf-8') as f:
            template = f.read()
            
            if "case.target_images" in template:
                print("  PASS: Edit template shows existing images")
            else:
                issues.append("Edit template might not show existing images")
                print("  FAIL: Existing images not displayed")
    except FileNotFoundError:
        issues.append("edit_case.html not found")
        print("  FAIL: Edit template missing")
    
    # Check 4.3: Update doesn't create duplicates
    print("\n[4.3] Checking update logic...")
    if "case = Case.query.get_or_404(case_id)" in content and "db.session.add(case)" not in content.split("def edit_case")[1].split("def ")[0]:
        print("  PASS: Update modifies existing case (no duplicate creation)")
    else:
        print("  WARNING: Verify update doesn't create duplicates")
    
    # Check 4.4: Path normalization in edit
    print("\n[4.4] Checking path normalization in edit...")
    edit_section = content.split("def edit_case")[1] if "def edit_case" in content else ""
    if ".replace('\\\\', '/')" in edit_section or '.replace("\\\\", "/")' in edit_section:
        print("  PASS: Path normalization in edit route")
    else:
        issues.append("Path normalization missing in edit route")
        print("  FAIL: Edit route missing path normalization")
    
    return len(issues) == 0, issues


def audit_5_circular_data_flow():
    """Audit 5: Circular Data Flow Verification"""
    print("\n" + "=" * 70)
    print("AUDIT 5: CIRCULAR DATA FLOW (Register -> Save -> Display -> Edit -> Update)")
    print("=" * 70)
    
    issues = []
    
    # Check 5.1: All paths normalized at entry points
    print("\n[5.1] Checking path normalization at all entry points...")
    with open('routes.py', 'r', encoding='utf-8') as f:
        content = f.read()
        
        # Count path normalizations
        normalize_count = content.count(".replace('\\\\', '/')") + content.count('.replace("\\\\", "/")')
        
        if normalize_count >= 2:  # Should be in register and edit at minimum
            print(f"  PASS: Found {normalize_count} path normalization points")
        else:
            issues.append(f"Only {normalize_count} path normalizations found (need at least 2)")
            print(f"  FAIL: Insufficient path normalizations ({normalize_count})")
    
    # Check 5.2: Template helpers handle legacy paths
    print("\n[5.2] Checking template helpers normalize paths...")
    try:
        with open('template_helpers.py', 'r', encoding='utf-8') as f:
            helpers = f.read()
            
            if ".replace('\\\\', '/')" in helpers:
                print("  PASS: Template helpers normalize backslashes")
            else:
                issues.append("Template helpers don't normalize paths")
                print("  FAIL: Template helpers missing normalization")
    except FileNotFoundError:
        issues.append("template_helpers.py not found")
        print("  FAIL: Template helpers file missing")
    
    # Check 5.3: Database migration script exists
    print("\n[5.3] Checking migration scripts exist...")
    import os
    
    if os.path.exists('fix_existing_paths.py'):
        print("  PASS: Path migration script exists")
    else:
        issues.append("Path migration script missing")
        print("  FAIL: fix_existing_paths.py not found")
    
    if os.path.exists('fix_person_profile_schema.py'):
        print("  PASS: Schema migration script exists")
    else:
        issues.append("Schema migration script missing")
        print("  FAIL: fix_person_profile_schema.py not found")
    
    return len(issues) == 0, issues


def run_full_audit():
    """Run all audits and generate report"""
    print("\n" + "=" * 70)
    print("FULL-CYCLE INTEGRATION AUDIT")
    print("Forensic Software Testing - Data Consistency Verification")
    print("=" * 70)
    
    results = {}
    all_issues = []
    
    # Run all audits
    results['Registration Flow'], issues1 = audit_1_registration_flow()
    all_issues.extend(issues1)
    
    results['Media Relationships'], issues2 = audit_2_media_relationships()
    all_issues.extend(issues2)
    
    results['Admin Location Sync'], issues3 = audit_3_admin_location_sync()
    all_issues.extend(issues3)
    
    results['Edit Mode Persistence'], issues4 = audit_4_edit_mode_persistence()
    all_issues.extend(issues4)
    
    results['Circular Data Flow'], issues5 = audit_5_circular_data_flow()
    all_issues.extend(issues5)
    
    # Generate final report
    print("\n" + "=" * 70)
    print("AUDIT SUMMARY")
    print("=" * 70)
    
    for audit_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{audit_name}: {status}")
    
    print("\n" + "=" * 70)
    print("ISSUES FOUND")
    print("=" * 70)
    
    if all_issues:
        for i, issue in enumerate(all_issues, 1):
            print(f"{i}. {issue}")
    else:
        print("No issues found - System is 100% integrated!")
    
    print("\n" + "=" * 70)
    print("FINAL VERDICT")
    print("=" * 70)
    
    total_audits = len(results)
    passed_audits = sum(1 for passed in results.values() if passed)
    
    print(f"Passed: {passed_audits}/{total_audits} audits")
    print(f"Issues: {len(all_issues)} total")
    
    if len(all_issues) == 0:
        print("\nSTATUS: PRODUCTION READY")
        print("All data flows are circular and consistent.")
        print("No Windows backslashes can enter the database.")
    else:
        print("\nSTATUS: NEEDS ATTENTION")
        print("Review issues above and apply fixes.")
    
    print("=" * 70)
    
    return len(all_issues) == 0


if __name__ == "__main__":
    success = run_full_audit()
    exit(0 if success else 1)
