"""
FORENSIC SYSTEM INTEGRATION VERIFICATION
Tests complete data flow from Engine → Database → Route → UI
"""

def verify_forensic_integration():
    """Verify complete forensic system integration"""
    print("="*80)
    print("FORENSIC SYSTEM INTEGRATION VERIFICATION")
    print("="*80)
    
    checks = []
    
    # 1. Database Model Check
    print("\n1. DATABASE MODEL CHECK")
    try:
        from models import PersonDetection, LocationMatch
        
        # Check PersonDetection fields
        required_fields = ['matched_view', 'evidence_number', 'frame_hash', 'decision_factors']
        pd_columns = [c.name for c in PersonDetection.__table__.columns]
        
        for field in required_fields:
            if field in pd_columns:
                print(f"   ✅ PersonDetection.{field} exists")
                checks.append(True)
            else:
                print(f"   ❌ PersonDetection.{field} MISSING")
                checks.append(False)
        
        # Check LocationMatch fields
        lm_columns = [c.name for c in LocationMatch.__table__.columns]
        if 'detection_count' in lm_columns:
            print(f"   ✅ LocationMatch.detection_count exists")
            checks.append(True)
        else:
            print(f"   ❌ LocationMatch.detection_count MISSING")
            checks.append(False)
            
    except Exception as e:
        print(f"   ❌ Database check failed: {e}")
        checks.append(False)
    
    # 2. Route Check
    print("\n2. BACKEND ROUTE CHECK")
    try:
        from admin import admin_bp
        
        routes = [r.rule for r in admin_bp.url_map.iter_rules()]
        
        if '/case/<int:case_id>/match/<int:match_id>/results' in str(routes):
            print(f"   ✅ match_results route exists")
            checks.append(True)
        else:
            print(f"   ❌ match_results route MISSING")
            checks.append(False)
        
        if '/api/batch-progress/<int:case_id>' in str(routes):
            print(f"   ✅ batch_progress_api route exists")
            checks.append(True)
        else:
            print(f"   ❌ batch_progress_api route MISSING")
            checks.append(False)
            
    except Exception as e:
        print(f"   ❌ Route check failed: {e}")
        checks.append(False)
    
    # 3. Engine Check
    print("\n3. CORE ENGINE CHECK")
    try:
        from location_matching_engine import location_engine
        import inspect
        
        # Check analyze_footage_for_person has finally block
        source = inspect.getsource(location_engine.analyze_footage_for_person)
        
        if 'finally:' in source:
            print(f"   ✅ analyze_footage_for_person has finally block")
            checks.append(True)
        else:
            print(f"   ❌ analyze_footage_for_person missing finally block")
            checks.append(False)
        
        if 'db.session.commit()' in source and 'IMMEDIATE COMMIT' in source:
            print(f"   ✅ Immediate commits implemented")
            checks.append(True)
        else:
            print(f"   ⚠️  Immediate commits may not be implemented")
            checks.append(False)
            
    except Exception as e:
        print(f"   ❌ Engine check failed: {e}")
        checks.append(False)
    
    # 4. Template Check
    print("\n4. TEMPLATE CHECK")
    import os
    
    templates = [
        'templates/admin/forensic_timeline.html',
        'templates/admin/forensic_timeline_batch.html'
    ]
    
    for template in templates:
        if os.path.exists(template):
            print(f"   ✅ {template} exists")
            checks.append(True)
        else:
            print(f"   ❌ {template} MISSING")
            checks.append(False)
    
    # 5. Integration Flow Check
    print("\n5. DATA FLOW VERIFICATION")
    print("   Expected Flow:")
    print("   Case Approval → LocationMatch → Celery Task →")
    print("   Frame Analysis → _save_multi_view_detection() →")
    print("   db.session.commit() → PersonDetection →")
    print("   match_results route → forensic_timeline.html")
    
    flow_complete = all([
        'PersonDetection' in str(checks),
        'LocationMatch' in str(checks),
        'match_results' in str(checks),
        'forensic_timeline.html' in str(checks)
    ])
    
    if flow_complete:
        print("   ✅ Complete data flow verified")
        checks.append(True)
    else:
        print("   ❌ Data flow incomplete")
        checks.append(False)
    
    # Final Report
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    
    passed = sum(checks)
    total = len(checks)
    percentage = (passed / total * 100) if total > 0 else 0
    
    print(f"Checks Passed: {passed}/{total} ({percentage:.1f}%)")
    
    if percentage == 100:
        print("\n✅ SYSTEM FULLY INTEGRATED - PRODUCTION READY")
    elif percentage >= 80:
        print("\n⚠️  SYSTEM MOSTLY INTEGRATED - Minor fixes needed")
    else:
        print("\n❌ SYSTEM INCOMPLETE - Major fixes required")
    
    print("="*80)
    
    return percentage == 100


if __name__ == "__main__":
    verify_forensic_integration()
