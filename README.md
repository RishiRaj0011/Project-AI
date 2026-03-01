# Integrated Case Management & Surveillance Platform

AI-powered missing person investigation system with advanced computer vision, surveillance analysis, and automated case management.

## 🚀 Features

- **AI-Powered Person Detection** - Multi-modal recognition with face, clothing, and biometric analysis
- **Surveillance Analysis** - Automated CCTV footage processing with AWS Rekognition
- **Case Management** - Comprehensive investigation tracking with status workflows
- **Real-time Chat** - Communication system between users and admins
- **Smart Validation** - Automated case quality assessment and person consistency checks
- **Evidence Management** - Secure evidence handling with integrity verification

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** (Recommended: Python 3.10 or 3.11)
- **Git** (for cloning the repository)
- **pip** (Python package manager)
- **AWS Account** (for Rekognition features - optional)

---

## 🛠️ Installation & Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/PiyushKumar92/Major-Project-Final.git
cd Major-Project-Final
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Optional AI Features:**
```bash
pip install -r requirements_ai.txt
```

### Step 4: Create Environment File

Create a `.env` file in the project root:

```env
# Flask Configuration
SECRET_KEY=your-secret-key-here-change-this
FLASK_DEBUG=False

# AWS Credentials (Optional - for Rekognition features)
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=ap-south-1

# Database (SQLite by default)
DATABASE_URL=sqlite:///instance/app.db
```

**Generate Secret Key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5: Initialize Database

```bash
python
>>> from __init__ import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
...     print("Database created!")
>>> exit()
```

**Or simply run:**
```bash
python run_app.py
```
(Database will be created automatically on first run)

### Step 6: Create Admin User (Optional)

```bash
python
>>> from __init__ import create_app, db
>>> from models import User
>>> app = create_app()
>>> with app.app_context():
...     admin = User(username='admin', email='admin@example.com', is_admin=True)
...     admin.set_password('admin123')
...     db.session.add(admin)
...     db.session.commit()
...     print("Admin user created!")
>>> exit()
```

---

## ▶️ Running the Application

### Development Mode

```bash
python run_app.py
```

The application will be available at: **http://localhost:5000**

### Production Mode

```bash
# Set environment variable
set FLASK_DEBUG=False  # Windows
export FLASK_DEBUG=False  # Linux/Mac

# Run with Gunicorn (Linux/Mac)
gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app

# Run with Waitress (Windows)
pip install waitress
waitress-serve --port=5000 wsgi:app
```

---

## 📁 Project Structure

```
Major-Project-Final/
├── static/                 # Static files (CSS, JS, images)
├── templates/              # HTML templates
├── instance/               # Database files
├── migrations/             # Database migrations
├── models.py              # Database models
├── routes.py              # Application routes
├── forms.py               # Form definitions
├── admin.py               # Admin panel
├── run_app.py             # Application entry point
├── requirements.txt       # Python dependencies
└── .env                   # Environment variables (create this)
```

---

## 🔑 Default Credentials

After setup, you can create users or use:

**Admin Account:**
- Username: `admin`
- Password: `admin123`

**⚠️ Change these credentials immediately in production!**

---

## 🎯 Usage Guide

### For Users:
1. **Register** - Create an account at `/register`
2. **Login** - Access your dashboard
3. **Submit Case** - Register a missing person case
4. **Track Progress** - Monitor case status and updates
5. **Chat** - Communicate with admin team

### For Admins:
1. **Login** - Use admin credentials
2. **Dashboard** - View all cases and analytics
3. **Review Cases** - Approve/reject submissions
4. **Upload Footage** - Add surveillance videos
5. **Manage Users** - User administration

---

## 🔧 Configuration

### Database Configuration

**SQLite (Default):**
```python
# config.py
SQLALCHEMY_DATABASE_URI = 'sqlite:///instance/app.db'
```

**PostgreSQL:**
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://user:password@localhost/dbname'
```

**MySQL:**
```python
SQLALCHEMY_DATABASE_URI = 'mysql://user:password@localhost/dbname'
```

### AWS Rekognition Setup (Optional)

1. Create AWS Account
2. Enable AWS Rekognition service
3. Create IAM user with Rekognition permissions
4. Add credentials to `.env` file

---

## 🐛 Troubleshooting

### Issue: Database not found
```bash
# Solution: Create database manually
python
>>> from __init__ import create_app, db
>>> app = create_app()
>>> with app.app_context():
...     db.create_all()
```

### Issue: Module not found
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Issue: Port already in use
```bash
# Solution: Change port in run_app.py
app.run(host='0.0.0.0', port=5001)  # Use different port
```

### Issue: AWS credentials error
```bash
# Solution: Check .env file has correct AWS keys
# Or disable AWS features by not using surveillance analysis
```

---

## 📦 Dependencies

### Core Dependencies:
- **Flask** - Web framework
- **SQLAlchemy** - Database ORM
- **Flask-Login** - User authentication
- **Flask-WTF** - Form handling
- **Werkzeug** - Security utilities

### AI/ML Dependencies (Optional):
- **OpenCV** - Computer vision
- **face_recognition** - Face detection
- **boto3** - AWS SDK
- **numpy** - Numerical computing

---

## 🔒 Security Notes

1. **Change default admin password** immediately
2. **Use strong SECRET_KEY** in production
3. **Never commit `.env` file** to Git
4. **Rotate AWS keys** regularly
5. **Enable HTTPS** in production
6. **Set FLASK_DEBUG=False** in production

---

## 📝 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Flask secret key | Yes | - |
| `FLASK_DEBUG` | Debug mode | No | False |
| `AWS_ACCESS_KEY_ID` | AWS access key | No | - |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | No | - |
| `AWS_REGION` | AWS region | No | ap-south-1 |
| `DATABASE_URL` | Database connection | No | SQLite |

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Developer

**Piyush Kumar**
- GitHub: [@PiyushKumar92](https://github.com/PiyushKumar92)

---

## 🆘 Support

For issues and questions:
1. Check [Troubleshooting](#-troubleshooting) section
2. Open an issue on GitHub
3. Contact: [Your Email]

---

## 🎓 Project Type

**Academic Project** - Integrated Case Management & Surveillance Platform
- AI-powered investigation system
- Computer vision integration
- Full-stack web application
- Database management
- Security implementation

---

## ⚡ Quick Start (TL;DR)

```bash
# Clone
git clone https://github.com/PiyushKumar92/Major-Project-Final.git
cd Major-Project-Final

# Setup
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Create .env file with SECRET_KEY

# Run
python run_app.py

# Access: http://localhost:5000
```

---

**Made with ❤️ for investigation and surveillance management**
