@echo off
title Missing Person Investigation System - RUNNING
color 0A
cls

echo.
echo ============================================================
echo   MISSING PERSON INVESTIGATION SYSTEM
echo   Server Starting...
echo ============================================================
echo.

python run_app.py

if errorlevel 1 (
    echo.
    echo [ERROR] Server stopped with error
    echo Press any key to close...
    pause >nul
) else (
    echo.
    echo [INFO] Server stopped normally
    pause
)
