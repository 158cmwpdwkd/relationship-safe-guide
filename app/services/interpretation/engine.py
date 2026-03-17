# app/services/interpretation/engine.py

from __future__ import annotations

import json
from typing import Any, Dict, List, Sequence, Set, Tuple

from .axis import calculate_axis_scores
from .confidence import calculate_confidence
from .contradictions import detect_contradictions
from .rules import extract_rule_applications
from .safety_gate import build_safety_gate
from .schemas import (
    EngineDebugBundle,
    EngineInput,
    InterpretationResult,
    PaidSurveyAnswers,
    RuleApplication,
)
from .narrative import build_narrative_context


# --------------------------------------------------
# Question mapping
# --------------------------------------------------

PAID_QUESTION_MAP = {
    "q1": "PAID_Q1_duration",
    "q2": "PAID_Q2_relationship_weight",
    "q3": "PAID_Q3_reunion_history",
    "q4": "PAID_Q4_breakup_timing",
    "q5": "PAID_Q5_last_contact_timing",
    "q6": "PAID_Q6_breakup_initiator",
    "q7": "PAID_Q7_breakup_reason",
    "q8": "PAID_Q8_issue_severity",
    "q9": "PAID_Q9_last_conversation_mood",
    "q10": "PAID_Q10_conflict_pattern",
    "q11": "PAID_Q11_partner_conflict_response",
    "q12": "PAID_Q12_my_problem_behavior",
    "q13": "PAID_Q13_channel_state",
    "q14": "PAID_Q14_recent_signal",
    "q15": "PAID_Q15_contact_after_reject",
    "q16": "PAID_Q16_response_after_contact",
    "q17": "PAID_Q17_regret_freq",
    "q18": "PAID_Q18_impulse_action",
    "q19": "PAID_Q19_changes_2w",
    "q20": "PAID_Q20_goal",
}

