# backend/schemas/auth.py
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
import re

# Existing schemas (keep these)
class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password endpoint"""
    email: EmailStr

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """Additional email validation"""
        if not re.match(r'[^@]+@[^@]+\.[^@]+', v):
            raise ValueError('Invalid email format')
        return v.lower().strip()  # Normalize email

class ForgotPasswordResponse(BaseModel):
    """Response schema for forgot password endpoint"""
    message: str = Field(
        default="If the email exists, a reset link has been sent",
        description="Always returns success message for security"
    )

class ResetPasswordRequest(BaseModel):
    """Request schema for reset password endpoint"""
    token: str = Field(
        min_length=32,
        max_length=255,
        description="Password reset token from email link"
    )
    new_password: str = Field(
        min_length=6,
        max_length=128,
        description="New password (min 6 characters)"
    )

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v):
        """Basic password strength validation"""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class ResetPasswordResponse(BaseModel):
    """Response schema for reset password endpoint"""
    message: str = Field(
        default="Password reset successfully",
        description="Confirmation message"
    )

# Optional: Additional auth-related schemas you might need later
class ChangePasswordRequest(BaseModel):
    """Schema for changing password while logged in"""
    current_password: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 6:
            raise ValueError('New password must be at least 6 characters long')
        return v

class ChangePasswordResponse(BaseModel):
    """Response for password change"""
    message: str = "Password changed successfully"

# ✅ ADD THESE MFA SCHEMAS BELOW

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """Email validation"""
        if not re.match(r'[^@]+@[^@]+\.[^@]+', v):
            raise ValueError('Invalid email format')
        return v.lower().strip()

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    password: str = Field(..., min_length=6)
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """Email validation"""
        if not re.match(r'[^@]+@[^@]+\.[^@]+', v):
            raise ValueError('Invalid email format')
        return v.lower().strip()
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        """Password validation"""
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class User(BaseModel):
    """Schema for user response"""
    id: str
    email: EmailStr
    created_at: str  # Can be string or datetime
    mfa_enabled: bool = False
    mfa_email: Optional[str] = None
    mfa_setup_completed: bool = False

class MFASetupRequest(BaseModel):
    """Schema for enabling MFA"""
    email: EmailStr
    mfa_email: Optional[EmailStr] = None  # Optional different email for MFA codes
    
    @field_validator('email', 'mfa_email')
    @classmethod
    def validate_email_format(cls, v, info):
        """Email validation for MFA setup"""
        if v is None:  # mfa_email is optional, can be None
            return v
        if not re.match(r'[^@]+@[^@]+\.[^@]+', v):
            raise ValueError('Invalid email format')
        return v.lower().strip()

class MFAVerifyRequest(BaseModel):
    """Schema for verifying MFA code"""
    email: EmailStr
    mfa_code: str = Field(..., min_length=6, max_length=6, description="6-digit MFA code")
    
    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v):
        """Email validation"""
        if not re.match(r'[^@]+@[^@]+\.[^@]+', v):
            raise ValueError('Invalid email format')
        return v.lower().strip()
    
    @field_validator('mfa_code')
    @classmethod
    def validate_mfa_code(cls, v):
        """MFA code validation - must be 6 digits"""
        if not v.isdigit() or len(v) != 6:
            raise ValueError('MFA code must be 6 digits')
        return v

class MFALoginResponse(BaseModel):
    """Schema for login response with MFA support"""
    requires_mfa: bool
    email: str
    message: str
    access_token: Optional[str] = None
    token_type: Optional[str] = None