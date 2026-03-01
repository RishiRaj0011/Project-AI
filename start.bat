@echo off
echo ========================================
echo Missing Person Investigation System
echo Quick Start Script
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo [1/5] Creating virtual environment...
    python -m venv venv
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)
echo.

REM Activate virtual environment
echo [2/5] Activating virtual environment...
call venv\Scripts\activate
echo ✓ Virtual environment activated
echo.

REM Install dependencies
echo [3/5] Installing dependencies...
pip install -r requirements.txt --quiet
echo ✓ Dependencies installed
echo.

REM Create required folders
echo [4/5] Creating required folders...
if not exist "instance\" mkdir instance
if not exist "static\uploads\" mkdir static\uploads
if not exist "static\surveillance\" mkdir static\surveillance
if not exist "static\chat_uploads\" mkdir static\chat_uploads
echo ✓ Folders created
echo.

REM Initialize database if not exists
if not exist "instance\app.db" (
    echo [5/5] Initializing database and creating admin user...
    python -c "from __init__ import create_app, db; from models import User; app = create_app(); app.app_context().push(); db.create_all(); admin = User(username='admin', email='admin@example.com', is_admin=True); admin.set_password('admin123'); db.session.add(admin); db.session.commit(); print('✓ Database initialized with admin user')"
) else (
    echo [5/5] Database already exists
    echo ✓ Skipping database initialization
)
echo.

echo ========================================
echo Starting Application...
echo ========================================
echo.
echo Access the application at: http://localhost:5000
echo.
echo Default Admin Credentials:
echo Username: admin
echo Password: admin123
echo.
echo Press Ctrl+C to stop the server
echo ========================================
echo.

REM Run the application
python run_app.py

pause
