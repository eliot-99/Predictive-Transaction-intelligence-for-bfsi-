# FraudGuard BFSI - Complete Deployment Guide

This guide covers deploying the entire FraudGuard BFSI platform (FastAPI + Flask) to Render.

## Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│              FraudGuard BFSI Platform              │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ┌──────────────────────────────────────────────┐  │
│  │   Flask Web Application (WebApp/)            │  │
│  │   - Dashboard, predict, history, chatbot     │  │
│  │   - User authentication & sessions           │  │
│  │   - SQLite database (user.db)                │  │
│  └──────────────────────────────────────────────┘  │
│              ↓ (HTTP POST)                         │
│  ┌──────────────────────────────────────────────┐  │
│  │   FastAPI Fraud Detection Service (api/)    │  │
│  │   - Real-time ML model inference (ONNX)     │  │
│  │   - Rule-based fraud signatures              │  │
│  │   - Transaction evaluation                   │  │
│  └──────────────────────────────────────────────┘  │
│              ↓ (ML Models + Joblib)               │
│  ┌──────────────────────────────────────────────┐  │
│  │   Model Artifacts                            │  │
│  │   - fraud_model.onnx (99.1% AUC)             │  │
│  │   - preprocessor.pkl (feature scaler)        │  │
│  └──────────────────────────────────────────────┘  │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Pre-Deployment Checklist

- [ ] GitHub repository created and code pushed
- [ ] Render account created (free tier available)
- [ ] Model files present: `api/fraud_model.onnx`, `api/preprocessor.pkl`
- [ ] Environment variables documented
- [ ] Requirements files updated: `api/requirements.txt`, `WebApp/requirements.txt`
- [ ] `.gitignore` configured to exclude sensitive files
- [ ] `render.yaml` in repository root

## Step 1: Prepare Repository

### 1.1 Create `.gitignore`
```bash
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/
dist/
build/

# Flask
instance/
.webassets-cache

# Database
*.db
*.sqlite
*.sqlite3

# Environment
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Compiled
*.pyc

# Node (if using frontend build)
node_modules/
npm-debug.log
EOF
```

### 1.2 Verify Project Structure
```
predictive-transaction-intelligence-for-bfsi/
├── api/
│   ├── main.py
│   ├── requirements.txt
│   ├── fraud_model.onnx          # ✅ Must exist
│   └── preprocessor.pkl           # ✅ Must exist
├── WebApp/
│   ├── app.py
│   ├── config.py
│   ├── requirements.txt
│   ├── templates/
│   ├── static/
│   └── models/
│       └── user.db (auto-created)
├── render.yaml                     # ✅ Deployment config
├── .gitignore
└── README.md
```

### 1.3 Commit and Push
```bash
git add -A
git commit -m "feat: Add FraudGuard BFSI production-ready platform"
git push origin main
```

## Step 2: Deploy on Render

### 2.1 Create Render Account
1. Go to https://render.com
2. Sign up with GitHub account
3. Authorize repository access

### 2.2 Create Services via Dashboard

#### Option A: Manual Service Creation (Recommended first time)

**FastAPI Service:**
1. Dashboard → "New +" → "Web Service"
2. Select your GitHub repo
3. Configuration:
   - **Name**: `fraudguard-api`
   - **Environment**: Python 3.11
   - **Build Command**: `pip install -r api/requirements.txt`
   - **Start Command**: `gunicorn -w 4 -b 0.0.0.0:$PORT api.main:app`
   - **Region**: Oregon (free tier)
   - **Plan**: Free

4. Environment Variables:
   ```
   PORT=8000
   PYTHONUNBUFFERED=true
   MODEL_PATH=api/fraud_model.onnx
   PREPROC_PATH=api/preprocessor.pkl
   ```

**Flask Service:**
1. Dashboard → "New +" → "Web Service"
2. Select your GitHub repo
3. Configuration:
   - **Name**: `fraudguard-webapp`
   - **Environment**: Python 3.11
   - **Build Command**: `pip install -r WebApp/requirements.txt`
   - **Start Command**: `cd WebApp && gunicorn -w 4 -b 0.0.0.0:$PORT app:app`
   - **Region**: Oregon (free tier)
   - **Plan**: Free

4. Environment Variables:
   ```
   PORT=5000
   PYTHONUNBUFFERED=true
   SECRET_KEY=<generate-secure-random-string>
   FRAUD_API_URL=https://fraudguard-api.onrender.com/detect
   FLASK_ENV=production
   ```

#### Option B: Auto-Deploy with render.yaml

If you have `render.yaml` in root:
```bash
# Just push to trigger auto-deployment
git push origin main

# Both services will be created automatically
```

### 2.3 Monitor Deployment

1. **In Render Dashboard:**
   - Select service → "Logs" tab
   - Monitor build and startup logs
   - Look for errors like missing files

