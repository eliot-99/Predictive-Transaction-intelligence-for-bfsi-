#!/usr/bin/env python
"""
FraudGuard BFSI - Setup Script
Initializes database and seeds demo data
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app import app, db, User

def setup_database():
    """Initialize database"""
    print("🔧 Initializing database...")
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database initialized")
        
        # Check if demo user exists
        demo_user = User.query.filter_by(email='demo@fraudguard.com').first()
        if not demo_user:
            print("🌱 Seeding demo user...")
            user = User(
                name='Demo Bank',
                email='demo@fraudguard.com',
                bank_id='DEMO001'
            )
            user.set_password('demo123')
            db.session.add(user)
            db.session.commit()
            print("✅ Demo user created")
            print("   Email: demo@fraudguard.com")
            print("   Password: demo123")
        else:
            print("ℹ️  Demo user already exists")

def main():
    """Main setup function"""
    print("\n" + "="*60)
    print("FraudGuard BFSI - Setup Script")
    print("="*60 + "\n")
    
    try:
        setup_database()
        
        print("\n" + "="*60)
        print("✅ Setup Complete!")
        print("="*60)
        print("\nNext steps:")
        print("1. Run: python app.py")
        print("2. Open: http://localhost:5000")
        print("3. Login with: demo@fraudguard.com / demo123")
        print("\n" + "="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()