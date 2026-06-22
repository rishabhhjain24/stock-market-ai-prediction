@echo off
REM 🚀 QUICK DEPLOYMENT SCRIPT (Windows)
REM One command to deploy your trading app!

echo 📱 Trading Dashboard Deployment Setup
echo ======================================
echo.

REM Check if git is initialized
if not exist ".git" (
    echo 1️⃣ Initializing Git Repository...
    git init
    echo ✅ Git initialized
) else (
    echo ✅ Git already initialized
)

REM Check if .env exists
if not exist ".env" (
    echo.
    echo 2️⃣ Setting up environment variables...
    copy .env.example .env
    echo ✅ Created .env from template
    echo ⚠️ Edit .env with your API keys!
) else (
    echo ✅ .env already exists
)

REM Add files to git
echo.
echo 3️⃣ Staging files for commit...
git add .
echo ✅ Files staged

REM Commit
echo.
echo 4️⃣ Committing changes...
git commit -m "Deploy trading dashboard with mobile support"
echo ✅ Committed

REM Instructions
echo.
echo ======================================
echo 📦 NEXT STEPS:
echo ======================================
echo.
echo 1. Create repository on GitHub: https://github.com/new
echo    Name it: trading-dashboard
echo.
echo 2. Push to GitHub:
echo    git remote add origin https://github.com/YOUR_USERNAME/trading-dashboard.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 3. Deploy to Heroku:
echo    heroku login
echo    heroku create your-trading-app
echo    git push heroku main
echo.
echo 4. Access your app:
echo    Local: http://localhost:5000
echo    Cloud: https://your-trading-app.herokuapp.com
echo.
echo ✅ Setup complete! Follow steps above to deploy.

pause
