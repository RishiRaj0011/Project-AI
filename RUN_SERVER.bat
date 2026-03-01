@echo off
title Missing Person Investigation System - Server Running
color 0A

echo.
echo ============================================================
echo   Missing Person Investigation System
echo   Server Starting...
echo ============================================================
echo.

python -u start_server.py

if errorlevel 1 (
    echo.
    echo [ERROR] Server stopped with error
    pause
) else (
    echo.
    echo [INFO] Server stopped normally
    pause
)
