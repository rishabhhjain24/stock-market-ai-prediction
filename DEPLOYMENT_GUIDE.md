# 📱 MOBILE DEPLOYMENT GUIDE
# Deploy your AI Trading Dashboard to the cloud (accessible from mobile, web, desktop)

## ⚡ QUICK START (5 minutes)

### Option 1: Deploy to Heroku (Recommended - FREE tier available)

#### Step 1: Prepare Your Code
```bash
# 1. Go to your project directory
cd "path/to/Stock Market Prediction"

# 2. Initialize git (if not already done)
git init
git add .
git commit -m "Initial trading dashboard commit"
```

#### Step 2: Create Heroku Account & Deploy
```bash
# 3. Install Heroku CLI: https://devcenter.heroku.com/articles/heroku-cli

# 4. Login to Heroku
heroku login

# 5. Create new Heroku app
heroku create your-trading-app-name

# 6. Set environment variables
heroku config:set FLASK_ENV=production
heroku config:set OPENAI_API_KEY=your_key_here  # If using OpenAI

# 7. Deploy
git push heroku main

# 8. View logs
heroku logs --tail
```

**Your app is now live at:** `https://your-trading-app-name.herokuapp.com`

---

### Option 2: Deploy to Railway.app (Easiest - GitHub integration)

#### Step 1: Push to GitHub
```bash
# If not already on GitHub:
git remote add origin https://github.com/your-username/trading-dashboard.git
git branch -M main
git push -u origin main
```

#### Step 2: Deploy on Railway
1. Visit https://railway.app
2. Sign up with GitHub
3. Create new project → Deploy from GitHub repo
4. Select your trading-dashboard repository
5. Railway auto-detects Dockerfile and deploys
6. Add environment variables in Railway dashboard
7. Done! Access via Railway's provided URL

**Railway features:**
- Auto-redeploy on GitHub push
- Free tier with 500 hours/month
- PostgreSQL database available

---

### Option 3: Deploy to AWS (Production-grade)

#### Using Elastic Beanstalk:
```bash
# 1. Install AWS CLI & EB CLI
pip install awsebcli

# 2. Initialize EB environment
eb init -p "Docker running on 64bit Amazon Linux 2" trading-dashboard

# 3. Create environment
eb create trading-env

# 4. Deploy
eb deploy

# 5. Open application
eb open
```

---

## 📱 ACCESSING FROM MOBILE

### Desktop Browser (Test locally first):
```bash
python api_server.py
# Visit: http://localhost:5000
```

### From Mobile:
1. **Get your machine IP:**
   ```bash
   ipconfig getifaddr en0  # Mac
   ipconfig                 # Windows (look for IPv4 Address)
   ```

2. **On mobile (same WiFi):**
   - Open: `http://YOUR_IP:5000`
   - Bookmark it for quick access

3. **From anywhere (Deployed):**
   - Open: `https://your-trading-app-name.herokuapp.com`
   - Works globally!

---

## 🔧 GITHUB SETUP (For auto-deployment)

### Step 1: Create GitHub Repository
```bash
# 1. Go to https://github.com/new
# 2. Create repository: trading-dashboard
# 3. Copy repository URL

# 4. Push your code
git remote add origin https://github.com/YOUR_USERNAME/trading-dashboard.git
git branch -M main
git push -u origin main
```

### Step 2: Set Up GitHub Actions (Auto-deploy)
The `.github/workflows/deploy.yml` file automatically:
- Builds Docker image
- Runs tests
- Deploys to Heroku on every push

**Configure secrets in GitHub:**
1. Go to Settings → Secrets and variables → Actions
2. Add new secrets:
   - `HEROKU_API_KEY`: Get from https://dashboard.heroku.com/account/applications/authorizations/new
   - `HEROKU_APP_NAME`: Your Heroku app name

---

## 🚀 ADVANCED DEPLOYMENT OPTIONS

### Docker Compose (Local multi-container):
```bash
# Build
docker-compose build

# Run
docker-compose up

# Access: http://localhost:5000
```

### Kubernetes (For large scale):
```bash
# Install kubectl & create k8s config file
kubectl apply -f k8s/deployment.yaml
```

### Streamlit Cloud (Keep existing Streamlit app):
```bash
# Deploy trading_dashboard.py directly
# Go to https://streamlit.io/cloud
# Connect GitHub repo
# Select trading_dashboard.py
```

---

## 📊 API ENDPOINTS (For custom integration)

### Get Market Status
```bash
curl http://localhost:5000/api/market-status
```

### Get Forecast for Symbol
```bash
curl http://localhost:5000/api/forecast/RELIANCE.NS
```

### Get Price
```bash
curl http://localhost:5000/api/price/RELIANCE.NS
```

### Get Watchlist Forecasts
```bash
curl -X POST http://localhost:5000/api/watchlist \
  -H "Content-Type: application/json" \
  -d '{"symbols": ["RELIANCE.NS", "TCS.NS", "INFY.NS"]}'
```

---

## 🔒 SECURITY CHECKLIST

- [ ] Never commit `.env` file to Git
- [ ] Use `.env.example` for templates
- [ ] Rotate API keys regularly
- [ ] Enable HTTPS (all cloud providers do this)
- [ ] Add authentication if sharing with others
- [ ] Monitor logs for errors
- [ ] Set up error alerts

---

## 🆘 TROUBLESHOOTING

### "Heroku Build Fails"
```bash
# Check logs
heroku logs --tail

# Rebuild
heroku builds:cancel
git push heroku main --force
```

### "Cannot access from mobile"
- Check firewall settings
- Ensure Flask is listening on 0.0.0.0 (not localhost)
- Verify same WiFi network for local testing
- For cloud: check security groups/firewall rules

### "Slow forecasts"
- Increase Heroku dyno size
- Enable caching in api_server.py
- Optimize ML model inference
- Consider async workers

### "Out of memory"
- Reduce batch size in watchlist processing
- Use Railway/AWS for more RAM
- Implement data streaming instead of loading all

---

## 📈 MONITORING & SCALING

### Monitor Performance
```bash
# Heroku metrics
heroku metrics

# View logs
heroku logs --tail --lines 100
```

### Scale Up
```bash
# Increase dynos
heroku dyno:scale web=2

# Upgrade to higher tier
heroku dyno:type standard-1x
```

### Custom Domain
```bash
# Add custom domain
heroku domains:add www.yourdomain.com

# Update DNS records at your domain provider
```

---

## 📞 SUPPORT

For issues:
1. Check logs: `heroku logs --tail`
2. Test locally: `python api_server.py`
3. Review firewall/security settings
4. Check API key validity

---

**🎉 Your app is now live and accessible from mobile!**
