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

class PaidSurveySaveOut(BaseModel):
    ok: bool
    sid: str
    saved: bool
    next: Literal["GENERATE_REPORT"]

PremiumResolvedState = Literal[
    "INVALID_REPORT_TOKEN",
    "REPORT_ORDER_MISMATCH",
    "NOT_PAID",
    "NEED_SURVEY",
    "PROCESSING",
    "READY",
]

PremiumNextAction = Literal[
    "SHOW_ERROR",
    "GO_PAYMENT",
    "GO_SURVEY",
    "POLL_STATUS",
    "OPEN_REPORT",
]


class PremiumStateOut(BaseModel):
    state: PremiumResolvedState
    sid: Optional[str] = None
    order_id: Optional[str] = None
    report_token: str
    report_url: Optional[str] = None
    next_action: PremiumNextAction
    next_url: Optional[str] = None
    user_message: str
    has_paid_survey: bool = False
    has_report_html: bool = False
    has_report_markdown: bool = False


class PremiumEntryOut(BaseModel):
    ok: bool
    state: PremiumResolvedState
    sid: Optional[str] = None
    order_id: Optional[str] = None
    report_token: str
    next_action: PremiumNextAction
    next_url: Optional[str] = None
    user_message: str
    report_url: Optional[str] = None


class SurveySubmitOut(BaseModel):
    ok: bool
    sid: str
    saved: bool
    next: Literal["OPEN_REPORT", "POLL_STATUS"]
    order_id: str
    report_token: str
    state: PremiumResolvedState
    next_action: PremiumNextAction
    next_url: Optional[str] = None
    user_message: str
    report_url: Optional[str] = None

class PremiumReportGenerateIn(BaseModel):
    order_id: str
    report_token: str


class PremiumReportGenerateOut(BaseModel):
    ok: bool
    sid: str
    prompt: str
    interpretation_result: Dict[str, Any]
    metrics: Dict[str, Any]
    meta: Dict[str, Any]


class PremiumReportFinalizeIn(BaseModel):
    order_id: str
    report_token: str
    overwrite: bool = True


class PremiumReportFinalizeOut(BaseModel):
    ok: bool
    sid: str
    report_token: str
    saved: bool
    status: str
    prompt: str
    interpretation_result: Dict[str, Any]
    metrics: Dict[str, Any]
    markdown: str
    html: str
    meta: Dict[str, Any]

class PremiumReportStatusOut(BaseModel):
    ok: bool
    sid: str
    report_token: str
    status: str
    has_html: bool
    has_markdown: bool
    report_url: str
