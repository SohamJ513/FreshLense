# backend/app/utils/security.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv

load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
# ✅ INCREASED TOKEN EXPIRY TO 24 HOURS FOR TESTING
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))  # 24 hours default

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    now = datetime.utcnow()
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # ✅ ADDED iat (issued at) CLAIM - CRITICAL FIX
    to_encode.update({
        "exp": expire,  # Expiration time
        "iat": now,     # Issued at time - REQUIRED for proper validation
        "type": "access"  # Token type for clarity
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    # ✅ DEBUG LOGGING
    print(f"🔐 [JWT] Token created:")
    print(f"   - Subject: {data.get('sub', 'N/A')}")
    print(f"   - Issued at (UTC): {now}")
    print(f"   - Expires at (UTC): {expire}")
    print(f"   - Duration: {ACCESS_TOKEN_EXPIRE_MINUTES} minutes ({ACCESS_TOKEN_EXPIRE_MINUTES/60:.1f} hours)")
    print(f"   - Token preview: {encoded_jwt[:50]}...")
    
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # ✅ DEBUG LOGGING
        print(f"🔐 [JWT] Token decoded:")
        print(f"   - Subject: {payload.get('sub', 'N/A')}")
        print(f"   - Issued at: {datetime.fromtimestamp(payload.get('iat', 0)) if payload.get('iat') else 'N/A'}")
        print(f"   - Expires at: {datetime.fromtimestamp(payload.get('exp', 0)) if payload.get('exp') else 'N/A'}")
        print(f"   - Current time (UTC): {datetime.utcnow()}")
        
        # Check if token is expired
        if 'exp' in payload:
            expiry_time = datetime.fromtimestamp(payload['exp'])
            current_time = datetime.utcnow()
            time_remaining = expiry_time - current_time
            print(f"   - Time remaining: {time_remaining}")
        
        return payload
    except jwt.ExpiredSignatureError:
        print(f"❌ [JWT] Token expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"❌ [JWT] Invalid token: {e}")
        return None

def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from JWT token"""
    payload = decode_access_token(token)
    if payload:
        return payload.get("sub")  # Assuming "sub" contains user email/ID
    return None

# ✅ ADDED: Function to check token expiry without decoding
def is_token_valid(token: str) -> bool:
    """Check if token is valid and not expired"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": True})
        return True
    except jwt.ExpiredSignatureError:
        print(f"⚠️ [JWT] Token expired")
        return False
    except jwt.InvalidTokenError:
        print(f"⚠️ [JWT] Invalid token")
        return False

# ✅ ADDED: Function to get token expiry info
def get_token_expiry_info(token: str) -> Dict[str, Any]:
    """Get token expiry information"""
    try:
        # Decode without verifying expiry to get the payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        
        if 'exp' in payload:
            expiry_time = datetime.fromtimestamp(payload['exp'])
            current_time = datetime.utcnow()
            time_remaining = expiry_time - current_time
            
            return {
                "valid": expiry_time > current_time,
                "expires_at": expiry_time,
                "issued_at": datetime.fromtimestamp(payload.get('iat', 0)) if payload.get('iat') else None,
                "time_remaining_seconds": max(0, time_remaining.total_seconds()),
                "subject": payload.get('sub')
            }
    except Exception as e:
        print(f"❌ [JWT] Error getting token info: {e}")
    
    return {"valid": False, "expires_at": None, "time_remaining_seconds": 0}

# Optional: Token blacklist for logout functionality (if needed)
token_blacklist = set()

def blacklist_token(token: str) -> None:
    """Add token to blacklist (for logout)"""
    token_blacklist.add(token)

def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted"""
    return token in token_blacklist