2. **Watch for Messages:**
   ```
   ✓ Build succeeded
   ✓ Service started on port 8000
   ✓ App deployed successfully
   ```

3. **Test API:**
   ```bash
   curl https://fraudguard-api.onrender.com/health
   # Expected: {"status": "ok"}
   
   curl https://fraudguard-api.onrender.com/
   # Expected: {"status": "LIVE", "model": "fraud_model.onnx", ...}
   ```

4. **Test Web App:**
   ```bash
   curl https://fraudguard-webapp.onrender.com/
   # Should redirect to /login
   ```

## Step 3: Database Initialization

### 3.1 Access Flask Shell (Render)

Option 1: Via Render Shell
```bash
# In Render Dashboard → fraudguard-webapp → Shell
# Then run:
python
>>> from app import app, db
>>> app.app_context().push()
>>> db.create_all()
>>> exit()
```

Option 2: Via Flask CLI
```bash
# After deployment, trigger initialization via HTTP
# Or run local then sync with Render
```

### 3.2 Seed Demo User
```bash
python
>>> from app import app, User, db
>>> app.app_context().push()
>>> user = User(name='Demo Bank', email='demo@fraudguard.com', bank_id='DEMO001')
>>> user.set_password('demo123')
>>> db.session.add(user)
>>> db.session.commit()
>>> exit()
```

## Step 4: Production Configuration

### 4.1 SSL/HTTPS
✅ **Automatic** - Render provides free SSL certificate for all services

### 4.2 Custom Domain (Optional)
1. Render Dashboard → Settings → Custom Domain
2. Add your domain (e.g., `fraudguard.yourdomain.com`)
3. Update DNS records as instructed

### 4.3 Environment Variables in Production

Update in Render Dashboard:
```
SECRET_KEY=<use-random-secure-string>
FRAUD_API_URL=https://fraudguard-api.onrender.com/detect
FLASK_ENV=production
DEBUG=False
```

Generate secure SECRET_KEY:
```python
python -c "import secrets; print(secrets.token_hex(32))"
# Use output as SECRET_KEY
```

### 4.4 Scaling (if needed, upgrade plan)

Current: Free tier
- 0.5 CPU
- 512 MB RAM
- Auto-sleep after 15 min inactivity
- No idle timeout with "Paid" plan

To enable continuous operation:
1. Dashboard → Service → Settings
2. Upgrade to **Starter ($7/month)** or higher

## Step 5: Post-Deployment Verification

### 5.1 Health Checks

```bash
# Check API
curl https://fraudguard-api.onrender.com/health
# Status: {"status": "ok"}

# Check Web App
curl https://fraudguard-webapp.onrender.com/login
# Status: 200 (returns login page HTML)

# Test fraud detection
curl -X POST https://fraudguard-api.onrender.com/detect \
  -H "Content-Type: application/json" \
  -d '{
    "User_ID": 1,
    "Transaction_Amount": 75000000,
    "Transaction_Location": "Russia",
    "Merchant_ID": 1,
    "Device_ID": 1,
    "Card_Type": "Credit",
    "Transaction_Currency": "UZS",
    "Transaction_Status": "Completed",
    "Previous_Transaction_Count": 5,
    "Distance_Between_Transactions_km": 0,
    "Time_Since_Last_Transaction_min": 60,
    "Authentication_Method": "PIN",
    "Transaction_Velocity": 10,
    "Transaction_Category": "Shopping",
    "Transaction_Hour": 2,
    "Transaction_Day": 15,
    "Transaction_Month": 6,
    "Transaction_Weekday": 2,
    "Log_Transaction_Amount": 17.8,
    "Velocity_Distance_Interact": 0,
    "Amount_Velocity_Interact": 750000000,
    "Time_Distance_Interact": 0,
    "Hour_sin": 0.909,
    "Hour_cos": -0.415,
    "Weekday_sin": 0.782,
    "Weekday_cos": 0.623
  }'

# Expected: High-risk alert with fraud signatures
```

### 5.2 Web App Full Flow

1. **Sign Up**: https://fraudguard-webapp.onrender.com/signup
   - Create new bank account
   - Use credentials to login

2. **Dashboard**: https://fraudguard-webapp.onrender.com/dashboard
   - View statistics and real-time chart
   - Should show 0 transactions initially

3. **Predict**: https://fraudguard-webapp.onrender.com/predict
   - Fill form with transaction data
   - Submit to get fraud risk assessment

4. **History**: https://fraudguard-webapp.onrender.com/history
   - View prediction history
   - Export to CSV

5. **Chatbot**: https://fraudguard-webapp.onrender.com/chatbot
   - Ask about fraud risks
   - Get AI responses

### 5.3 Demo Flow

1. **Login with Demo Account**
   ```
   Email: demo@fraudguard.com
   Password: demo123
   ```

