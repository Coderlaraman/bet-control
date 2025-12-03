import sys
import os
import asyncio
import traceback
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal, init_db
# Import all models to ensure they are registered with Base
from app.models.user import User
from app.models.bankroll import BankrollConfig
from app.models.bet import Bet
from app.models.sport import Sport
from app.api.v1.endpoints.auth import register
from app.schemas.user import UserCreate

async def verify_registration():
    print("🚀 Starting Registration Verification...")
    
    try:
        # Initialize DB
        print("Initializing database...")
        init_db()
        print("Database initialized.")
        
        db = SessionLocal()
        
        # 1. Test Successful Registration
        username = "verify_user_1"
        email = "verify@example.com"
        
        print(f"Cleaning up existing user: {username} / {email}")
        # Clean up if exists (by username OR email)
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing:
            # Also delete bankroll config if exists
            config = db.query(BankrollConfig).filter(BankrollConfig.user_id == existing.id).first()
            if config:
                db.delete(config)
            db.delete(existing)
            db.commit()
            print("Cleanup complete.")
            
        print(f"👤 Attempting to register new user: {username}")
        
        user_data = UserCreate(
            username=username,
            email=email,
            password="password123",
            full_name="Verify User"
        )
        
        new_user = await register(user_data, db)
        print(f"✅ Registration successful! User ID: {new_user.id}")
        
        # 2. Test Duplicate Registration
        print("👤 Attempting to register SAME user again (should fail)...")
        
        try:
            await register(user_data, db)
            print("❌ Error: Duplicate registration should have failed but succeeded.")
        except Exception as e:
            # Check for the specific HTTP exception detail we throw
            if "Username or email already registered" in str(e) or "400" in str(e):
                print(f"✅ Duplicate registration failed as expected: {e}")
            else:
                print(f"❌ Unexpected error during duplicate check: {e}")
                traceback.print_exc()

    except Exception as e:
        print(f"❌ Verification failed: {e}")
        traceback.print_exc()
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    asyncio.run(verify_registration())
