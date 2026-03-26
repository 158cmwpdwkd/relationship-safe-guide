from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel

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


PremiumResolvedState = Literal[
    "ORDER_NOT_FOUND",
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
    order_id: str
    free_report_token: Optional[str] = None
    premium_report_token: Optional[str] = None
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
    order_id: str
    free_report_token: Optional[str] = None
    premium_report_token: Optional[str] = None
    next_action: PremiumNextAction
    next_url: Optional[str] = None
    user_message: str
    report_url: Optional[str] = None


class SurveySubmitOut(BaseModel):
    ok: bool
    sid: str
    saved: bool
    next: Literal["GENERATE_REPORT", "OPEN_REPORT"]
    order_id: str
    free_report_token: Optional[str] = None
    premium_report_token: Optional[str] = None
    state: PremiumResolvedState
    next_action: PremiumNextAction
    next_url: Optional[str] = None
    user_message: str
    report_url: Optional[str] = None


class PremiumReportGenerateIn(BaseModel):
    order_id: str
    overwrite: bool = False


class PremiumReportGenerateOut(BaseModel):
    ok: bool
    sid: str
    order_id: str
    premium_report_token: str
    report_url: str
    status: str
    reused_existing: bool
    prompt: str
    interpretation_result: Dict[str, Any]
    metrics: Dict[str, Any]
    meta: Dict[str, Any]


class PremiumReportFinalizeIn(BaseModel):
    order_id: str
    overwrite: bool = False


class PremiumReportFinalizeOut(BaseModel):
    ok: bool
    sid: str
    order_id: str
    premium_report_token: str
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
    order_id: str
    premium_report_token: Optional[str] = None
    status: str
    has_html: bool
    has_markdown: bool
    report_url: Optional[str] = None
