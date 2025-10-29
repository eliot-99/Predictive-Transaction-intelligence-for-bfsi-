# Repository Configuration - FraudGuard BFSI

## Project Overview
Production-ready banking fraud detection platform combining ML models (XGBoost, LightGBM, ONNX) with rule-based fraud signatures.

## Technology Stack
- **Backend**: Flask 3.0 (WebApp), FastAPI 0.115 (API)
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: Bootstrap 5, Chart.js, Animate.css
- **ML**: ONNX Runtime, scikit-learn, joblib
- **Deployment**: Render (free tier with auto-scaling)

## Repository Structure
```
project-root/
├── api/                          # FastAPI Fraud Detection Service
│   ├── main.py                   # Core FastAPI app (200+ lines)
│   ├── requirements.txt
│   ├── fraud_model.onnx          # ML model artifact
│   └── preprocessor.pkl          # Feature scaler
│
├── WebApp/                       # Flask Web Application
│   ├── app.py                    # Main Flask app (600+ lines)
│   ├── config.py                 # Configuration management
│   ├── requirements.txt
│   ├── .env.example
│   ├── setup.py                  # Setup script
│   │
│   ├── templates/                # 9 HTML templates
│   │   ├── base.html             # Navigation & base layout
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── dashboard.html        # Main dashboard
│   │   ├── predict.html          # 25-field prediction form
│   │   ├── history.html          # Transaction history
│   │   ├── chatbot.html          # AI assistant
│   │   ├── about.html
│   │   ├── 404.html
│   │   └── 500.html
│   │
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css         # Banking-grade CSS (700+ lines)
│   │   └── js/
│   │       └── script.js         # JavaScript utilities (600+ lines)
│   │
│   ├── models/
│   │   └── user.db               # SQLite database (auto-created)
│   │
│   └── README.md
│
├── render.yaml                   # Deployment configuration (2 services)
├── DEPLOYMENT.md                 # Detailed deployment guide
├── README_FRAUDGUARD.md          # Main README
├── .gitignore
└── .zencoder/
    └── rules/
        └── repo.md              # This file
```

## Testing Framework
**targetFramework: Playwright**

### Test Coverage Areas
1. **Authentication Tests**
   - Signup validation (email, password, bank_id)
   - Login with credentials
   - Session management
   - Logout functionality

