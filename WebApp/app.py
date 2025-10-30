"""
FraudGuard BFSI - Banking Fraud Detection Web Platform
Main Flask Application
"""
import os
import csv
from datetime import datetime
from io import StringIO, BytesIO
from functools import wraps

import requests
from flask import (
    Flask, render_template, request, redirect, url_for, 
    flash, session, jsonify, send_file, g
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash
import logging

# Initialize Flask app and database
app = Flask(__name__)
app.config.from_object('config.DevelopmentConfig')
db = SQLAlchemy(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== DATABASE MODELS ====================
class User(db.Model):
    """User model for authentication"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    bank_id = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    transactions = db.relationship('Transaction', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password"""
        return check_password_hash(self.password_hash, password)

class Transaction(db.Model):
    """Transaction history model"""
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    transaction_id = db.Column(db.String(50), unique=True, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    location = db.Column(db.String(100), nullable=False)
    fraud_probability = db.Column(db.Float, nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    alert_triggered = db.Column(db.Boolean, default=False)
    alert_reasons = db.Column(db.String(500))  # JSON string
    prediction = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'location': self.location,
            'fraud_probability': self.fraud_probability,
            'risk_score': self.risk_score,
            'alert_triggered': self.alert_triggered,
            'alert_reasons': self.alert_reasons,
            'prediction': self.prediction,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

# ==================== AUTHENTICATION HELPERS ====================
def login_required(f):
    """Decorator to protect routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in first.', 'warning')
            return redirect(url_for('login'))
        
        # Load user into g for use in template
        g.user = User.query.get(session['user_id'])
        if not g.user:
            session.clear()
            flash('User not found.', 'danger')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

# ==================== CONTEXT PROCESSORS ====================
@app.before_request
def before_request():
    """Before each request"""
    if 'user_id' in session:
        g.user = User.query.get(session['user_id'])
    else:
        g.user = None

@app.context_processor
def inject_user():
    """Inject user into all templates"""
    return {'current_user': g.user}

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Home page - redirect to dashboard if logged in"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """User signup"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        bank_id = request.form.get('bank_id', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validation
        if not all([name, email, bank_id, password, confirm_password]):
            flash('All fields are required.', 'danger')
            return redirect(url_for('signup'))
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'danger')
            return redirect(url_for('signup'))
        
        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('signup'))
        
        # Check if user exists
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'warning')
            return redirect(url_for('login'))
        
        if User.query.filter_by(bank_id=bank_id).first():
            flash('Bank ID already registered.', 'warning')
            return redirect(url_for('signup'))
        
        # Create new user
        try:
            user = User(name=name, email=email, bank_id=bank_id)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            
            flash('Signup successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Signup error: {e}")
            flash('An error occurred during signup. Please try again.', 'danger')
            return redirect(url_for('signup'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        # Validation
        if not email or not password:
            flash('Email and password required.', 'danger')
            return redirect(url_for('login'))
        
        # Check user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            flash('Invalid email or password.', 'danger')
            return redirect(url_for('login'))
        
        # Set session
        session['user_id'] = user.id
        session.permanent = True
        app.permanent_session_lifetime = __import__('datetime').timedelta(days=7)
        
        flash(f'Welcome back, {user.name}!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """User logout"""
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    # Get statistics
    today = datetime.utcnow().date()
    
    # Today's transactions
    today_txs = Transaction.query.filter(
        Transaction.user_id == g.user.id,
        db.func.date(Transaction.created_at) == today
    ).all()
    
    today_count = len(today_txs)
    fraud_count = sum(1 for tx in today_txs if tx.alert_triggered)
    fraud_rate = (fraud_count / today_count * 100) if today_count > 0 else 0
    
    # High-risk alerts
    high_risk = Transaction.query.filter(
        Transaction.user_id == g.user.id,
        Transaction.alert_triggered == True
    ).count()
    
    # Average risk score
    avg_risk = db.session.query(db.func.avg(Transaction.risk_score)).filter(
        Transaction.user_id == g.user.id
    ).scalar() or 0
    
    # Recent alerts (last 5)
    recent_alerts = Transaction.query.filter_by(
        user_id=g.user.id,
        alert_triggered=True
    ).order_by(Transaction.created_at.desc()).limit(5).all()
    
    # Mock time-series data for chart (last 24 hours)
    from random import randint
    chart_data = {
        'labels': [f'{i}:00' for i in range(24)],
        'data': [round(randint(10, 95) / 100, 2) for _ in range(24)]
    }
    
    return render_template('dashboard.html',
                         today_count=today_count,
                         fraud_rate=round(fraud_rate, 1),
                         high_risk=high_risk,
                         avg_risk=round(avg_risk, 2),
                         recent_alerts=recent_alerts,
                         chart_data=chart_data)

@app.route('/predict', methods=['GET', 'POST'])
@login_required
def predict():
    """Fraud prediction form"""
    if request.method == 'POST':
        try:
            # Collect form data (25 fields from API schema)
            payload = {
                'User_ID': int(request.form.get('User_ID', 1)),
                'Transaction_Amount': float(request.form.get('Transaction_Amount', 0)),
                'Transaction_Location': request.form.get('Transaction_Location', 'Tashkent'),
                'Merchant_ID': int(request.form.get('Merchant_ID', 1)),
                'Device_ID': int(request.form.get('Device_ID', 1)),
                'Card_Type': request.form.get('Card_Type', 'Credit'),
                'Transaction_Currency': request.form.get('Transaction_Currency', 'UZS'),
                'Transaction_Status': request.form.get('Transaction_Status', 'Completed'),
                'Previous_Transaction_Count': int(request.form.get('Previous_Transaction_Count', 5)),
                'Distance_Between_Transactions_km': float(request.form.get('Distance_Between_Transactions_km', 0)),
                'Time_Since_Last_Transaction_min': int(request.form.get('Time_Since_Last_Transaction_min', 60)),
                'Authentication_Method': request.form.get('Authentication_Method', 'PIN'),
                'Transaction_Velocity': int(request.form.get('Transaction_Velocity', 1)),
                'Transaction_Category': request.form.get('Transaction_Category', 'Shopping'),
                'Transaction_Hour': int(request.form.get('Transaction_Hour', 12)),
                'Transaction_Day': int(request.form.get('Transaction_Day', 15)),
                'Transaction_Month': int(request.form.get('Transaction_Month', 6)),
                'Transaction_Weekday': int(request.form.get('Transaction_Weekday', 2)),
                'Log_Transaction_Amount': float(request.form.get('Log_Transaction_Amount', 0)),
                'Velocity_Distance_Interact': float(request.form.get('Velocity_Distance_Interact', 0)),
                'Amount_Velocity_Interact': float(request.form.get('Amount_Velocity_Interact', 0)),
                'Time_Distance_Interact': float(request.form.get('Time_Distance_Interact', 0)),
                'Hour_sin': float(request.form.get('Hour_sin', 0)),
                'Hour_cos': float(request.form.get('Hour_cos', 1)),
                'Weekday_sin': float(request.form.get('Weekday_sin', 0)),
                'Weekday_cos': float(request.form.get('Weekday_cos', 1)),
            }
            
            # Call external API
            logger.info(f"Calling fraud detection API with payload: {payload}")
            response = requests.post(
                app.config['FRAUD_API_URL'],
                json=payload,
                timeout=app.config['FRAUD_API_TIMEOUT']
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"API Response: {result}")
            
            # Save to database
            transaction = Transaction(
                user_id=g.user.id,
                transaction_id=str(result.get('Transaction_ID', int(datetime.utcnow().timestamp() * 1000))),
                amount=payload['Transaction_Amount'],
                location=payload['Transaction_Location'],
                fraud_probability=result.get('Fraud_Probability', 0),
                risk_score=result.get('Final_Risk_Score', 0),
                alert_triggered=result.get('alert_triggered', False),
                alert_reasons=','.join(result.get('alert_reasons', [])),
                prediction=result.get('isFraud_pred', 0)
            )
            db.session.add(transaction)
            db.session.commit()
            
            # Determine risk level
            risk_level = 'SAFE'
            risk_class = 'success'
            if result.get('alert_triggered'):
                risk_level = 'HIGH'
                risk_class = 'danger'
            elif result.get('Final_Risk_Score', 0) > 0.4:
                risk_level = 'MEDIUM'
                risk_class = 'warning'
            
            flash('Prediction completed successfully!', 'success')
            return render_template('predict.html',
                                 result=result,
                                 payload=payload,
                                 risk_level=risk_level,
                                 risk_class=risk_class,
                                 show_result=True,
                                 now=datetime.utcnow())
        
        except requests.exceptions.RequestException as e:
            logger.error(f"API call failed: {e}")
            flash(f'API Error: Unable to reach fraud detection service. {str(e)}', 'danger')
            return render_template('predict.html', show_result=False)
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            flash(f'Error: {str(e)}', 'danger')
            return render_template('predict.html', show_result=False)
    
    # Render form with defaults
    return render_template('predict.html', show_result=False)

@app.route('/history')
@login_required
def history():
    """Transaction history"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Get transactions with pagination
    paginated = Transaction.query.filter_by(user_id=g.user.id).order_by(
        Transaction.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    transactions = paginated.items
    
    return render_template('history.html',
                         transactions=transactions,
                         page=page,
                         total_pages=paginated.pages,
                         total_transactions=paginated.total,
                         max=max,
                         min=min)

@app.route('/api/history')
@login_required
def api_history():
    """API endpoint for history data (JSON)"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    paginated = Transaction.query.filter_by(user_id=g.user.id).order_by(
        Transaction.created_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    return jsonify({
        'data': [tx.to_dict() for tx in paginated.items],
        'page': page,
        'per_page': per_page,
        'total': paginated.total,
        'pages': paginated.pages
    })

@app.route('/export-csv')
@login_required
def export_csv():
    """Export transaction history to CSV"""
    try:
        transactions = Transaction.query.filter_by(user_id=g.user.id).order_by(
            Transaction.created_at.desc()
        ).all()
        
        # Create CSV in memory
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Transaction ID', 'Date', 'Amount (UZS)', 'Location', 
                        'Fraud Probability', 'Risk Score', 'Alert', 'Reasons'])
        
        for tx in transactions:
            writer.writerow([
                tx.transaction_id,
                tx.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                f"{tx.amount:,.2f}",
                tx.location,
                f"{tx.fraud_probability:.1%}",
                f"{tx.risk_score:.2f}",
                'YES' if tx.alert_triggered else 'NO',
                tx.alert_reasons or 'N/A'
            ])
        
        # Convert StringIO to BytesIO
        output.seek(0)
        bytes_output = BytesIO(output.getvalue().encode('utf-8'))
        bytes_output.seek(0)
        
        return send_file(
            bytes_output,
            mimetype='text/csv',
            as_attachment=True,
            attachment_filename=f'fraudguard_export_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        logger.error(f"CSV export error: {e}\n{error_msg}")
        print(f"CSV export error: {e}\n{error_msg}")
        flash('Error exporting CSV.', 'danger')
        return redirect(url_for('history'))

@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    """Chatbot API endpoint"""
    try:
        user_message = request.json.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': 'Empty message'}), 400
        
        # Simple chatbot logic based on keywords
        message_lower = user_message.lower()
        
        # Default response
        response = {
            'bot_message': 'Thank you for your question. How can FraudGuard help protect your bank today?',
            'type': 'info'
        }
        
        # Risk assessment keywords
        if any(word in message_lower for word in ['risk', 'safe', 'fraud', 'dangerous', 'suspicious']):
            if any(word in message_lower for word in ['million', 'large', 'high', 'big']):
                response = {
                    'bot_message': '⚠️ HIGH RISK ALERT: Large transactions may trigger fraud alerts, especially if combined with night hours or foreign locations. Always verify with your bank!',
                    'type': 'danger'
                }
            else:
                response = {
                    'bot_message': '✅ Risk assessment: Your transaction appears safe based on normal patterns. Monitor for unusual activity.',
                    'type': 'success'
                }
        
        # Location keywords
        elif any(word in message_lower for word in ['russia', 'turkey', 'usa', 'china', 'uae', 'foreign', 'international']):
            response = {
                'bot_message': '🌍 Foreign transactions may trigger alerts if combined with high amounts or unusual hours. Always verify location and amount before confirming.',
                'type': 'warning'
            }
        
        # Time keywords
        elif any(word in message_lower for word in ['night', 'midnight', 'early', 'morning', '2am', '3am', '4am']):
            response = {
                'bot_message': '🌙 Night transactions (12 AM - 5 AM) are flagged as potentially risky. Combine with other factors for full risk assessment.',
                'type': 'warning'
            }
        
        # Features keywords
        elif any(word in message_lower for word in ['feature', 'model', 'accuracy', 'auc', 'performance']):
            response = {
                'bot_message': '📊 FraudGuard uses XGBoost & LightGBM models with 99.1% AUC. Real-time risk scoring combines ML predictions with rule-based fraud signatures.',
                'type': 'info'
            }
        
        # Help keywords
        elif any(word in message_lower for word in ['help', 'how', 'what', 'guide', 'support']):
            response = {
                'bot_message': '💡 Use FraudGuard to: (1) Predict fraud risk for transactions, (2) View transaction history, (3) Get real-time alerts, (4) Export reports. Visit /about for more info!',
                'type': 'info'
            }
        
        return jsonify(response)
    
    except Exception as e:
        logger.error(f"Chatbot error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/chatbot')
@login_required
def chatbot():
    """Chatbot page"""
    return render_template('chatbot.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

@app.route('/404')
@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return render_template('404.html'), 404

@app.route('/500')
@app.errorhandler(500)
def server_error(error):
    """500 error handler"""
    return render_template('500.html'), 500

# ==================== CLI COMMANDS ====================

@app.cli.command()
def init_db():
    """Initialize database"""
    with app.app_context():
        db.create_all()
        print("Database initialized!")

@app.cli.command()
def seed_demo():
    """Seed demo data"""
    with app.app_context():
        # Check if demo user exists
        demo_user = User.query.filter_by(email='demo@fraudguard.com').first()
        if not demo_user:
            user = User(
                name='Demo Bank',
                email='demo@fraudguard.com',
                bank_id='DEMO001'
            )
            user.set_password('demo123')
            db.session.add(user)
            db.session.commit()
            print(f"Demo user created: {user.email}")
        else:
            print("Demo user already exists!")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)