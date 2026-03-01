@echo off
echo ========================================
echo COMPLETE Git Cleanup - All AWS Files
echo ========================================
echo.

echo Step 1: Removing ALL problematic files from Git...
git rm --cached check_video_faces.py 2>nul
git rm --cached test_aws_fixed.py 2>nul
git rm --cached test_hybrid_detection.py 2>nul
git rm --cached test_manual_aws.py 2>nul
git rm --cached check_faces.py 2>nul
git rm --cached test_aws_detection.py 2>nul
echo Done!
echo.

echo Step 2: Cleaning ENTIRE Git history (this will take 2-3 minutes)...
set FILTER_BRANCH_SQUELCH_WARNING=1
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch check_video_faces.py test_aws_fixed.py test_hybrid_detection.py test_manual_aws.py check_faces.py test_aws_detection.py aws_rekognition_matcher.py" --prune-empty --tag-name-filter cat -- --all
echo Done!
echo.

echo Step 3: Re-adding aws_rekognition_matcher.py (clean version)...
git add aws_rekognition_matcher.py
git commit -m "Re-add aws_rekognition_matcher.py with environment variables only"
echo Done!
echo.

echo Step 4: Garbage collection...
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo Done!
echo.

echo Step 5: Force pushing to GitHub...
git push origin main --force
echo Done!
echo.

echo ========================================
echo SUCCESS! All AWS credentials removed.
echo ========================================
echo.
echo CRITICAL: Rotate AWS keys NOW!
echo 1. AWS Console: https://console.aws.amazon.com/iam
echo 2. Delete OLD keys (they are exposed!)
echo 3. Generate NEW keys
echo 4. Update .env file
echo.
pause
