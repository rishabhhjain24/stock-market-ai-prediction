# 🚀 GITHUB & DEPLOYMENT SETUP

## Quick GitHub Setup (3 steps)

### 1️⃣ Initialize Git Repository
```bash
cd "path/to/Stock Market Prediction"

# Initialize repository
git init

# Add all files
git add .

# First commit
git commit -m "Initial commit: AI Trading Dashboard"
```

### 2️⃣ Create Repository on GitHub
- Go to https://github.com/new
- Repository name: `trading-dashboard` (or any name)
- Description: "AI-powered trading forecast with news sentiment & technical analysis"
- Choose **Public** or **Private**
- Click **Create repository**

### 3️⃣ Push to GitHub
```bash
# Add GitHub as remote (replace with your repo URL)
git remote add origin https://github.com/YOUR_USERNAME/trading-dashboard.git

# Rename branch to main (if on master)
git branch -M main

# Push code to GitHub
git push -u origin main

# Verify
git remote -v
# Should show your GitHub repo URL
```

---

## 🔄 Regular Updates

After making changes locally:
```bash
# Stage changes
git add .

# Commit with message
git commit -m "Describe your changes here"

# Push to GitHub
git push origin main

# GitHub Actions will auto-deploy (if configured)
```

---

## 🔐 Set Up Heroku Deployment (Auto-deploy on push)

### Get Heroku API Key
1. Go to https://dashboard.heroku.com/account/applications/authorizations/new
2. Create authorization → Copy API Key

### Add to GitHub Secrets
1. Go to your GitHub repo
2. Settings → Secrets and variables → Actions
3. Click **New repository secret**
4. Add two secrets:

| Name | Value |
|------|-------|
| `HEROKU_API_KEY` | Paste your Heroku API key |
| `HEROKU_APP_NAME` | Your Heroku app name (e.g., `trading-dashboard-123`) |

### Now every push to main = Auto-deploy to Heroku! 🚀

---

## 📂 File Structure for Deployment

```
your-repo/
├── api_server.py              ← Main Flask app
├── trading_forecast_engine.py ← Your existing engine
├── news_sentiment_unified.py  ← Sentiment analysis
├── Dockerfile                 ← Docker config
├── Procfile                   ← Heroku config
├── requirements-deploy.txt    ← Dependencies
├── .env.example               ← Environment template
├── .gitignore                 ← Files to exclude
├── .github/
│   └── workflows/
│       └── deploy.yml         ← CI/CD pipeline
└── README.md                  ← Project info
```

---

## 🌐 Domain Pointing (Optional)

After deployment, point your custom domain:

1. **Get Heroku URL:** `https://your-app-name.herokuapp.com`
2. **Buy domain** (Godaddy, Namecheap, etc.)
3. **Update DNS to point to Heroku**
4. **Add custom domain to Heroku:**
   ```bash
   heroku domains:add www.yourdomain.com
   ```

---

## 📊 View Live App

After deployment:
- **Heroku:** https://your-app-name.herokuapp.com
- **Railway:** URL from Railway dashboard
- **AWS:** URL from Elastic Beanstalk dashboard

**Share the link with anyone!** 📱✨

---

## 🔧 Useful Commands

```bash
# See all changes
git status

# See detailed changes
git diff

# See commit history
git log --oneline

# Undo last commit (keep changes)
git reset --soft HEAD~1

# View all branches
git branch -a

# Switch branch
git checkout branch-name

# Delete local branch
git branch -D branch-name

# Force push (use carefully!)
git push origin main --force
```

---

## 🎯 Next Steps

1. ✅ Push code to GitHub
2. ✅ Set up Heroku (or Railway/AWS)
3. ✅ Configure GitHub Actions secrets
4. ✅ Push a small change to trigger auto-deploy
5. ✅ Share app link with others
6. ✅ Monitor logs: `heroku logs --tail`

**Done! Your trading app is live & mobile-accessible!** 🎉
