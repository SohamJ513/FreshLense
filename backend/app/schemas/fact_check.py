from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

class ClaimType(str, Enum):
    VERSION_INFO = "version_info"
    PERFORMANCE = "performance"
    SECURITY = "security"
    COMPATIBILITY = "compatibility"
    API_REFERENCE = "api_reference"
    CODE_EXAMPLE = "code_example"
    OTHER = "other"

class Verdict(str, Enum):
    TRUE = "true"
    FALSE = "false"
    UNVERIFIED = "unverified"
    INCONCLUSIVE = "inconclusive"

class FactCheckItem(BaseModel):
    claim: str
    claim_type: ClaimType
    context: Optional[str] = ""
    verdict: Verdict
    confidence: float
    sources: List[str]
    explanation: str

class FactCheckRequest(BaseModel):
    version_id: str

class FactCheckResponse(BaseModel):
    page_id: str
    version_id: str
    page_url: str
    page_title: str
    checked_at: datetime
    results: List[FactCheckItem]
    total_claims: int
    verified_claims: int
    unverified_claims: int
    inconclusive_claims: int