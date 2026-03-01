@echo off
title Missing Person Investigation System - Starting...
color 0A

echo.
echo ================================================
echo   Missing Person Investigation System
echo   Starting with Full Efficiency...
echo ================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

echo [1/4] Installing core dependencies...
python -m pip install --quiet Flask Flask-SQLAlchemy Flask-Login Flask-Bcrypt Flask-WTF Flask-Migrate Flask-Moment python-dotenv pytz celery boto3 2>nul
echo       ✓ Core dependencies ready

echo.
echo [2/4] Creating required directories...
if not exist "instance" mkdir instance
if not exist "static\uploads" mkdir static\uploads
if not exist "static\surveillance" mkdir static\surveillance  
if not exist "static\chat_uploads" mkdir static\chat_uploads
echo       ✓ Directories created

echo.
echo [3/4] Initializing database...
python init_db.py
echo       ✓ Database ready

echo.
echo [4/4] Starting application server...
echo.
echo ================================================
echo   APPLICATION READY!
echo ================================================
echo.
echo   URL: http://localhost:5000
echo.
echo   Admin Login:
echo   Username: admin
echo   Password: admin123
echo.
echo   Press Ctrl+C to stop the server
echo ================================================
echo.

python run_app.py
