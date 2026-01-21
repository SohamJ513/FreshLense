# backend/routers/auth.py
from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from datetime import datetime, timedelta
import secrets
import os
import logging
from typing import Optional, Dict, Any

from ..database import (
    get_user_by_email, 
    create_user,
    create_password_reset_token,
    get_valid_password_reset_token,
    mark_password_reset_token_used,
    update_user_password,
    update_user_mfa_status,
    update_user_mfa_code,
    clear_user_mfa_code,
    get_user_mfa_status,
    get_db
)
from ..schemas.auth import (
    ForgotPasswordRequest, 
    ResetPasswordRequest, 
    ForgotPasswordResponse, 
    ResetPasswordResponse,
    MFASetupRequest,
    MFAVerifyRequest,
    MFALoginResponse,
    User,
    UserCreate,
    UserLogin
)
from ..services.mfa_service import mfa_service
from ..services.email_service import send_mfa_email, send_mfa_setup_email, send_reset_email

# Import your JWT utilities
from ..utils.security import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_token_expiry_info,
    is_token_valid,
    decode_access_token
)

router = APIRouter(prefix="/api/auth", tags=["authentication"])
logger = logging.getLogger(__name__)

# -------------------------------
# DEBUG ENDPOINT - ADD THIS FIRST
# -------------------------------
@router.post("/debug-token-test")
async def debug_token_test():
    """Debug endpoint to test token creation"""
    # Create a test token
    test_token = create_access_token(data={"sub": "debug@test.com"})
    
    # Get token info
    token_info = get_token_expiry_info(test_token)
    
    # Decode to see payload
    try:
        payload = decode_access_token(test_token)
    except:
        payload = {"error": "Cannot decode"}
    
    return {
        "token_created": True,
        "token_preview": test_token[:50] + "..." if len(test_token) > 50 else test_token,
        "token_info": token_info,
        "payload": payload,
        "server_time_utc": datetime.utcnow().isoformat(),
        "access_token_expire_minutes": 1440
    }

# -------------------------------
# TOKEN VALIDATION ENDPOINT
# -------------------------------
@router.post("/validate-token")
async def validate_token(token: Dict[str, str]):
    """
    Validate if a token is still valid.
    """
    token_str = token.get("token")
    if not token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token is required"
        )
    
    # Check if token is valid
    if is_token_valid(token_str):
        token_info = get_token_expiry_info(token_str)
        return {
            "valid": True,
            "message": "Token is valid",
            "expires_at": token_info.get("expires_at"),
            "time_remaining_seconds": token_info.get("time_remaining_seconds"),
            "subject": token_info.get("subject")
        }
    else:
        return {
            "valid": False,
            "message": "Token is invalid or expired",
            "expires_at": None,
            "time_remaining_seconds": 0
        }

# -------------------------------
# Registration Endpoint - UPDATED
# -------------------------------
@router.post("/register", response_model=MFALoginResponse)
async def register(user_data: UserCreate):
    """
    Register a new user with MFA enabled by default.
    """
    # Check if user already exists
    existing_user = get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # ✅ Create user WITH MFA ENABLED BY DEFAULT
    user = create_user({
        "email": user_data.email,
        "password": user_data.password,
        "mfa_enabled": True,           # ✅ Enable MFA by default
        "mfa_email": user_data.email,  # ✅ Use same email for MFA
        "mfa_setup_completed": True    # ✅ Mark as setup completed
    })
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )
    
    logger.info(f"New user registered with MFA enabled: {user['email']}")
    
    # Send MFA code for setup
    await send_mfa_code_to_user(user)
    
    return MFALoginResponse(
        requires_mfa=True,
        email=user["email"],
        message="Registration successful! MFA code sent to your email for account setup."
    )

# -------------------------------
# Login with MFA Support - UPDATED WITH CONSISTENT RESPONSE
# -------------------------------
@router.post("/login")
async def login(user_credentials: UserLogin):
    """
    User login with MFA support.
    Returns MFA requirement if enabled (default), or tokens if explicitly disabled.
    """
    # Get user from database
    user = get_user_by_email(user_credentials.email)
    
    if not user:
        # Return generic error for security
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # ✅ Check if MFA is enabled for this user (default is True)
    if user.get("mfa_enabled", True):  # Default to True if not set
        logger.info(f"MFA required for user: {user['email']}")
        
        # Send MFA code automatically
        await send_mfa_code_to_user(user)
        
        # ✅ RETURN CONSISTENT STRUCTURE
        return MFALoginResponse(
            requires_mfa=True,
            email=user["email"],
            message="MFA code sent to your email"
        )
    
    # If MFA is explicitly disabled, return tokens directly
    access_token = create_access_token(data={"sub": user["email"]})
    
    # ✅ DEBUG: Log token creation
    token_info = get_token_expiry_info(access_token)
    logger.info(f"Token created for {user['email']}: expires in {token_info.get('time_remaining_seconds', 0)/60:.1f} minutes")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user["email"],
        "message": "Login successful"
    }

# -------------------------------
# MFA Endpoints
# -------------------------------
@router.post("/send-mfa-code")
async def send_mfa_code(request: Dict[str, str]):
    """
    Send MFA code to user's email.
    Can be used for login or during MFA setup.
    """
    email = request.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    user = get_user_by_email(email)
    if not user:
        # Return success even if user doesn't exist for security
        return {"message": "If the email exists, a verification code has been sent"}
    
    # Check if MFA is enabled
    if not user.get("mfa_enabled", True):  # Default to True
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is not enabled for this account"
        )
    
    # Send MFA code
    await send_mfa_code_to_user(user)
    
    return {"message": "MFA code sent to your email"}

@router.post("/verify-mfa")
async def verify_mfa_code(request: MFAVerifyRequest):
    """
    Verify MFA code and return access token.
    """
    email = request.email
    mfa_code = request.mfa_code
    
    if not email or not mfa_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email and MFA code are required"
        )
    
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Get stored MFA code and expiry
    stored_code = user.get("mfa_code")
    expires_at = user.get("mfa_code_expires")
    
    # Convert string to datetime if needed
    if expires_at and isinstance(expires_at, str):
        try:
            expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
        except ValueError:
            expires_at = None
    
    # Validate code
    is_valid, error_message = mfa_service.is_code_valid(stored_code, mfa_code, expires_at)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )
    
    # Clear MFA code after successful verification
    clear_user_mfa_code(user["_id"])
    
    print(f"\n" + "="*60)
    print(f"✅ MFA Verification Successful for: {user['email']}")
    
    # Create access token
    access_token = create_access_token(data={"sub": user["email"]})
    
    # ✅ CRITICAL: Validate the token immediately after creation
    token_info = get_token_expiry_info(access_token)
    print(f"🔍 [AUTH] Token Validation Check:")
    print(f"   - Valid: {token_info['valid']}")
    print(f"   - Expires at: {token_info['expires_at']}")
    print(f"   - Time remaining: {token_info['time_remaining_seconds']:.0f} seconds")
    print(f"   - Subject: {token_info['subject']}")
    
    if not token_info['valid']:
        print(f"❌ [AUTH] CRITICAL: Token is INVALID immediately after creation!")
        print(f"   - This explains the session expiry issue")
    
    print("="*60 + "\n")
    
    # Log successful MFA verification
    logger.info(f"MFA verification successful for user: {user['email']}")
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "email": user["email"],
        "message": "Login successful"
    }

# -------------------------------
# Forgot Password Endpoint
# -------------------------------
@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(request: ForgotPasswordRequest):
    """
    Initiate password reset process.
    Always returns success to prevent email enumeration attacks.
    """
    logger.info(f"🔍 [DEBUG] Forgot password requested for: {request.email}")
    
    user = get_user_by_email(request.email)
    
    # Always return success to prevent email enumeration
    if not user:
        logger.info(f"[DEBUG] Password reset requested for non-existent email: {request.email}")
        return ForgotPasswordResponse(
            message="If the email exists, a reset link has been sent"
        )
    
    logger.info(f"✅ [DEBUG] User found: {user['email']}, ID: {user['_id']}")
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)  # Token valid for 1 hour
    
    logger.info(f"🔑 [DEBUG] Generated reset token: {reset_token[:10]}...")
    
    # Save token to database
    token_created = create_password_reset_token(
        token=reset_token,
        user_id=user["_id"],
        expires_at=expires_at
    )
    
    if not token_created:
        logger.error(f"❌ [DEBUG] Failed to create password reset token for user: {user['email']}")
        # Still return success for security
        return ForgotPasswordResponse(
            message="If the email exists, a reset link has been sent"
        )
    
    logger.info(f"💾 [DEBUG] Token saved to database successfully")
    
    # Send reset email
    try:
        logger.info(f"📤 [DEBUG] Attempting to send reset email to {user['email']}")
        result = await send_reset_email(user["email"], reset_token, user["email"])
        logger.info(f"📧 [DEBUG] Reset email send result: {result}")
        logger.info(f"✅ Password reset email sent to: {user['email']}")
    except Exception as e:
        logger.error(f"❌ [DEBUG] Failed to send reset email to {user['email']}: {str(e)}", exc_info=True)
        # Still return success for security
    
    return ForgotPasswordResponse(
        message="If the email exists, a reset link has been sent"
    )

# -------------------------------
# Reset Password Endpoint
# -------------------------------
@router.post("/reset-password", response_model=ResetPasswordResponse)
async def reset_password(request: ResetPasswordRequest):
    """
    Reset user password using a valid reset token.
    """
    # Find valid token
    token_record = get_valid_password_reset_token(request.token)
    
    if not token_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Update user password
    password_updated = update_user_password(
        user_id=token_record["user_id"],
        new_password=request.new_password
    )
    
    if not password_updated:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )
    
    # Mark token as used
    mark_password_reset_token_used(request.token)
    
    logger.info(f"Password reset successful for user ID: {token_record['user_id']}")
    
    return ResetPasswordResponse(
        message="Password reset successfully"
    )

# -------------------------------
# Other MFA endpoints (setup, disable, status)
# -------------------------------
@router.post("/setup-mfa")
async def setup_mfa(request: MFASetupRequest, background_tasks: BackgroundTasks):
    """
    Enable MFA for user account (if not already enabled by default).
    """
    email = request.email
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if MFA is already enabled
    if user.get("mfa_enabled", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already enabled for this account"
        )
    
    # Update MFA settings
    mfa_email = request.mfa_email or user["email"]
    update_data = {
        "mfa_enabled": True,
        "mfa_email": mfa_email,
        "mfa_setup_completed": True,
        "updated_at": datetime.utcnow()
    }
    
    success = update_user_mfa_status(user["_id"], update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to enable MFA"
        )
    
    # Send setup confirmation email
    background_tasks.add_task(
        send_mfa_setup_email,
        user_email=user["email"]
    )
    
    logger.info(f"MFA enabled for user: {user['email']}")
    
    return {
        "message": "MFA enabled successfully",
        "mfa_email": mfa_email,
        "setup_completed": True
    }

@router.post("/disable-mfa")
async def disable_mfa(request: Dict[str, str]):
    """
    Disable MFA for user account (admin only).
    """
    email = request.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if MFA is already disabled
    if not user.get("mfa_enabled", True):  # Default to True
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="MFA is already disabled for this account"
        )
    
    # Disable MFA
    update_data = {
        "mfa_enabled": False,
        "mfa_code": None,
        "mfa_code_expires": None,
        "updated_at": datetime.utcnow()
    }
    
    success = update_user_mfa_status(user["_id"], update_data)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to disable MFA"
        )
    
    logger.info(f"MFA disabled for user: {user['email']}")
    
    return {"message": "MFA disabled successfully"}

@router.get("/mfa-status")
async def get_mfa_status(email: str):
    """
    Get MFA status for a user.
    """
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "mfa_enabled": user.get("mfa_enabled", True),  # Default to True
        "mfa_email": user.get("mfa_email"),
        "mfa_setup_completed": user.get("mfa_setup_completed", False)
    }

# -------------------------------
# Helper Functions
# -------------------------------
async def send_mfa_code_to_user(user: Dict[str, Any]):
    """
    Generate and send MFA code to user.
    """
    # Generate new MFA code
    mfa_code = mfa_service.generate_mfa_code()
    expires_at = mfa_service.get_code_expiry()
    
    # Update user with new code
    update_user_mfa_code(
        user_id=user["_id"],
        mfa_code=mfa_code,
        expires_at=expires_at
    )
    
    # Determine which email to use
    mfa_email = user.get("mfa_email") or user["email"]
    
    try:
        # Send MFA email
        await send_mfa_email(
            to_email=mfa_email,
            mfa_code=mfa_code,
            user_email=user["email"]
        )
        logger.info(f"MFA code sent to {mfa_email} for user {user['email']}")
    except Exception as e:
        logger.error(f"Failed to send MFA email to {mfa_email}: {e}")
        # Don't raise error to prevent email enumeration
        # The code is still saved, user can request resend