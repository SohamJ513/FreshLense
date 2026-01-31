# backend/app/models.py
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Any, Annotated, Dict
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

class PruneStrategy(str, Enum):
    SIGNIFICANT_ONLY = "significant_only"
    ALL = "all"
    TIME_BASED = "time_based"

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
    
    # ✅ ADDED: Soft delete protection fields
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = Field(default=None)
    deleted_by: Optional[str] = Field(default=None)
    
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
        ser_json_by_alias=True,
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
    
    # ✅ ADDED: SMART VERSIONING CONFIGURATION
    versioning_config: Dict[str, Any] = Field(default_factory=lambda: {
        "min_change_threshold": 0.05,  # 5% change required to save version
        "require_significant_keywords": True,
        "max_versions_kept": 50,
        "check_structural_changes": True,
        "prune_strategy": PruneStrategy.SIGNIFICANT_ONLY,
        "notification_threshold": 0.3  # Only notify for changes with score >= 0.3
    })

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        ser_json_by_alias=True,
    )

# -------------------------------
# Page Version Models - UPDATED WITH SMART VERSIONING
# -------------------------------
class PageVersionBase(BaseModel):
    html_content: Optional[str] = None
    text_content: str
    semantic_embedding: Optional[List[float]] = None

class PageVersionCreate(PageVersionBase):
    """Schema for creating new versions"""
    pass

class PageVersion(PageVersionBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    page_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # ✅ ADDED: SMART VERSIONING FIELDS
    content_hash: str = Field(...)  # SHA256 hash of content for quick comparison
    checksum: str = Field(...)  # MD5 checksum for very fast comparison
    change_significance_score: float = Field(default=0.0)  # 0-1 score of change significance
    change_metrics: Dict[str, Any] = Field(default_factory=lambda: {
        "character_change_percentage": 0.0,
        "word_change_percentage": 0.0,
        "structural_changes": 0.0,
        "similarity_score": 1.0,
        "words_added": 0,
        "words_removed": 0,
        "total_words_old": 0,
        "total_words_new": 0
    })
    
    metadata: Dict[str, Any] = Field(default_factory=lambda: {
        "store_reason": "first_version",
        "analysis": {},
        "config_used": {}
    })

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        ser_json_by_alias=True,
    )

# -------------------------------
# Change Log Models - UPDATED
# -------------------------------
class ChangeLogBase(BaseModel):
    type: ChangeType
    description: Optional[str] = None
    semantic_similarity_score: Optional[float] = None

class ChangeLogCreate(ChangeLogBase):
    """Schema for creating change logs"""
    page_id: str
    user_id: str
    change_significance_score: Optional[float] = None
    details: Optional[Dict[str, Any]] = None

class ChangeLog(ChangeLogBase):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    page_id: PyObjectId
    user_id: PyObjectId
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # ✅ UPDATED: Enhanced change tracking
    change_significance_score: Optional[float] = Field(default=None)
    versions: Dict[str, Any] = Field(default_factory=lambda: {
        "old_version_id": None,
        "new_version_id": None,
        "old_content_length": 0,
        "new_content_length": 0
    })
    
    diff: Dict[str, Any] = Field(default_factory=lambda: {
        "change_percentage": 0.0,
        "significant_changes": [],
        "keyword_changes": []
    })
    
    details: Dict[str, Any] = Field(default_factory=lambda: {
        "url": "",
        "notification_sent": False,
        "email_sent_to": None,
        "viewed_by_user": False,
        "auto_generated": True
    })
    
    # Renamed for clarity
    user_viewed: bool = Field(default=False, alias="viewed_by_user")

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str},
        ser_json_by_alias=True,
    )

# -------------------------------
# Versioning Analysis Models
# -------------------------------
class VersioningAnalysis(BaseModel):
    """Model for versioning analysis results"""
    store: bool = Field(...)
    reason: str = Field(...)
    score: float = Field(ge=0.0, le=1.0)  # 0-1 score
    hash: str = Field(...)
    checksum: str = Field(...)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    analysis: Dict[str, Any] = Field(default_factory=dict)

class VersioningConfig(BaseModel):
    """Model for versioning configuration"""
    min_change_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    require_significant_keywords: bool = Field(default=True)
    max_versions_kept: int = Field(default=50, ge=1, le=1000)
    check_structural_changes: bool = Field(default=True)
    prune_strategy: PruneStrategy = Field(default=PruneStrategy.SIGNIFICANT_ONLY)
    notification_threshold: float = Field(default=0.3, ge=0.0, le=1.0)

class ChangeMetrics(BaseModel):
    """Model for change metrics"""
    character_change_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    word_change_percentage: float = Field(default=0.0, ge=0.0, le=100.0)
    structural_changes: float = Field(default=0.0, ge=0.0, le=100.0)
    similarity_score: float = Field(default=1.0, ge=0.0, le=1.0)
    words_added: int = Field(default=0, ge=0)
    words_removed: int = Field(default=0, ge=0)
    total_words_old: int = Field(default=0, ge=0)
    total_words_new: int = Field(default=0, ge=0)
    lines_added: int = Field(default=0, ge=0)
    lines_removed: int = Field(default=0, ge=0)

# -------------------------------
# API Response Models
# -------------------------------
class VersioningStatus(BaseModel):
    """Response model for versioning status"""
    page_id: str
    total_versions: int
    significant_versions: int
    last_version_score: Optional[float] = None
    config: VersioningConfig
    storage_efficiency: float = Field(ge=0.0, le=100.0)  # % of versions actually needed

class SmartVersioningResponse(BaseModel):
    """Response for smart versioning operations"""
    saved: bool
    version_id: Optional[str] = None
    reason: str
    score: float
    analysis: VersioningAnalysis
    pruned_count: int = Field(default=0)

# -------------------------------
# Utility Models
# -------------------------------
class ContentComparison(BaseModel):
    """Model for comparing two versions"""
    old_version_id: str
    new_version_id: str
    old_content: Optional[str] = None
    new_content: Optional[str] = None
    analysis: Optional[VersioningAnalysis] = None

class PruneResult(BaseModel):
    """Result of version pruning"""
    page_id: str
    versions_kept: int
    versions_pruned: int
    kept_versions: List[str] = Field(default_factory=list)
    pruned_versions: List[str] = Field(default_factory=list)

# -------------------------------
# Update Models for Backward Compatibility
# -------------------------------
class LegacyPageVersion(PageVersion):
    """Legacy model for backward compatibility"""
    class Config:
        extra = "ignore"  # Ignore extra fields from old versions

class LegacyTrackedPage(TrackedPage):
    """Legacy model for backward compatibility"""
    class Config:
        extra = "ignore"  # Ignore missing versioning_config in old pages