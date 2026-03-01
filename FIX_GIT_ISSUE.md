# Fix GitHub Push Protection Issue - AWS Credentials Exposed

## Problem
GitHub detected AWS credentials in your Git history and blocked the push.

## Solution - Run These Commands in Order:

### Step 1: Remove files from Git history (not from disk)
```bash
git rm --cached check_video_faces.py 2>nul
git rm --cached test_aws_fixed.py 2>nul
git rm --cached test_hybrid_detection.py 2>nul
git rm --cached test_manual_aws.py 2>nul
```

### Step 2: Commit the removal
```bash
git commit -m "Remove test files with exposed AWS credentials from tracking"
```

### Step 3: Clean Git history (IMPORTANT!)
```bash
git filter-branch --force --index-filter "git rm --cached --ignore-unmatch check_video_faces.py test_aws_fixed.py test_hybrid_detection.py test_manual_aws.py" --prune-empty --tag-name-filter cat -- --all
```

### Step 4: Force push to GitHub
```bash
git push origin main --force
```

### Step 5: Rotate AWS Keys (CRITICAL SECURITY!)
1. Go to AWS Console: https://console.aws.amazon.com/
2. Navigate to: IAM → Users → Your User → Security Credentials
3. **Deactivate/Delete** the old exposed keys
4. **Generate new keys**
5. Update your `.env` file with new keys

---

## Alternative Quick Fix (If above doesn't work):

### Option A: Create new branch and force push
```bash
git checkout -b main-clean
git push origin main-clean --force
```

### Option B: Delete and recreate repository
1. Delete the GitHub repository
2. Create new repository with same name
3. Push fresh code:
```bash
git remote set-url origin https://github.com/PiyushKumar92/Major-Project-Final.git
git push -u origin main --force
```

---

## Verify .env file exists with credentials:
Your `.env` file should contain:
```
AWS_ACCESS_KEY_ID=your_new_key_here
AWS_SECRET_ACCESS_KEY=your_new_secret_here
AWS_REGION=ap-south-1
```

## Note:
- `.env` is already in `.gitignore` ✓
- `aws_rekognition_matcher.py` already uses `os.getenv()` ✓
- Only test files had hardcoded credentials (now removed from history)
