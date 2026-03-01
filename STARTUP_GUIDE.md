# 🚀 QUICK START GUIDE - Missing Person Investigation System

## ⚡ Fast Setup (5 Minutes)

### Step 1: Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 2: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 3: Generate Secret Key
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Copy the output and paste it in `.env` file as `SECRET_KEY`

### Step 4: Initialize Database
```bash
python
```
Then in Python shell:
```python
from __init__ import create_app, db
from models import User
app = create_app()
with app.app_context():
    db.create_all()
    admin = User(username='admin', email='admin@example.com', is_admin=True)
    admin.set_password('admin123')
    db.session.add(admin)
    db.session.commit()
    print("✅ Database and admin user created!")
exit()
```

### Step 5: Run Application
```bash
python run_app.py
```

### Step 6: Access Application
Open browser: **http://localhost:5000**

**Login Credentials:**
- Username: `admin`
- Password: `admin123`

---

## 📋 Full Setup (With AI Features)

### Prerequisites
- Python 3.8+ (Recommended: 3.10 or 3.11)
- Visual Studio Build Tools (for dlib on Windows)
- CMake (for dlib compilation)

### Install AI Dependencies
```bash
pip install -r requirements_ai.txt
```

**Note:** Installing `dlib` on Windows requires Visual Studio Build Tools:
1. Download from: https://visualstudio.microsoft.com/downloads/
2. Install "Desktop development with C++"
3. Then run: `pip install dlib`

---

## 🔧 Configuration

### Environment Variables (.env)
```env
SECRET_KEY=<your-generated-secret-key>
FLASK_DEBUG=True
AWS_ACCESS_KEY_ID=<optional-aws-key>
AWS_SECRET_ACCESS_KEY=<optional-aws-secret>
AWS_REGION=ap-south-1
DATABASE_URL=sqlite:///instance/app.db
```

### Create Required Folders
```bash
mkdir instance
mkdir static\uploads
mkdir static\surveillance
mkdir static\chat_uploads
```

---

## 🎯 Running with Full Efficiency

### Development Mode (Recommended for Testing)
```bash
python run_app.py
```

### Production Mode (Windows)
```bash
set FLASK_DEBUG=False
pip install waitress
waitress-serve --port=5000 wsgi:app
```

### Production Mode (Linux/Mac)
```bash
export FLASK_DEBUG=False
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

### With Celery (Background Tasks)
**Terminal 1 - Flask App:**
```bash
python run_app.py
```

**Terminal 2 - Celery Worker:**
```bash
celery -A celery_app.celery worker --loglevel=info --pool=solo
```

---

## 🚀 Performance Optimization

### 1. Database Optimization
For better performance, use PostgreSQL instead of SQLite:
```bash
pip install psycopg2-binary
```
Update `.env`:
```env
DATABASE_URL=postgresql://username:password@localhost/dbname
```

### 2. Redis for Celery (Better Performance)
```bash
pip install redis
```
Update `.env`:
```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### 3. Enable Caching
```bash
pip install Flask-Caching
```

---

## 📊 System Features

### For Users:
1. Register account
2. Submit missing person cases
3. Upload photos/videos
4. Track case status
5. Chat with admin
6. Receive notifications

### For Admins:
1. Review and approve cases
2. Upload surveillance footage
3. AI-powered person detection
4. Case management dashboard
5. User management
6. Analytics and reports

---

## 🔍 AI Features

### Face Recognition
- Multi-face detection
- Face encoding comparison
- Age progression analysis

### Clothing Analysis
- Color detection
- Pattern recognition
- Seasonal categorization

### Surveillance Analysis
- CCTV footage processing
- Person tracking
- Behavioral analysis
- Crowd detection

### AWS Rekognition (Optional)
- Advanced face matching
- Celebrity recognition
- Object detection

---

## 🐛 Troubleshooting

### Issue: ModuleNotFoundError
```bash
pip install -r requirements.txt --force-reinstall
```

### Issue: Database locked
```bash
# Stop all running instances
# Delete instance/app.db
# Recreate database (Step 4)
```

### Issue: Port 5000 already in use
Edit `run_app.py`:
```python
app.run(host='0.0.0.0', port=5001)
```

### Issue: dlib installation fails
```bash
# Windows: Install Visual Studio Build Tools
# Or use pre-built wheel:
pip install dlib-19.24.2-cp310-cp310-win_amd64.whl
```

### Issue: Face recognition not working
```bash
pip install cmake
pip install dlib
pip install face-recognition
```

---

## 📈 Monitoring & Logs

### View Application Logs
Logs are printed to console. For file logging, add to `run_app.py`:
```python
import logging
logging.basicConfig(filename='app.log', level=logging.INFO)
```

### Database Backup
```bash
# SQLite backup
copy instance\app.db instance\app_backup.db
```

---

## 🔒 Security Checklist

- [ ] Change default admin password
- [ ] Generate strong SECRET_KEY
- [ ] Set FLASK_DEBUG=False in production
- [ ] Enable HTTPS
- [ ] Rotate AWS keys regularly
- [ ] Regular database backups
- [ ] Update dependencies regularly

---

## 📞 Support

For issues:
1. Check troubleshooting section
2. Review logs
3. Check GitHub issues
4. Contact: admin@example.com

---

## 🎓 Quick Commands Reference

```bash
# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run application
python run_app.py

# Create admin user
python -c "from __init__ import create_app, db; from models import User; app = create_app(); app.app_context().push(); admin = User(username='admin', email='admin@example.com', is_admin=True); admin.set_password('admin123'); db.session.add(admin); db.session.commit()"

# Database migrations
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# Run tests
pytest

# Check installed packages
pip list
```

---

**✅ You're all set! Start the application and begin investigating!**
