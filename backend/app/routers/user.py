# backend/app/routers/user.py
from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
from typing import Optional
import logging

from ..database import (
    get_user_by_email,
    update_user_profile,
    update_user_password,
    update_notification_settings,
    delete_user_account,
    get_db
)
from ..schemas.user import (
    UserProfileResponse,
    UpdateProfileRequest,
    ChangePasswordRequest,
    NotificationSettingsRequest,
    NotificationSettingsResponse,
    DeleteAccountRequest
)
from ..utils.security import get_current_user, verify_password, get_password_hash
from ..services.email_service import send_account_deletion_email

router = APIRouter(prefix="/api/user", tags=["user"])
logger = logging.getLogger(__name__)


@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user = Depends(get_current_user)):
    """
    Get current user's profile information
    """
    try:
        # current_user is already a dict from get_current_user
        user_id = current_user.get("_id") if isinstance(current_user, dict) else getattr(current_user, "_id", None)
        
        return {
            "id": str(user_id),
            "email": current_user.get("email") if isinstance(current_user, dict) else current_user.email,
            "display_name": current_user.get("display_name") if isinstance(current_user, dict) else getattr(current_user, "display_name", None),
            "created_at": current_user.get("created_at") if isinstance(current_user, dict) else current_user.created_at,
            "mfa_enabled": current_user.get("mfa_enabled", False) if isinstance(current_user, dict) else current_user.mfa_enabled,
        }
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user profile"
        )


@router.put("/profile")
async def update_user_profile(
    request: UpdateProfileRequest,
    current_user = Depends(get_current_user)
):
    """
    Update user's profile information (display name)
    """
    try:
        user_id = current_user.get("_id") if isinstance(current_user, dict) else getattr(current_user, "_id", None)
        
        success = update_user_profile(user_id, request.display_name)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update profile"
            )
        
        return {"message": "Profile updated successfully", "display_name": request.display_name}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )


@router.put("/password")
async def change_user_password(
    request: ChangePasswordRequest,
    current_user = Depends(get_current_user)
):
    """
    Change user's password
    """
    try:
        # Get current password from request
        current_password = request.current_password
        new_password = request.new_password
        
        # Get stored hashed password
        stored_password = current_user.get("hashed_password") if isinstance(current_user, dict) else current_user.hashed_password
        
        # Verify current password
        if not verify_password(current_password, stored_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Hash new password
        hashed_new_password = get_password_hash(new_password)
        
        # Update password in database
        user_id = current_user.get("_id") if isinstance(current_user, dict) else getattr(current_user, "_id", None)
        success = update_user_password(user_id, hashed_new_password)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to change password"
            )
        
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.get("/settings")
async def get_user_settings(current_user = Depends(get_current_user)):
    """
    Get user's notification settings and MFA status
    """
    try:
        notification_prefs = current_user.get("notification_preferences", {}) if isinstance(current_user, dict) else current_user.notification_preferences
        mfa_enabled = current_user.get("mfa_enabled", False) if isinstance(current_user, dict) else current_user.mfa_enabled
        
        return {
            "email_alerts": notification_prefs.get("email_alerts", True),
            "alert_frequency": notification_prefs.get("frequency", "immediately"),
            "default_check_interval": notification_prefs.get("default_check_interval", 1440),
            "mfa_enabled": mfa_enabled
        }
    except Exception as e:
        logger.error(f"Error getting user settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user settings"
        )


@router.put("/settings/notifications")
async def update_notification_settings(
    request: NotificationSettingsRequest,
    current_user = Depends(get_current_user)
):
    """
    Update user's notification preferences
    """
    try:
        user_id = current_user.get("_id") if isinstance(current_user, dict) else getattr(current_user, "_id", None)
        
        notification_prefs = {
            "email_alerts": request.email_alerts,
            "frequency": request.alert_frequency,
            "default_check_interval": request.default_check_interval
        }
        
        success = update_notification_settings(user_id, notification_prefs)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update notification settings"
            )
        
        return {"message": "Notification settings updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating notification settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update notification settings"
        )


@router.delete("/account")
async def delete_user_account(
    current_user = Depends(get_current_user)
):
    """
    Permanently delete user account and all associated data
    """
    try:
        user_id = current_user.get("_id") if isinstance(current_user, dict) else getattr(current_user, "_id", None)
        user_email = current_user.get("email") if isinstance(current_user, dict) else current_user.email
        
        # Delete all user data
        success = delete_user_account(user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete account"
            )
        
        # Send deletion confirmation email
        try:
            await send_account_deletion_email(user_email)
        except Exception as e:
            logger.error(f"Failed to send account deletion email: {e}")
        
        return {"message": "Account deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting user account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )