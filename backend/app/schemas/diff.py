from pydantic import BaseModel
from typing import List, Optional, Tuple
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