2. **Dashboard Tests**
   - Statistics calculation (today's tx, fraud rate, avg risk)
   - Chart rendering (24-hour trend)
   - Recent alerts display
   - Navigation links

3. **Prediction Tests**
   - Form submission with 25 fields
   - API integration with external service
   - Result display (risk level, score, alerts)
   - Database storage

4. **History Tests**
   - Pagination (10 per page)
   - Filtering by risk/location
   - CSV export
   - Transaction detail modal

5. **Chatbot Tests**
   - Message sending
   - AI response logic
   - Quick questions
   - Conversation history

6. **Error Handling**
   - 404 page
   - 500 error page
   - API timeout/failure
   - Missing fields validation

## Key Routes & Endpoints

### Flask Routes (WebApp)
```
GET  /                          → Redirect to dashboard/login
GET  /login                     → Login page
POST /login                     → Process login
GET  /signup                    → Signup page
POST /signup                    → Process registration
GET  /dashboard                 → Main dashboard (protected)
GET  /predict                   → Prediction form (protected)
POST /predict                   → Submit prediction (protected)
GET  /history                   → Transaction history (protected)
GET  /export-csv               → CSV export (protected)
GET  /chatbot                  → Chat interface (protected)
POST /api/chat                 → Chat endpoint (protected)
GET  /api/history              → JSON history (protected)
GET  /about                    → About page
GET  /404                      → 404 error
GET  /500                      → 500 error
GET  /logout                   → Logout
```

### FastAPI Routes (API)
```
GET  /                         → API info
GET  /health                   → Health check
POST /detect                   → Fraud detection
GET  /docs                     → Swagger UI
```

## Database Schema

### Users Table
```python
id (Primary Key)
name (String, 100, NOT NULL)
email (String, 100, UNIQUE, NOT NULL)
bank_id (String, 50, UNIQUE, NOT NULL)
password_hash (String, 255, NOT NULL)
created_at (DateTime, default=UTC now)
```

### Transactions Table
```python
id (Primary Key)
user_id (Foreign Key → Users.id)
transaction_id (String, 50, UNIQUE)
amount (Float)
location (String, 100)
fraud_probability (Float)
risk_score (Float)
alert_triggered (Boolean)
alert_reasons (String, 500)
prediction (Integer)
created_at (DateTime)
```

## Configuration Files

### Environment Variables (.env)
```
FLASK_ENV=development
SECRET_KEY=dev-secret-key
DEBUG=False
FRAUD_API_URL=https://fraud-detection-api.onrender.com/detect
FRAUD_API_TIMEOUT=10
PORT=5000
```

### Deployment (render.yaml)
- Two services: FastAPI API + Flask WebApp
- Python 3.11 runtime
- Free tier with auto-deployment
- Auto-scaling on demand

## Color Scheme (Banking Professional)
- Primary: #003087 (Navy Blue)
- Secondary: #00A3E0 (Sky Blue)
- Success: #28a745 (Green)
- Danger: #dc3545 (Red)
- Warning: #ffc107 (Yellow)
- Background: #f8f9fa (Light Gray)

## Security Features
✅ Session-based authentication
✅ Password hashing (Werkzeug)
✅ HTTPS/SSL (Render)
✅ SQL injection prevention (SQLAlchemy ORM)
✅ XSS protection (Jinja2)
✅ CSRF protection ready
✅ Secure headers configured

## API Integration
### External Fraud Detection API
- URL: `https://fraud-detection-api.onrender.com/detect`
- Method: POST
- Payload: 25 transaction fields
- Response: Risk score, fraud probability, alert reasons
- Timeout: 10 seconds
- Error handling: Graceful fallback with user notification

## Performance Metrics
- Response Time: <200ms local, <500ms deployed
- Concurrent Users: 1000+
- ML Inference: <100ms
- Database Queries: Optimized with indexes
- Memory Usage: ~200MB (WebApp) + ~300MB (API)

## Known Limitations
- Free tier: Auto-sleep after 15 min inactivity
- SQLite: Single writer (upgrade to PostgreSQL for concurrent writes)
- Session: 7-day default persistence
- Transactions: No real-time alerts (polling required)
- Models: Static (no versioning yet)

## Development Guidelines

### Code Style
- PEP 8 (Python)
- Bootstrap class naming conventions
- JavaScript ES6+
- Jinja2 template best practices

### Testing
- Use Playwright for E2E tests
- Place tests in `tests/` directory
- Target selectors should be stable (avoid XPath)
- Mock external API calls

### Documentation
- Docstrings for all functions
- Inline comments for complex logic
- README for each module
- API documentation via FastAPI /docs

## Deployment Checklist
- [ ] Code committed to main branch
- [ ] Environment variables configured
- [ ] Model files present and committed
- [ ] Requirements.txt updated
- [ ] render.yaml in place
- [ ] .gitignore configured
- [ ] Database migrations tested
- [ ] All routes tested
- [ ] Static files served correctly
- [ ] Error pages configured

## Maintenance
- Monitor Render logs weekly
- Update dependencies monthly
- Review security advisories
- Backup database monthly
- Test deployment procedure quarterly

## Support & Resources
- Render Docs: https://render.com/docs
- FastAPI Docs: https://fastapi.tiangolo.com
- Flask Docs: https://flask.palletsprojects.com
- SQLAlchemy Docs: https://docs.sqlalchemy.org
- Bootstrap Docs: https://getbootstrap.com/docs

---
Last Updated: 2025-01-01
Version: 1.0.0