# backend/app/schemas/user.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import re


class UserProfileResponse(BaseModel):
    """Response schema for user profile"""
    id: str
    email: str
    display_name: Optional[str] = None
    created_at: datetime
    mfa_enabled: bool = False


class UpdateProfileRequest(BaseModel):
    """Request schema for updating user profile"""
    display_name: Optional[str] = Field(None, max_length=100, description="Display name for the user")
    
    @field_validator('display_name')
    @classmethod
    def validate_display_name(cls, v):
        if v is not None:
            # Remove extra spaces
            v = ' '.join(v.split())
            if len(v) < 1:
                raise ValueError('Display name must be at least 1 character')
            if len(v) > 100:
                raise ValueError('Display name must be less than 100 characters')
        return v


class ChangePasswordRequest(BaseModel):
    """Request schema for changing password"""
    current_password: str = Field(..., min_length=1, description="Current password")
    new_password: str = Field(..., min_length=6, max_length=128, description="New password")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('New password must be at least 6 characters long')
        return v


class NotificationSettingsRequest(BaseModel):
    """Request schema for updating notification settings"""
    email_alerts: bool = Field(default=True, description="Enable email alerts")
    alert_frequency: str = Field(default="immediately", description="Alert frequency: immediately, daily, weekly")
    default_check_interval: int = Field(default=1440, ge=60, le=10080, description="Default check interval in minutes")
    
    @field_validator('alert_frequency')
    @classmethod
    def validate_alert_frequency(cls, v):
        allowed = ["immediately", "daily", "weekly"]
        if v not in allowed:
            raise ValueError(f'Alert frequency must be one of: {", ".join(allowed)}')
        return v
    
    @field_validator('default_check_interval')
    @classmethod
    def validate_check_interval(cls, v):
        if v < 60:
            raise ValueError('Check interval must be at least 60 minutes (1 hour)')
        if v > 10080:
            raise ValueError('Check interval cannot exceed 10080 minutes (1 week)')
        return v


class NotificationSettingsResponse(BaseModel):
    """Response schema for notification settings"""
    email_alerts: bool
    alert_frequency: str
    default_check_interval: int
    mfa_enabled: bool


class DeleteAccountRequest(BaseModel):
    """Request schema for account deletion"""
    confirm_email: str = Field(..., description="Email confirmation for deletion")
    
    @field_validator('confirm_email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'[^@]+@[^@]+\.[^@]+', v):
            raise ValueError('Invalid email format')
        return v.lower().strip()