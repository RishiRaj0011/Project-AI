import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __init__ import create_app, db
from models import User

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("  MAKING YOUR USER AN ADMIN")
    print("="*60 + "\n")
    
    # Get all users
    users = User.query.all()
    
    if not users:
        print("No users found. Creating default admin...")
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("\nAdmin created!")
        print("Username: admin")
        print("Password: admin123")
    else:
        print("Current users:")
        for i, user in enumerate(users, 1):
            status = "ADMIN" if user.is_admin else "USER"
            print(f"{i}. {user.username} - {status}")
        
        print("\n" + "="*60)
        
        # Make all non-admin users into admins
        made_admin = []
        for user in users:
            if not user.is_admin:
                user.is_admin = True
                made_admin.append(user.username)
        
        if made_admin:
            db.session.commit()
            print("\nMADE ADMIN:")
            for username in made_admin:
                print(f"  - {username}")
            print("\nYou can now login as admin with your username and password!")
        else:
            print("\nAll users are already admins!")
    
    print("\n" + "="*60)
    print("  FINAL USER LIST")
    print("="*60 + "\n")
    
    users = User.query.all()
    for user in users:
        status = "ADMIN" if user.is_admin else "USER"
        print(f"  {user.username} ({user.email}) - {status}")
    
    print("\n" + "="*60)
    print("\nNow login at: http://localhost:5000")
    print("="*60 + "\n")
