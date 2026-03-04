# app/schemas.py
from pydantic import BaseModel, Field
from typing import Any, Dict, List, Optional, Literal

SchemaVersion = Literal["survey_v1"]
Stage = Literal["free", "paid"]

class Consent(BaseModel):
    privacy_consent: bool
    consent_at: Optional[str] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None

class Contact(BaseModel):
    phone: str
    email: Optional[str] = None

class SurveyIn(BaseModel):
    schema_version: SchemaVersion
    stage: Stage
    answers: Dict[str, Any]
    contact: Contact
    consent: Consent

class FreeOut(BaseModel):
    sid: str
    risk_level: str
    free_token: str
    report_url: str
    next: Literal["PAY", "HARD_BLOCK"]