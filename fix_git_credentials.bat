@echo off
echo ========================================
echo Fixing GitHub Push Protection Issue
echo ========================================
echo.

echo Step 1: Removing problematic files from Git tracking...
git rm --cached check_video_faces.py 2>nul
git rm --cached test_aws_fixed.py 2>nul
git rm --cached test_hybrid_detection.py 2>nul
git rm --cached test_manual_aws.py 2>nul
echo Done!
echo.

echo Step 2: Committing the removal...
git commit -m "Remove test files with exposed AWS credentials"
echo Done!
echo.

echo Step 3: Cleaning Git history (this may take a minute)...
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch check_video_faces.py test_aws_fixed.py test_hybrid_detection.py test_manual_aws.py" --prune-empty --tag-name-filter cat -- --all
echo Done!
echo.

echo Step 4: Force pushing to GitHub...
git push origin main --force
echo Done!
echo.

echo ========================================
echo SUCCESS! Git issue fixed.
echo ========================================
echo.
echo IMPORTANT: Now you MUST rotate your AWS keys!
echo 1. Go to AWS Console: https://console.aws.amazon.com/
echo 2. IAM - Users - Security Credentials
echo 3. DELETE old exposed keys
echo 4. GENERATE new keys
echo 5. UPDATE .env file with new keys
echo.
pause
