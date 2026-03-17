# app/services/interpretation/axis.py

from __future__ import annotations

from typing import Dict, List, Any

from .schemas import AxisScores, RuleApplication


# --------------------------------------------------
# Axis config
# --------------------------------------------------

BASE_AXES = [
    "immediate_risk",
    "emotional_fusion",
    "relationship_foundation",
    "closure_strength",
    "partner_openness",
    "contact_pressure",
]

ALL_AXES = BASE_AXES + ["stabilization_priority"]


# raw 점수 상한선
# 정규화 기준값이며 운영 중 튜닝 가능
AXIS_RAW_CAPS: Dict[str, int] = {
    "immediate_risk": 140,
    "emotional_fusion": 180,
    "relationship_foundation": 180,
    "closure_strength": 320,
    "partner_openness": 140,
    "contact_pressure": 180,
    "stabilization_priority": 160,  # direct raw 참고용
}


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(value, high))


def _normalize_axis(raw_score: int, cap: int) -> int:
    """
    raw score를 cap 기준 0~100으로 정규화
    """
    if cap <= 0:
        raise ValueError(f"Axis cap must be > 0, got: {cap}")
    normalized = round((_clamp(raw_score, 0, cap) / cap) * 100)
    return int(_clamp(normalized, 0, 100))


def _empty_raw_scores() -> Dict[str, int]:
    return {axis: 0 for axis in ALL_AXES}


# --------------------------------------------------
# Raw aggregation
# --------------------------------------------------

def aggregate_raw_axis_scores(rule_apps: List[RuleApplication]) -> Dict[str, int]:
    """
    RuleApplication 리스트를 받아 raw axis score를 축별 합산한다.
    """
    raw_scores = _empty_raw_scores()

    for app in rule_apps:
        for axis, value in app.score_effects.items():
            if axis not in raw_scores:
                raise ValueError(f"Unknown axis found during aggregation: {axis}")
            raw_scores[axis] += int(value)

    return raw_scores


# --------------------------------------------------
# Derived axis
# --------------------------------------------------

def derive_stabilization_priority(
    normalized_base_scores: Dict[str, int],
    direct_stabilization_normalized: int,
) -> int:
    """
    stabilization_priority는 파생축 우선.
    계산식:
      immediate_risk * 0.35
    + emotional_fusion * 0.25
    + contact_pressure * 0.20
    + closure_strength * 0.15
    + direct_stabilization * 0.20
    - partner_openness * 0.10
    - relationship_foundation * 0.05
    """

    immediate_risk = normalized_base_scores["immediate_risk"]
    emotional_fusion = normalized_base_scores["emotional_fusion"]
    contact_pressure = normalized_base_scores["contact_pressure"]
    closure_strength = normalized_base_scores["closure_strength"]
    partner_openness = normalized_base_scores["partner_openness"]
    relationship_foundation = normalized_base_scores["relationship_foundation"]

    derived = (
        immediate_risk * 0.35
        + emotional_fusion * 0.25
        + contact_pressure * 0.20
        + closure_strength * 0.15
        + direct_stabilization_normalized * 0.20
        - partner_openness * 0.10
        - relationship_foundation * 0.05
    )

    return int(round(_clamp(derived, 0, 100)))


# --------------------------------------------------
# Public API
# --------------------------------------------------

def calculate_axis_scores(rule_apps: List[RuleApplication]) -> AxisScores:
    raw_scores = aggregate_raw_axis_scores(rule_apps)

    normalized_base_scores: Dict[str, int] = {}

    for axis in BASE_AXES:
        normalized_base_scores[axis] = _normalize_axis(
            raw_score=raw_scores[axis],
            cap=AXIS_RAW_CAPS[axis],
        )

    normalized_base_scores["partner_openness"] = adjust_partner_openness(
        base_partner_openness=normalized_base_scores["partner_openness"],
        rule_apps=rule_apps,
    )

    direct_stabilization_normalized = _normalize_axis(
        raw_score=raw_scores["stabilization_priority"],
        cap=AXIS_RAW_CAPS["stabilization_priority"],
    )

    stabilization_priority = derive_stabilization_priority(
        normalized_base_scores=normalized_base_scores,
        direct_stabilization_normalized=direct_stabilization_normalized,
    )

    return AxisScores(
        immediate_risk=normalized_base_scores["immediate_risk"],
        emotional_fusion=normalized_base_scores["emotional_fusion"],
        relationship_foundation=normalized_base_scores["relationship_foundation"],
        closure_strength=normalized_base_scores["closure_strength"],
        partner_openness=normalized_base_scores["partner_openness"],
        contact_pressure=normalized_base_scores["contact_pressure"],
        stabilization_priority=stabilization_priority,
    )


