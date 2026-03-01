import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __init__ import create_app, db
from models import User

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("  ADMIN SYSTEM CHECK")
    print("="*60 + "\n")
    
    # Ensure default admin exists
    default_admin = User.query.filter_by(username='admin').first()
    
    if not default_admin:
        print("Creating default admin user...")
        default_admin = User(username='admin', email='admin@example.com', is_admin=True)
        default_admin.set_password('admin123')
        db.session.add(default_admin)
        db.session.commit()
        print("[OK] Default admin created")
    else:
        # Ensure default admin is always admin
        if not default_admin.is_admin:
            default_admin.is_admin = True
            db.session.commit()
            print("[OK] Default admin status restored")
        else:
            print("[OK] Default admin exists")
    
    print("\n" + "="*60)
    print("  ALL USERS")
    print("="*60 + "\n")
    
    users = User.query.all()
    for user in users:
        status = "ADMIN" if user.is_admin else "USER"
        print(f"  {user.username} ({user.email}) - {status}")
    
    print("\n" + "="*60)
    print("\nSYSTEM READY!")
    print("- Default admin: admin / admin123")
    print("- Admins can make other users admin via dashboard")
    print("="*60 + "\n")
