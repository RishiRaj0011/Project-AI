@echo off
echo ========================================
echo ULTIMATE FIX - Fresh Repository
echo ========================================
echo.
echo This will create a CLEAN repository without any credential history.
echo.
pause

echo Step 1: Backing up current code...
xcopy /E /I /Y . ..\Major-Project-Backup
echo Backup created at: ..\Major-Project-Backup
echo.

echo Step 2: Removing Git history...
rmdir /S /Q .git
echo Done!
echo.

echo Step 3: Initializing fresh Git repository...
git init
git branch -M main
echo Done!
echo.

echo Step 4: Adding all files (clean slate)...
git add .
git commit -m "Initial commit - Clean codebase with environment variables"
echo Done!
echo.

echo Step 5: Connecting to GitHub...
git remote add origin https://github.com/PiyushKumar92/Major-Project-Final.git
echo Done!
echo.

echo Step 6: Force pushing clean code...
git push -u origin main --force
echo Done!
echo.

echo ========================================
echo SUCCESS! Fresh repository created.
echo ========================================
echo.
echo IMPORTANT: Rotate AWS keys!
echo Old keys are exposed - DELETE them immediately!
echo.
pause