def collect_axis_debug(rule_apps: List[RuleApplication]) -> Dict[str, Any]:
    raw_scores = aggregate_raw_axis_scores(rule_apps)

    normalized_base_scores: Dict[str, int] = {}
    contributions: Dict[str, List[Dict[str, Any]]] = {axis: [] for axis in ALL_AXES}

    for app in rule_apps:
        for axis, value in app.score_effects.items():
            contributions[axis].append(
                {
                    "question_id": app.question_id,
                    "answer_value": app.answer_value,
                    "value": int(value),
                    "semantic_tags": list(app.semantic_tags),
                    "safety_flags": list(app.safety_flags),
                }
            )

    for axis in BASE_AXES:
        normalized_base_scores[axis] = _normalize_axis(
            raw_score=raw_scores[axis],
            cap=AXIS_RAW_CAPS[axis],
        )

    partner_openness_before_adjust = normalized_base_scores["partner_openness"]
    normalized_base_scores["partner_openness"] = adjust_partner_openness(
        base_partner_openness=partner_openness_before_adjust,
        rule_apps=rule_apps,
    )

    direct_stabilization_normalized = _normalize_axis(
        raw_score=raw_scores["stabilization_priority"],
        cap=AXIS_RAW_CAPS["stabilization_priority"],
    )

    derived_stabilization = derive_stabilization_priority(
        normalized_base_scores=normalized_base_scores,
        direct_stabilization_normalized=direct_stabilization_normalized,
    )

    return {
        "raw_scores": raw_scores,
        "caps": dict(AXIS_RAW_CAPS),
        "normalized_base_scores": normalized_base_scores,
        "partner_openness_before_adjust": partner_openness_before_adjust,
        "partner_openness_after_adjust": normalized_base_scores["partner_openness"],
        "direct_stabilization_normalized": direct_stabilization_normalized,
        "derived_stabilization_priority": derived_stabilization,
        "contributions": contributions,
    }

def adjust_partner_openness(
    base_partner_openness: int,
    rule_apps: List[RuleApplication],
) -> int:
    """
    닫힘 신호가 강할 때 partner_openness를 하향 보정한다.
    """
    safety_flags = set()
    semantic_tags = set()
    answers_by_question: Dict[str, List[str]] = {}

    for app in rule_apps:
        safety_flags.update(app.safety_flags)
        semantic_tags.update(app.semantic_tags)
        answers_by_question.setdefault(app.question_id, []).append(app.answer_value)

    penalty = 0

    # 강한 경계 신호
    if "hard_boundary" in safety_flags or "blocked_state" in safety_flags:
        penalty += 45

    if "explicit_rejection_signal" in safety_flags:
        penalty += 35

    if "ignored_after_contact" in safety_flags:
        penalty += 25

    if "partner_hard_boundary" in safety_flags:
        penalty += 20

    if "distance_signal" in safety_flags:
        penalty += 12

    if "bypass_contact" in safety_flags:
        penalty += 10

    if "repeat_contact_after_reject" in safety_flags:
        penalty += 10

    # 특정 응답 직접 보정
    q13 = answers_by_question.get("PAID_Q13_channel_state", [])
    if "all_blocked" in q13:
        penalty += 20
    elif "no_reply" in q13:
        penalty += 12

    q16 = answers_by_question.get("PAID_Q16_response_after_contact", [])
    if "cold_reject" in q16:
        penalty += 18
    elif "ignored" in q16:
        penalty += 12

    adjusted = base_partner_openness - penalty
    return int(_clamp(adjusted, 0, 100))