from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class FreeSurveyIn(BaseModel):
    q1_score: int = Field(ge=1, le=5)
    q2_score: int = Field(ge=1, le=5)
    q3_score: int = Field(ge=1, le=5)
    fear_type: str  # abandonment/breakdown/legal/rejection
    red_flags: List[str]  # ["해당 없음"] or selections

    raw: Dict[str, Any] = {}  # 원문 보관(옵션)

class FreeSurveyOut(BaseModel):
    sid: str
    impulse_index: int
    risk_level: str

class ConsentIn(BaseModel):
    sid: str
    consent_collection_use: bool
    consent_cross_border: bool
    consent_version: str = "v1"
    phone: str
    email: Optional[str] = None

class PaidSurveyIn(BaseModel):
    sid: str
    order_id: str
    answers: Dict[str, Any]

class GenerateIn(BaseModel):
    sid: str

class GenerateOut(BaseModel):
    status: str
    report_url: Optional[str] = None