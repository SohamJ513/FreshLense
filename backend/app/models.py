# backend/app/models.py
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Any, Annotated
from datetime import datetime
from bson import ObjectId
from enum import Enum
import re

# Simple ObjectId handling for Pydantic V2
def validate_object_id(v: Any) -> ObjectId:
    if isinstance(v, ObjectId):
        return v
    if isinstance(v, str) and ObjectId.is_valid(v):
        return ObjectId(v)
    raise ValueError("Invalid ObjectId")

# Type alias for ObjectId fields
PyObjectId = Annotated[ObjectId, Field(validate_default=True)]

# -------------------------------
# Enums
# -------------------------------
class ChangeType(str, Enum):
    STRUCTURAL = "structural"
    SEMANTIC = "semantic"
    NEW_PAGE = "new_page"

class NotificationFrequency(str, Enum):
    IMMEDIATELY = "immediately"
    DAILY_DIGEST = "daily_digest"

# -------------------------------
# MFA Models (NEW)
# -------------------------------
class MFASetupRequest(BaseModel):
    mfa_email: Optional[str] = None
    enable_mfa: bool = True
    
    @field_validator('mfa_email')
    @classmethod
    def validate_mfa_email(cls, v):
        if v is not None and not re.match(r'[^@]+@[^@]+\.[^@]+', v):
            raise ValueError('Invalid email format for MFA')
        return v

class MFAVerifyRequest(BaseModel):
    mfa_code: str = Field(min_length=6, max_length=6, pattern=r'^\d+$')
    
    @field_validator('mfa_code')
    @classmethod
    def validate_mfa_code(cls, v):
        if not v.isdigit():
            raise ValueError('MFA code must contain only digits')
        if len(v) != 6:
            raise ValueError('MFA code must be 6 digits')
        return v

class MFALoginResponse(BaseModel):
    requires_mfa: bool = Field(default=False)
    email: Optional[str] = None
    message: Optional[str] = None
    access_token: Optional[str] = None
    token_type: Optional[str] = None

# -------------------------------
# User Models
# -------------------------------
class UserBase(BaseModel):
    email: str

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if not re.match(r'[^@]+@[^@]+\.[^@]+', v):
            raise ValueError('Invalid email format')
        return v

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    hashed_password: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    notification_preferences: dict = Field(default={
        "email_alerts": True,
        "frequency": NotificationFrequency.IMMEDIATELY
    })
    
    # MFA Fields (NEW)
    mfa_enabled: bool = Field(default=False)
    mfa_email: Optional[str] = Field(default=None)  # Different email for MFA codes
    mfa_code: Optional[str] = Field(default=None)  # Temporary verification code
    mfa_code_expires: Optional[datetime] = Field(default=None)  # Code expiry time
    mfa_setup_completed: bool = Field(default=False)  # Track if user completed MFA setup

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        ser_json_by_alias=True,   # ✅ ensures "id" instead of "_id" in API response
    )

# -------------------------------
# Password Reset Models
# -------------------------------
class PasswordResetTokenBase(BaseModel):
    token: str
    user_id: str  # ✅ CHANGED: Use string instead of PyObjectId
    expires_at: datetime

class PasswordResetTokenCreate(PasswordResetTokenBase):
    pass

class PasswordResetToken(PasswordResetTokenBase):
    id: Optional[str] = Field(alias="_id", default=None)  # ✅ CHANGED: Use string instead of PyObjectId
    created_at: datetime = Field(default_factory=datetime.utcnow)
    used: bool = Field(default=False)
    used_at: Optional[datetime] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        ser_json_by_alias=True,
    )

# -------------------------------
# Tracked Page Models
# -------------------------------
class TrackedPageBase(BaseModel):
    url: str
    display_name: Optional[str] = None
    check_interval_minutes: int = Field(default=1440)  # Default to 24 hours

class TrackedPageCreate(TrackedPageBase):
    pass

class TrackedPage(TrackedPageBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    user_id: PyObjectId
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked: Optional[datetime] = None
    last_change_detected: Optional[datetime] = None
    current_version_id: Optional[PyObjectId] = None

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        ser_json_by_alias=True,   # ✅ Fix for frontend expecting "id"
    )

# -------------------------------
# Page Version Models
# -------------------------------
class PageVersionBase(BaseModel):
    html_content: Optional[str] = None
    text_content: str
    semantic_embedding: Optional[List[float]] = None

class PageVersion(PageVersionBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    page_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        ser_json_by_alias=True,
    )

# -------------------------------
# Change Log Models
# -------------------------------
class ChangeLogBase(BaseModel):
    type: ChangeType
    description: Optional[str] = None
    semantic_similarity_score: Optional[float] = None

class ChangeLog(ChangeLogBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    page_id: PyObjectId
    user_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    versions: dict = Field(default_factory=dict)
    diff: dict = Field(default_factory=dict)
    viewed_by_user: bool = Field(default=False)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        ser_json_by_alias=True,
    )