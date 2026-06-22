# 📦 GITHUB SETUP FOR STREAMLIT CLOUD DEPLOYMENT

## This guide shows exact steps to get your code on GitHub so Streamlit Cloud can access it

---

## 🔧 BEFORE YOU START

Make sure you have:
- ✅ Git installed (Windows comes with it)
- ✅ GitHub account (free at github.com)
- ✅ Your project folder with `trading_dashboard.py`

---

## STEP 1: Create GitHub Repository

1. **Go to:** https://github.com/new
2. **Enter:**
   - Repository name: `trading-dashboard`
   - Description: "AI Trading Dashboard - Streamlit App"
   - Choose: **Public** (so Streamlit Cloud can access)
   - Click: **Create repository**

3. **You'll see a page with commands. Copy the HTTPS URL**
   ```
   https://github.com/YOUR_USERNAME/trading-dashboard.git
   ```

---

## STEP 2: Push Your Code to GitHub

### Open PowerShell in your project folder:

```powershell
# Navigate to your project
cd "C:\Users\Rishabh Jain\OneDrive\Desktop\Stock Market Prediction"

# Check if git is already initialized
git status
```

**If you see "fatal: not a git repository", then:**

```powershell
# Initialize git locally
git init

# Add all your files
git add .

# Make first commit
git commit -m "Initial commit: AI Trading Dashboard ready for Streamlit Cloud"

# Connect to GitHub (replace with YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/trading-dashboard.git

# Rename default branch to main (if needed)
git branch -M main

# Push to GitHub
git push -u origin main
```

**If you already have git:**

```powershell
# Just push any new changes
git add .
git commit -m "Ready for Streamlit deployment"
git push origin main
```

---

## ✅ VERIFY ON GITHUB

1. Go to: `https://github.com/YOUR_USERNAME/trading-dashboard`
2. You should see your files:
   - ✅ `trading_dashboard.py`
   - ✅ `trading_forecast_engine.py`
   - ✅ `requirements.txt`
   - ✅ All other files

---

## 🚀 CONNECT TO STREAMLIT CLOUD

Once code is on GitHub:

1. **Go to:** https://streamlit.io/cloud
2. **Click:** "New app"
3. **Select:**
   - Repository: `YOUR_USERNAME/trading-dashboard`
   - Branch: `main`
   - File: `trading_dashboard.py`
4. **Deploy!**

---

## 🔄 REGULAR UPDATES

Every time you make changes:

```powershell
# Make your changes to files locally

# Stage changes
git add .

# Commit with a message
git commit -m "Describe what you changed"

# Push to GitHub
git push origin main

# Streamlit auto-redeploys! (1-2 minutes)
```

---

## 🐛 COMMON ISSUES

### "fatal: not a git repository"
```powershell
# Solution: Initialize git first
git init
```

### "error: The following untracked working tree files would be overwritten"
```powershell
# Solution: Add files first
git add .
git commit -m "Fix"
```

### "Authentication failed for GitHub"
```
Solution:
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Create a new token
3. Use it as password when pushing
```

### "Permission denied (publickey)"
```
Solution:
1. Generate SSH key (GitHub docs)
2. Or use HTTPS URL instead of SSH
```

---

## ✅ CHECKLIST

- [ ] GitHub account created
- [ ] Repository created on GitHub
- [ ] Git initialized locally (`git init`)
- [ ] Code pushed to GitHub (`git push origin main`)
- [ ] Can see files on GitHub.com
- [ ] Ready for Streamlit Cloud deployment

---

## 📞 SUPPORT

**View git status anytime:**
```powershell
git status
```

**See your commits:**
```powershell
git log --oneline
```

**Check remote connection:**
```powershell
git remote -v
```

---

**Next: Deploy to Streamlit Cloud (see STREAMLIT_QUICK_DEPLOY.md)** 🚀
