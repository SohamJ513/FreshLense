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
import bcrypt

load_dotenv()

# Create logger for this module
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
# ✅ INCREASED TOKEN EXPIRY TO 24 HOURS FOR TESTING
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))  # 24 hours default

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

# ================================================
# ✅ BCRYPT INITIALIZATION WITH ERROR HANDLING
# ================================================

# Test bcrypt backend on startup
try:
    # Force bcrypt backend to load by doing a test hash
    test_hash = bcrypt.hashpw(b"test_password", bcrypt.gensalt())
    logger.info("✅ bcrypt backend loaded successfully")
except Exception as e:
    logger.error(f"❌ bcrypt backend failed to load: {e}")
    logger.error("Password hashing will not work correctly!")

# Password hashing with explicit configuration
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12,  # Explicitly set rounds
    bcrypt__ident="2b"  # Use bcrypt version 2b
)

def validate_password_length(password: str) -> str:
    """
    Validate and truncate password if longer than 72 bytes (bcrypt limitation)
    Returns the (possibly truncated) password.
    """
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        logger.warning(f"Password longer than 72 bytes ({len(password_bytes)} bytes), truncating to 72 bytes")
        # Truncate to 72 bytes, decoding back to string
        return password_bytes[:72].decode('utf-8', errors='ignore')
    return password

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password with proper error handling.
    """
    if not plain_password or not hashed_password:
        logger.error("Password verification failed: missing password or hash")
        return False
    
    try:
        # Validate password length for bcrypt
        validated_password = validate_password_length(plain_password)
        
        logger.debug(f"Verifying password (length: {len(validated_password)} chars)")
        result = pwd_context.verify(validated_password, hashed_password)
        logger.debug(f"Password verification result: {result}")
        return result
        
    except ValueError as ve:
        # Specific handling for bcrypt value errors
        if "invalid salt" in str(ve):
            logger.error(f"Invalid salt in hash - hash may be corrupted: {ve}")
        elif "invalid bcrypt hash" in str(ve):
            logger.error(f"Invalid bcrypt hash format - hash may be corrupted: {ve}")
        else:
            logger.error(f"Password verification value error: {ve}")
        return False
        
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        # Log more details for debugging
        logger.debug(f"Password type: {type(plain_password)}")
        logger.debug(f"Hash type: {type(hashed_password)}")
        logger.debug(f"Hash preview: {hashed_password[:30] if hashed_password else 'None'}...")
        return False

def get_password_hash(password: str) -> str:
    """
    Hash a password with proper error handling.
    """
    if not password:
        logger.error("Password hashing failed: empty password")
        raise ValueError("Password cannot be empty")
    
    try:
        # Validate password length for bcrypt
        validated_password = validate_password_length(password)
        
        logger.debug(f"Hashing password (length: {len(validated_password)} chars)")
        hashed = pwd_context.hash(validated_password)
        logger.debug(f"Password hashed successfully, result length: {len(hashed)}")
        return hashed
        
    except Exception as e:
        logger.error(f"Password hashing error: {e}")
        # Re-raise as ValueError with more context
        raise ValueError(f"Failed to hash password: {str(e)}")

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
        logger.warning(f"Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
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
        logger.debug(f"Token expired")
        return False
    except jwt.InvalidTokenError:
        logger.debug(f"Invalid token")
        return False

# ✅ ADDED: Function to get token expiry info - FIXED with UTC timezone
def get_token_expiry_info(token: str) -> Dict[str, Any]:
    """Get token expiry information"""
    try:
        # Decode without verifying expiry to get the payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_exp": False})
        
        if 'exp' in payload:
            # ✅ FIXED: Use utcfromtimestamp instead of fromtimestamp for UTC consistency
            expiry_time = datetime.utcfromtimestamp(payload['exp'])
            current_time = datetime.utcnow()
            time_remaining = expiry_time - current_time
            
            return {
                "valid": expiry_time > current_time,
                "expires_at": expiry_time,
                "issued_at": datetime.utcfromtimestamp(payload.get('iat', 0)) if payload.get('iat') else None,
                "time_remaining_seconds": max(0, time_remaining.total_seconds()),
                "subject": payload.get('sub')
            }
    except Exception as e:
        logger.error(f"Error getting token info: {e}")
    
    return {"valid": False, "expires_at": None, "time_remaining_seconds": 0}

# ✅ ADDED: get_current_user dependency function - UPDATED
async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get current user from JWT token - Returns User model object"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # If no token provided, raise exception
    if not token:
        logger.warning("No token provided")
        raise credentials_exception
    
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