from pydantic import BaseModel
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime
from enum import Enum

class ChangeType(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"

class ContentChange(BaseModel):
    change_type: ChangeType
    old_content: str
    new_content: str
    line_range_old: Tuple[int, int]
    line_range_new: Tuple[int, int]
    
    # ✅ NEW FIELDS FOR BETTER VISUALIZATION
    highlighted_old: Optional[str] = None  # HTML with highlighting for old content
    highlighted_new: Optional[str] = None  # HTML with highlighting for new content
    context_before: Optional[str] = None   # Context before the change
    context_after: Optional[str] = None    # Context after the change
    change_summary: Optional[str] = None   # Summary of what changed
    
    # Metadata
    word_count_old: Optional[int] = None
    word_count_new: Optional[int] = None
    char_count_old: Optional[int] = None
    char_count_new: Optional[int] = None

class DiffRequest(BaseModel):
    old_version_id: str
    new_version_id: str

class DiffResponse(BaseModel):
    page_id: str
    old_version_id: str
    new_version_id: str
    old_timestamp: datetime
    new_timestamp: datetime
    changes: List[ContentChange]
    total_changes: int
    
    # ✅ NEW FIELDS FOR BETTER UX
    change_metrics: Dict[str, Any] = {}    # Statistics about changes
    html_diff: Optional[str] = None        # Complete HTML diff
    side_by_side_diff: Optional[List[Dict[str, Any]]] = None  # Line-by-line comparison
    
    # Summary info
    has_changes: bool = True
    change_percentage: float = 0.0
    similarity_score: float = 0.0

class VersionComparison(BaseModel):
    """Model for comparing two versions"""
    version1_id: str
    version2_id: str
    version1_content: str
    version2_content: str
    version1_timestamp: datetime
    version2_timestamp: datetime
    
class SideBySideLine(BaseModel):
    """Single line in side-by-side comparison"""
    old_line: Optional[str] = None
    new_line: Optional[str] = None
    type: str  # "unchanged", "added", "removed", "modified"
    old_line_num: Optional[int] = None
    new_line_num: Optional[int] = None
    highlighted_old: Optional[str] = None
    highlighted_new: Optional[str] = None

# ✅ ADDED: Version information schema
class VersionInfo(BaseModel):
    """Schema for version information"""
    id: str
    page_id: str
    version_number: int
    captured_at: datetime
    content_preview: Optional[str] = None
    title: Optional[str] = None
    has_content: Optional[bool] = True
    
    # Legacy fields for compatibility
    version_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    word_count: Optional[int] = None
    content_length: Optional[int] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# ✅ ADDED: Page information schema
class PageInfo(BaseModel):
    """Schema for page information"""
    id: str
    url: str
    title: str
    last_checked: Optional[datetime] = None
    version_count: int
    is_active: bool = True
    
    # Additional fields
    display_name: Optional[str] = None
    check_interval_minutes: Optional[int] = None
    created_at: Optional[datetime] = None
    last_change_detected: Optional[datetime] = None
    current_version_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# ✅ ADDED: Response for /pages endpoint
class PageListResponse(BaseModel):
    """Response for getting list of pages"""
    pages: List[PageInfo]
    total: Optional[int] = None
    skip: Optional[int] = None
    limit: Optional[int] = None

# ✅ ADDED: Version detail response
class VersionDetailResponse(BaseModel):
    """Response for getting a specific version"""
    id: str
    page_id: str
    timestamp: datetime
    text_content: str
    html_content: Optional[str] = None
    page_title: str
    page_url: str
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

# ✅ ADDED: Change metrics schema
class ChangeMetrics(BaseModel):
    """Schema for change statistics"""
    words_added: int
    words_removed: int
    total_words_old: Optional[int] = None
    total_words_new: Optional[int] = None
    similarity_score: float
    change_percentage: Optional[float] = None
    lines_added: Optional[int] = None
    lines_removed: Optional[int] = None