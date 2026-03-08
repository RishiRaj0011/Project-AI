"""
Quick Route Verification Script
Run this to verify Targeted Find route is accessible
"""

def verify_targeted_find_route():
    """Verify the targeted-analysis route exists"""
    print("=" * 80)
    print("TARGETED FIND ROUTE VERIFICATION")
    print("=" * 80)
    
    try:
        from admin import admin_bp
        
        # Get all routes in admin blueprint
        routes = []
        for rule in admin_bp.url_map.iter_rules():
            if 'targeted' in rule.rule.lower():
                routes.append({
                    'endpoint': rule.endpoint,
                    'methods': list(rule.methods),
                    'rule': rule.rule
                })
        
        print("\n✅ FOUND TARGETED ROUTES:")
        for route in routes:
            print(f"  - {route['rule']}")
            print(f"    Methods: {route['methods']}")
            print(f"    Endpoint: {route['endpoint']}")
        
        # Check specific route
        expected_route = '/admin/api/targeted-analysis'
        found = any(expected_route in r['rule'] for r in routes)
        
        if found:
            print(f"\n✅ SUCCESS: Route {expected_route} is registered!")
            print("\nFull URL: http://localhost:5000/admin/api/targeted-analysis")
            print("Method: POST")
            print("Body: {case_id: int, footage_id: int}")
        else:
            print(f"\n❌ ERROR: Route {expected_route} NOT FOUND!")
            print("\nAvailable routes:")
            for route in routes:
                print(f"  - {route['rule']}")
        
        return found
        
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    from __init__ import create_app
    
    app = create_app()
    
    with app.app_context():
        # Check all admin routes
        print("\n📋 ALL ADMIN ROUTES:")
        print("-" * 80)
        
        admin_routes = []
        for rule in app.url_map.iter_rules():
            if rule.rule.startswith('/admin'):
                admin_routes.append({
                    'rule': rule.rule,
                    'methods': sorted(list(rule.methods - {'HEAD', 'OPTIONS'})),
                    'endpoint': rule.endpoint
                })
        
        # Sort by rule
        admin_routes.sort(key=lambda x: x['rule'])
        
        # Find API routes
        api_routes = [r for r in admin_routes if '/api/' in r['rule']]
        
        print(f"\nFound {len(api_routes)} API routes:")
        for route in api_routes:
            print(f"  {route['methods'][0]:6} {route['rule']}")
        
        # Check targeted-analysis specifically
        print("\n" + "=" * 80)
        print("TARGETED ANALYSIS ROUTE CHECK:")
        print("=" * 80)
        
        targeted_route = next((r for r in admin_routes if 'targeted-analysis' in r['rule']), None)
        
        if targeted_route:
            print(f"\n✅ FOUND: {targeted_route['rule']}")
            print(f"   Methods: {targeted_route['methods']}")
            print(f"   Endpoint: {targeted_route['endpoint']}")
            print("\n✅ Route is correctly registered!")
            print("\nTest with:")
            print("  curl -X POST http://localhost:5000/admin/api/targeted-analysis \\")
            print("    -H 'Content-Type: application/json' \\")
            print("    -d '{\"case_id\": 1, \"footage_id\": 6}'")
        else:
            print("\n❌ NOT FOUND: /admin/api/targeted-analysis")
            print("\nSearching for similar routes...")
            similar = [r for r in admin_routes if 'target' in r['rule'].lower() or 'analysis' in r['rule'].lower()]
            if similar:
                print("\nSimilar routes found:")
                for route in similar:
                    print(f"  - {route['rule']}")
            else:
                print("\nNo similar routes found.")
        
        print("\n" + "=" * 80)
        print("VERIFICATION COMPLETE")
        print("=" * 80)
