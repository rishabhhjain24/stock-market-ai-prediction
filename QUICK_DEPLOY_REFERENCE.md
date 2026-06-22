# 📱 DEPLOY TO MOBILE - INSTANT REFERENCE

## ⚡ 5-MINUTE DEPLOYMENT

```
1. https://share.streamlit.io
2. "Create new app"
3. GitHub: username/repo, main branch, trading_dashboard.py
4. Click Deploy
5. Get URL: https://your-app.streamlit.app
6. Open on phone → DONE! 🎉
```

---

## 🔑 API KEYS (Optional)

Get free:
- Gemini: https://ai.google.dev
- NewsAPI: https://newsapi.org

Add to Streamlit Cloud → Settings → Secrets:
```toml
gemini_api_key = "your-key"
newsapi_key = "your-key"
```

---

## 📱 MOBILE ACCESS

1. Copy: `https://your-username-trading-dashboard.streamlit.app`
2. Open in Safari (iPhone) or Chrome (Android)
3. Bookmark it
4. Works perfectly on mobile! ✓

---

## 🆘 QUICK FIXES

| Problem | Fix |
|---------|-----|
| Deploy fails | Run: `pip freeze > requirements.txt && git push` |
| Crashes | Check logs on Streamlit Cloud dashboard |
| API error | Add to Secrets: Settings → Secrets |
| Slow | Try Railway ($5/mo) instead of free tier |

---

## 🎯 NEXT STEPS

1. Check GitHub has your code
2. Go to https://share.streamlit.io
3. Deploy `trading_dashboard.py`
4. Get your URL
5. Open on phone

**Total time: 5-15 minutes**

---

## 📖 FULL GUIDES

- `DEPLOY_5_MINUTES.md` - Quick version
- `DEPLOY_COMPLETE_GUIDE.md` - Full with troubleshooting
- `MOBILE_DEPLOYMENT_FINAL.md` - All 3 platforms

---

**READY? GO TO: https://share.streamlit.io** 🚀
