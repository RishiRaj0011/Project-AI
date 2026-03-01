"""Test blueprint registration"""
import sys
sys.path.insert(0, 'd:\\Major-Project-Final-main')

print("Testing blueprint imports...")

# Test admin
try:
    from admin import admin_bp
    print(f"OK admin_bp: {admin_bp.name} at {admin_bp.url_prefix}")
except Exception as e:
    print(f"FAIL admin_bp: {e}")
    import traceback
    traceback.print_exc()

# Test location
try:
    from location_matching_routes import location_bp
    print(f"OK location_bp: {location_bp.name} at {location_bp.url_prefix}")
except Exception as e:
    print(f"FAIL location_bp: {e}")

# Test enhanced admin
try:
    from enhanced_admin_routes import enhanced_admin_bp
    print(f"OK enhanced_admin_bp: {enhanced_admin_bp.name} at {enhanced_admin_bp.url_prefix}")
except Exception as e:
    print(f"FAIL enhanced_admin_bp: {e}")

# Test learning
try:
    from continuous_learning_routes import learning_bp
    print(f"OK learning_bp: {learning_bp.name} at {learning_bp.url_prefix}")
except Exception as e:
    print(f"FAIL learning_bp: {e}")

print("\nTesting Flask app creation...")
try:
    from __init__ import create_app
    app = create_app()
    
    print("\nRegistered blueprints:")
    for bp_name, bp in app.blueprints.items():
        print(f"  - {bp_name}: {bp.url_prefix}")
    
    print("\nLooking for admin.dashboard route:")
    found = False
    for rule in app.url_map.iter_rules():
        if 'admin.dashboard' in rule.endpoint:
            print(f"  FOUND: {rule.endpoint} -> {rule.rule}")
            found = True
    
    if not found:
        print("  NOT FOUND - admin blueprint not registered!")
    
except Exception as e:
    print(f"FAIL App creation: {e}")
    import traceback
    traceback.print_exc()
