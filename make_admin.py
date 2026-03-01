import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from __init__ import create_app, db
from models import User

app = create_app()

with app.app_context():
    print("\n" + "="*60)
    print("  ADMIN USER MANAGEMENT")
    print("="*60 + "\n")
    
    # Show all users
    users = User.query.all()
    print(f"Total users in database: {len(users)}\n")
    
    if users:
        print("Current users:")
        for i, user in enumerate(users, 1):
            admin_status = "ADMIN" if user.is_admin else "USER"
            print(f"{i}. {user.username} ({user.email}) - {admin_status}")
        
        print("\n" + "="*60)
        print("OPTIONS:")
        print("="*60)
        print("1. Make existing user an admin")
        print("2. Create new admin user")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == "1":
            username = input("\nEnter username to make admin: ").strip()
            user = User.query.filter_by(username=username).first()
            
            if user:
                user.is_admin = True
                db.session.commit()
                print(f"\n✓ SUCCESS! User '{username}' is now an ADMIN!")
                print(f"\nLogin credentials:")
                print(f"  Username: {username}")
                print(f"  Password: (your existing password)")
            else:
                print(f"\n✗ ERROR: User '{username}' not found!")
        
        elif choice == "2":
            username = input("\nEnter new admin username: ").strip()
            email = input("Enter admin email: ").strip()
            password = input("Enter admin password: ").strip()
            
            # Check if user exists
            existing = User.query.filter_by(username=username).first()
            if existing:
                print(f"\n✗ ERROR: Username '{username}' already exists!")
            else:
                admin = User(username=username, email=email, is_admin=True)
                admin.set_password(password)
                db.session.add(admin)
                db.session.commit()
                print(f"\n✓ SUCCESS! Admin user created!")
                print(f"\nLogin credentials:")
                print(f"  Username: {username}")
                print(f"  Password: {password}")
        
        else:
            print("\nExiting...")
    
    else:
        print("No users found. Creating default admin user...\n")
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("✓ Default admin user created!")
        print("\nLogin credentials:")
        print("  Username: admin")
        print("  Password: admin123")
    
    print("\n" + "="*60)
    print("  UPDATED USER LIST")
    print("="*60 + "\n")
    
    users = User.query.all()
    for i, user in enumerate(users, 1):
        admin_status = "ADMIN" if user.is_admin else "USER"
        print(f"{i}. {user.username} ({user.email}) - {admin_status}")
    
    print("\n" + "="*60)
