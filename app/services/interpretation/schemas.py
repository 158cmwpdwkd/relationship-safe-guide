# app/services/interpretation/schemas.py

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# --------------------------------------------------
# Base
# --------------------------------------------------

class InterpretationBaseModel(BaseModel):
    class Config:
        extra = "forbid"
        str_strip_whitespace = True


# --------------------------------------------------
# Paid survey input
# --------------------------------------------------

InterpretationSchemaVersion = Literal["paid_survey_v1", "paid_survey_v2_20q"]


class PaidSurveyAnswers(InterpretationBaseModel):
    """
    유료설문 원문 응답.
    실제 선택지 해석(score_effects / semantic_tags)은 rules.py에서 처리한다.
    따라서 여기서는 입력 계약만 안정적으로 고정한다.
    """

    q1: str
    q2: str
    q3: str
    q4: str
    q5: str
    q6: str
    q7: str
    q8: str
    q9: str
    q10: str
    q11: str
    q12: str
    q13: str
    q14: str
    q15: str
    q16: str
    q17: str
    q18: List[str]
    q19: List[str]
    q20: str

    # 기타/직접입력 대응
    q7_text: Optional[str] = None
    q12_text: Optional[str] = None
    q20_text: Optional[str] = None

    # 확장 메모
    notes: Optional[str] = None


class PaidSurveyRequest(InterpretationBaseModel):
    """
    routes_premium.py에서 받게 될 유료설문 저장 + 해석 실행용 요청 모델
    """

    schema_version: InterpretationSchemaVersion = "paid_survey_v1"

    order_id: str = Field(..., min_length=1, max_length=64)
    answers: PaidSurveyAnswers

    submitted_at: Optional[datetime] = None


# --------------------------------------------------
# Axis scores
# --------------------------------------------------

class AxisScores(InterpretationBaseModel):
    immediate_risk: int = Field(..., ge=0, le=100)
    emotional_fusion: int = Field(..., ge=0, le=100)
    relationship_foundation: int = Field(..., ge=0, le=100)
    closure_strength: int = Field(..., ge=0, le=100)
    partner_openness: int = Field(..., ge=0, le=100)
    contact_pressure: int = Field(..., ge=0, le=100)
    stabilization_priority: int = Field(..., ge=0, le=100)


# --------------------------------------------------
# Safety gate
# --------------------------------------------------

SafetyLevel = Literal["LOW", "ELEVATED", "HIGH_RISK", "HARD_BLOCK"]


class SafetyGate(InterpretationBaseModel):
    """
    결제 차단용이 아니라, 리포트 행동 제한용 안전 레이어.
    """

    level: SafetyLevel = "LOW"

    reasons: List[str] = Field(default_factory=list)
    hard_constraints: List[str] = Field(default_factory=list)

    no_direct_contact_recommendation: bool = False
    avoid_pressure_behavior: bool = False
    de_escalation_priority: bool = False


# --------------------------------------------------
# Confidence
# --------------------------------------------------

ConfidenceLevel = Literal["LOW", "MEDIUM", "HIGH"]


class Confidence(InterpretationBaseModel):
    score: int = Field(..., ge=0, le=100)
    level: ConfidenceLevel

    supporting_signals: List[str] = Field(default_factory=list)
    weakening_factors: List[str] = Field(default_factory=list)
    contradictions_found: List[str] = Field(default_factory=list)


# --------------------------------------------------
# Final interpretation result
# --------------------------------------------------

class InterpretationResult(InterpretationBaseModel):
    safety_gate: SafetyGate
    axis_scores: AxisScores

    semantic_tags: List[str] = Field(default_factory=list)
    primary_labels: List[str] = Field(default_factory=list)
    secondary_labels: List[str] = Field(default_factory=list)
    report_constraints: List[str] = Field(default_factory=list)

    confidence: Confidence
    narrative_context: Dict[str, Any]


# --------------------------------------------------
# Optional internal helper payloads
# --------------------------------------------------

class RuleApplication(InterpretationBaseModel):
    """
    rules.py 내부 처리용 보조 타입
    """
    question_id: str
    answer_value: str
    score_effects: Dict[str, int] = Field(default_factory=dict)
    semantic_tags: List[str] = Field(default_factory=list)
    overrides: Dict[str, Any] = Field(default_factory=dict)
    safety_flags: List[str] = Field(default_factory=list)


class ContradictionItem(InterpretationBaseModel):
    code: str
    message: str
    severity: Literal["LOW", "MEDIUM", "HIGH"] = "LOW"


class EngineInput(InterpretationBaseModel):
    """
    engine.py 조립용 내부 입력 모델
    무료 리스크 결과 + 유료 설문 응답을 함께 넣기 위한 구조
    """

    sid: str
    order_id: str
    report_token: str

    free_risk_level: str
    free_impulse_index: Optional[int] = None
    free_answers: Dict[str, Any] = Field(default_factory=dict)

    paid_answers: PaidSurveyAnswers


class EngineDebugBundle(InterpretationBaseModel):
    """
    필요 시 디버깅/로그 저장용.
    외부 응답으로 반드시 노출할 필요는 없음.
    """

    applied_rules: List[RuleApplication] = Field(default_factory=list)
    contradictions: List[ContradictionItem] = Field(default_factory=list)
