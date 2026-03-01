#!/usr/bin/env python
import os
os.environ['FLASK_DEBUG'] = 'True'

from __init__ import create_app, db

print("\n" + "="*60)
print("  MISSING PERSON INVESTIGATION SYSTEM")
print("="*60)

app = create_app()

with app.app_context():
    db.create_all()
    print("✓ Database initialized")

print("\n" + "="*60)
print("  SERVER RUNNING")
print("="*60)
print("  URL: http://localhost:5000")
print("  Username: admin")
print("  Password: admin123")
print("="*60 + "\n")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
