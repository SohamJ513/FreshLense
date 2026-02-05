from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
import logging
from bson import ObjectId

load_dotenv()

# Create logger for this module
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
# ✅ INCREASED TOKEN EXPIRY TO 24 HOURS FOR TESTING
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))  # 24 hours default

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

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
    
    # ✅ DEBUG LOGGING - Changed to debug level
    logger.debug(f"Token created for subject: {data.get('sub', 'N/A')}")
    
    return encoded_jwt

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # ✅ DEBUG LOGGING - Changed to debug level
        logger.debug(f"Token decoded for subject: {payload.get('sub', 'N/A')}")
        
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning(f"Token expired")  # Changed to warning
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")  # Changed to warning
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
        logger.debug(f"Token expired")  # Changed to debug
        return False
    except jwt.InvalidTokenError:
        logger.debug(f"Invalid token")  # Changed to debug
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
        logger.error(f"Error getting token info: {e}")  # Keep error for actual errors
    
    return {"valid": False, "expires_at": None, "time_remaining_seconds": 0}

# ✅ ADDED: get_current_user dependency function - UPDATED
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token - Returns User model object"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Import here to avoid circular imports
    from ..database import get_user_by_email
    from ..models import User as UserModel  # Import the User model
    
    try:
        payload = decode_access_token(token)
        if not payload:
            raise credentials_exception
            
        email: str = payload.get("sub")
        if not email:
            logger.warning(f"Token missing 'sub' claim")
            raise credentials_exception
        
        logger.debug(f"Token validated for user: {email}")
        
    except jwt.ExpiredSignatureError:
        logger.warning(f"Token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected token error: {e}")
        raise credentials_exception

    # Get user as dictionary from database
    user_dict = get_user_by_email(email)
    if not user_dict:
        logger.warning(f"User not found for email: {email}")
        raise credentials_exception
    
    # ✅ CRITICAL FIX: Convert MongoDB document to User model
    # Ensure all required fields are present and properly formatted
    
    # Handle _id field - convert ObjectId to string for id field
    if "_id" in user_dict:
        user_dict["id"] = user_dict["_id"]  # Keep as ObjectId for model compatibility
        # Don't delete _id as the model expects it via alias
    
    # Ensure all required User model fields are present
    required_fields = ["email", "hashed_password"]
    for field in required_fields:
        if field not in user_dict:
            logger.error(f"User missing required field: {field}")
            raise credentials_exception
    
    # Set default values for optional fields if missing
    if "created_at" not in user_dict:
        user_dict["created_at"] = datetime.utcnow()
    
    if "notification_preferences" not in user_dict:
        user_dict["notification_preferences"] = {
            "email_alerts": True,
            "frequency": "immediately"
        }
    
    # MFA fields defaults
    mfa_fields = ["mfa_enabled", "mfa_setup_completed"]
    for field in mfa_fields:
        if field not in user_dict:
            user_dict[field] = False
    
    # Soft delete protection fields
    delete_fields = ["is_deleted", "deleted_at", "deleted_by"]
    for field in delete_fields:
        if field not in user_dict:
            if field == "is_deleted":
                user_dict[field] = False
            else:
                user_dict[field] = None
    
    try:
        # Create User model object
        user = UserModel(**user_dict)
        logger.debug(f"User model created successfully for: {email}")
        return user
    except Exception as e:
        logger.error(f"Failed to create User model for {email}: {e}")
        logger.error(f"User dict keys: {list(user_dict.keys())}")
        # Fallback: return the dictionary if model creation fails
        logger.warning(f"Falling back to dictionary for user: {email}")
        return user_dict

# Optional: Token blacklist for logout functionality (if needed)
token_blacklist = set()

def blacklist_token(token: str) -> None:
    """Add token to blacklist (for logout)"""
    token_blacklist.add(token)

def is_token_blacklisted(token: str) -> bool:
    """Check if token is blacklisted"""
    return token in token_blacklist