MULTI_KEYS = {"q18", "q19"}


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _dedupe_keep_order(items: Sequence[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for item in items:
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _safe_str(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_multi_answer(value: Any) -> List[str]:
    """
    멀티선택 방어적 정규화

    지원:
    - list[str]
    - "a,b,c"
    - "a|b|c"
    - '["a","b"]'
    - 단일 문자열 "a"
    """
    if value is None:
        return []

    if isinstance(value, list):
        return _dedupe_keep_order([_safe_str(v) for v in value if _safe_str(v)])

    if isinstance(value, tuple):
        return _dedupe_keep_order([_safe_str(v) for v in value if _safe_str(v)])

    raw = _safe_str(value)
    if not raw:
        return []

    # JSON array 문자열 대응
    if raw.startswith("[") and raw.endswith("]"):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                return _dedupe_keep_order([_safe_str(v) for v in parsed if _safe_str(v)])
        except Exception:
            pass

    for sep in ("|", ",", ";", "/"):
        if sep in raw:
            return _dedupe_keep_order([part.strip() for part in raw.split(sep) if part.strip()])

    return [raw]


def _paid_answers_to_rule_input(paid_answers: PaidSurveyAnswers) -> Dict[str, Any]:
    """
    PaidSurveyAnswers -> rules.extract_rule_applications() 입력 dict 변환
    """
    payload: Dict[str, Any] = {}

    for short_key, question_id in PAID_QUESTION_MAP.items():
        value = getattr(paid_answers, short_key)

        if short_key in MULTI_KEYS:
            payload[question_id] = _normalize_multi_answer(value)
        else:
            payload[question_id] = _safe_str(value)

    # 기타 텍스트 / 확장 텍스트
    if _safe_str(paid_answers.q7_text):
        payload["PAID_Q7_breakup_reason_other_text"] = _safe_str(paid_answers.q7_text)

    if _safe_str(paid_answers.q12_text):
        payload["PAID_Q12_my_problem_behavior_other_text"] = _safe_str(paid_answers.q12_text)

    if _safe_str(paid_answers.q20_text):
        payload["PAID_Q20_goal_other_text"] = _safe_str(paid_answers.q20_text)

    if _safe_str(paid_answers.notes):
        payload["PAID_NOTES"] = _safe_str(paid_answers.notes)

    return payload


def _collect_semantic_tags(rule_apps: List[RuleApplication]) -> List[str]:
    tags: List[str] = []
    for app in rule_apps:
        tags.extend(app.semantic_tags)
    return _dedupe_keep_order(tags)


def _derive_primary_labels(
    axis_scores,
    safety_gate,
    semantic_tags: List[str],
) -> List[str]:
    labels: List[str] = []
    tag_set = set(semantic_tags)

    if safety_gate.level == "HARD_BLOCK":
        labels.append("강한 행동 제한 필요")
    elif safety_gate.level == "HIGH_RISK":
        labels.append("고위험 접촉 국면")
    elif safety_gate.level == "ELEVATED":
        labels.append("행동 보수성 필요")

    if axis_scores.closure_strength >= 75 and axis_scores.partner_openness <= 15:
        labels.append("강한 종료 국면")
    elif axis_scores.partner_openness >= 50 and axis_scores.closure_strength < 70:
        labels.append("부분 개방 신호 존재")

    if axis_scores.stabilization_priority >= 70:
        labels.append("감정 안정화 우선")

    if axis_scores.relationship_foundation >= 65:
        labels.append("관계 기반 깊음")

    if axis_scores.emotional_fusion >= 70:
        labels.append("정서 몰입 높음")

    if "trust_damage_breakup" in tag_set:
        labels.append("신뢰 손상 이별")

    return _dedupe_keep_order(labels)[:4]


def _derive_secondary_labels(
    axis_scores,
    safety_gate,
    semantic_tags: List[str],
    free_risk_level: str,
) -> List[str]:
    labels: List[str] = []
    tag_set = set(semantic_tags)

    if free_risk_level:
        labels.append(f"무료게이트:{free_risk_level}")

    if axis_scores.immediate_risk >= 70:
        labels.append("즉시 리스크 높음")

    if axis_scores.contact_pressure >= 65:
        labels.append("재접촉 압박 높음")

    if axis_scores.partner_openness <= 10:
        labels.append("상대 경계 강함")

    if axis_scores.partner_openness >= 45:
        labels.append("최근 상호작용 단서 존재")

    if "all_channels_blocked" in tag_set:
        labels.append("전채널 차단 상태")

    if "contact_ignored" in tag_set or "ignored_after_contact" in tag_set:
        labels.append("재접촉 무응답")

    if "cold_rejection_after_contact" in tag_set:
        labels.append("명시적 거절 반응")

    if "pursue_avoid_cycle" in tag_set:
        labels.append("추격-회피 패턴")

    if "silent_cutoff_pattern" in tag_set:
        labels.append("침묵 단절 패턴")

    if safety_gate.level == "HARD_BLOCK":
        labels.append("우회접촉 금지 레벨")

    return _dedupe_keep_order(labels)[:6]


def _build_report_constraints(
    safety_gate,
    confidence,
    contradictions,
    semantic_tags: List[str],
) -> List[str]:
    constraints: List[str] = []

    constraints.extend(safety_gate.hard_constraints)

    if confidence.level == "LOW":
        constraints.append("단정적 해석 문장 최소화")
        constraints.append("가능성 예단보다 조건부 표현 사용")

    if contradictions:
        constraints.append("모순 신호 반영해 양면 서술 유지")

    if safety_gate.level in {"HIGH_RISK", "HARD_BLOCK"}:
        constraints.append("행동 제안보다 위험 완화 중심 서술")
        constraints.append("접촉 재개 전략 제시 금지")

    if "breakup_reason_other_text_present" in semantic_tags:
        constraints.append("기타 이별사유 직접입력 문맥을 보조적으로 반영")

    return _dedupe_keep_order(constraints)[:12]


# --------------------------------------------------
# Public API
# --------------------------------------------------

def run_interpretation_engine(engine_input: EngineInput) -> InterpretationResult:
    result, _ = run_interpretation_engine_with_debug(engine_input)
    return result


def run_interpretation_engine_with_debug(
    engine_input: EngineInput,
) -> Tuple[InterpretationResult, EngineDebugBundle]:
    """
    유료 해석 엔진 조립 함수

    원칙:
    - route에서 계산 금지
    - 모든 해석은 engine 내부에서만 수행
    """

    paid_rule_input = _paid_answers_to_rule_input(engine_input.paid_answers)

    rule_apps = extract_rule_applications(paid_rule_input)
    axis_scores = calculate_axis_scores(rule_apps)
    contradictions = detect_contradictions(rule_apps, axis_scores)
    safety_gate = build_safety_gate(rule_apps, axis_scores)
    confidence = calculate_confidence(rule_apps, axis_scores, contradictions, safety_gate)

    semantic_tags = _collect_semantic_tags(rule_apps)
    primary_labels = _derive_primary_labels(
        axis_scores=axis_scores,
        safety_gate=safety_gate,
        semantic_tags=semantic_tags,
    )
    secondary_labels = _derive_secondary_labels(
        axis_scores=axis_scores,
        safety_gate=safety_gate,
        semantic_tags=semantic_tags,
        free_risk_level=engine_input.free_risk_level,
    )
    report_constraints = _build_report_constraints(
        safety_gate=safety_gate,
        confidence=confidence,
        contradictions=contradictions,
        semantic_tags=semantic_tags,
    )
   
    narrative_context = build_narrative_context(
    axis_scores=axis_scores,
    safety_gate=safety_gate,
    confidence=confidence,
    contradictions=contradictions,
    semantic_tags=semantic_tags,
    primary_labels=primary_labels,
    secondary_labels=secondary_labels,
    )

    result = InterpretationResult(
        safety_gate=safety_gate,
        axis_scores=axis_scores,
        semantic_tags=semantic_tags,
        primary_labels=primary_labels,
        secondary_labels=secondary_labels,
        report_constraints=report_constraints,
        confidence=confidence,
        narrative_context=narrative_context,
    )

    debug = EngineDebugBundle(
        applied_rules=rule_apps,
        contradictions=contradictions,
    )

    return result, debug