2. **Test Prediction (High-Risk)**
   - User ID: 99999
   - Amount: 75,000,000 UZS
   - Location: Russia
   - Hour: 2 (night time)
   - Expected: ✓ HIGH RISK ALERT

3. **Test Prediction (Safe)**
   - User ID: 1
   - Amount: 1,000,000 UZS
   - Location: Tashkent
   - Hour: 12 (daytime)
   - Expected: ✓ SAFE

## Step 6: Monitoring & Maintenance

### 6.1 Logs and Errors

**View Logs in Render:**
```bash
# Web App
Dashboard → fraudguard-webapp → Logs

# API
Dashboard → fraudguard-api → Logs
```

**Common Issues:**

| Issue | Cause | Solution |
|-------|-------|----------|
| `ModuleNotFoundError` | Missing dependency | Check `requirements.txt` |
| `FileNotFoundError` | Missing model files | Verify files in git |
| Connection timeout | API not responding | Check `FRAUD_API_URL` |
| 503 Service Unavailable | Service restarting | Wait 1-2 minutes |
| Database locked | Concurrent writes | Verify app logic |

### 6.2 Auto-Deployment

Every push to `main` triggers deployment:
```bash
git push origin main
# Deployment starts automatically
# Takes 3-5 minutes for both services
```

To disable auto-deploy:
- Render Dashboard → Settings → Disable Auto-Deploy

### 6.3 Performance Monitoring

**Render Metrics:**
- Dashboard → Service → Metrics
- Monitor CPU, RAM, Connections
- Upgrade plan if consistently high usage

**Application Metrics:**
- Response times (check logs)
- Error rates (check logs)
- User count (via database queries)

### 6.4 Backup Strategy

**Database Backups (SQLite):**
```bash
# Download backup from Render
# Option 1: Export via Flask shell
# Option 2: Use Render's built-in download

# Recommended: Set up automated backups to S3/Google Cloud
```

## Step 7: Security Hardening

### 7.1 Secrets Management

**Never commit secrets to git:**
```bash
# Bad (Don't do this)
FRAUD_API_URL=https://api.example.com

# Good (Use Render Environment Variables)
# Set in Dashboard, not in code
```

### 7.2 HTTPS Enforcement

```python
# In app.py
app.config['SESSION_COOKIE_SECURE'] = True  # Render handles HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
```

### 7.3 Rate Limiting (Optional)

```python
# Add to app.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)
```

### 7.4 Regular Updates

- [ ] Update dependencies monthly
- [ ] Monitor security advisories
- [ ] Review logs for suspicious activity
- [ ] Patch critical vulnerabilities immediately

## Step 8: Troubleshooting Deployment

### Build Failures

**Error: "pip: command not found"**
```bash
# Solution: Use correct Python version in render.yaml
runtime: python-3.11  # Supported versions only
```

**Error: "ONNX Runtime not found"**
```bash
# Solution: Add to api/requirements.txt
onnxruntime==1.20.1
```

### Runtime Failures

**Error: "fraud_model.onnx not found"**
```bash
# Solution 1: Commit file to git
git add api/fraud_model.onnx
git commit -m "Add model artifacts"

# Solution 2: Check MODEL_PATH env var
# Dashboard → Environment Variables
# Verify MODEL_PATH=api/fraud_model.onnx
```

**Error: "Connection refused" from WebApp to API**
```bash
# Solution: Update FRAUD_API_URL to correct Render URL
# Get from: Dashboard → fraudguard-api → URL
# Format: https://fraudguard-api.onrender.com
```

### Database Issues

**Error: "Database is locked"**
```bash
# Solution: Restart service
# Dashboard → Service → Manual Deploy
# Or wait for auto-sleep/wake cycle
```

## Cost Estimation

| Component | Tier | Cost/Month |
|-----------|------|-----------|
| FastAPI Service | Free | $0 |
| Flask Service | Free | $0 |
| Database | SQLite (included) | $0 |
| Bandwidth | Free tier | $0 |
| **Total** | | **$0** |

**Upgrade Path:**
- Free → Starter: $7/month (for continuous operation)
- Starter → Professional: $25/month (production-grade)

## Next Steps

1. ✅ Deploy platform to Render
2. ✅ Test all user flows
3. ✅ Set up monitoring and alerts
4. ✅ Configure custom domain
5. ✅ Enable automatic backups
6. ✅ Document operational procedures
7. ✅ Train support team
8. ✅ Plan capacity expansion

## Support & Resources

- 📚 [Render Documentation](https://render.com/docs)
- 🐛 [GitHub Issues](https://github.com/yourusername/fraudguard-bfsi/issues)
- 💬 [Community Support](https://render.com/community)
- 📧 Support: contact@fraudguard.bfsi

---

**Successfully deployed!** 🎉

Your FraudGuard BFSI platform is now live and ready for banking fraud detection.