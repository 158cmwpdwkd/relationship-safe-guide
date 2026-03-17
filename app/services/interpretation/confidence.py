# app/services/interpretation/confidence.py

from __future__ import annotations

from typing import Dict, List, Set

from .schemas import (
    AxisScores,
    Confidence,
    ContradictionItem,
    RuleApplication,
    SafetyGate,
)


# --------------------------------------------------
# helpers
# --------------------------------------------------

def _clamp(value: int, low: int = 0, high: int = 100) -> int:
    return max(low, min(value, high))


def _collect_tags(rule_apps: List[RuleApplication]) -> Set[str]:
    tags: Set[str] = set()
    for app in rule_apps:
        tags.update(app.semantic_tags)
    return tags


def _collect_flags(rule_apps: List[RuleApplication]) -> Set[str]:
    flags: Set[str] = set()
    for app in rule_apps:
        flags.update(app.safety_flags)
    return flags


def _sum_override_penalties(rule_apps: List[RuleApplication]) -> int:
    total = 0
    for app in rule_apps:
        raw = app.overrides.get("confidence_penalty", 0)
        try:
            total += int(raw)
        except (TypeError, ValueError):
            continue
    return total


def _contradiction_penalty(items: List[ContradictionItem]) -> int:
    penalty_map = {
        "LOW": 4,
        "MEDIUM": 8,
        "HIGH": 14,
    }
    return sum(penalty_map.get(item.severity, 0) for item in items)


def _level_from_score(score: int) -> str:
    if score >= 80:
        return "HIGH"
    if score >= 55:
        return "MEDIUM"
    return "LOW"


# --------------------------------------------------
# signal text builders
# --------------------------------------------------

def _supporting_signals(
    axis_scores: AxisScores,
    tags: Set[str],
    flags: Set[str],
) -> List[str]:
    signals: List[str] = []

    if axis_scores.closure_strength >= 75:
        signals.append("종료 강도 축이 비교적 선명하게 형성되어 있습니다.")

    if axis_scores.partner_openness <= 15:
        signals.append("상대 개방성이 매우 낮아 현재 관계 접근 가능성 해석이 비교적 분명합니다.")

    if axis_scores.partner_openness >= 60:
        signals.append("상대 개방성 축이 높게 형성되어 최근 상호작용 해석 단서가 비교적 분명합니다.")

    if axis_scores.relationship_foundation >= 65:
        signals.append("관계 기반 정보가 충분히 잡혀 있어 맥락 해석 안정성이 높습니다.")

    if axis_scores.stabilization_priority >= 70:
        signals.append("현재는 행동 해석보다 안정화 우선 필요성이 명확하게 드러납니다.")

    if "all_channels_blocked" in tags or "contact_ignored" in tags or "cold_rejection_after_contact" in tags:
        signals.append("채널 상태/최근 반응 신호가 해석에 직접적인 기준점으로 작동합니다.")

    if "soft_open_response" in tags or "small_response_signal" in tags or "indirect_signal_present" in tags:
        signals.append("최근 반응 신호가 일부 존재해 현재 상호작용 국면을 읽을 단서가 있습니다.")

    # 중복 제거
    deduped: List[str] = []
    seen = set()
    for s in signals:
        if s in seen:
            continue
        seen.add(s)
        deduped.append(s)
    return deduped[:5]


def _weakening_factors(
    axis_scores: AxisScores,
    tags: Set[str],
    flags: Set[str],
    rule_apps: List[RuleApplication],
    contradictions: List[ContradictionItem],
    safety_gate: SafetyGate,
) -> List[str]:
    items: List[str] = []

    override_penalty = _sum_override_penalties(rule_apps)
    if override_penalty > 0:
        items.append(f"일부 응답에 불명확 선택이 있어 신뢰도 보정값 {override_penalty}점이 반영되었습니다.")

    if any("unknown" in tag or "unclear" in tag for tag in tags):
        items.append("일부 문항에 불명확/유보 응답이 있어 해석 선명도가 낮아질 수 있습니다.")

    if "mixed_signal_repeated" in tags or "mixed_response_after_contact" in tags:
        items.append("최근 신호가 혼합적이라 한 방향으로 단정하기 어렵습니다.")

    if "channel_state_unknown" in tags or "recent_signal_unknown" in tags or "goal_unclear" in tags:
        items.append("현재 채널 상태 또는 목표 방향이 일부 불명확합니다.")

    if contradictions:
        items.append(f"응답 간 해석 충돌 {len(contradictions)}건이 탐지되어 신뢰도를 낮춰 반영했습니다.")

    if safety_gate.level == "HARD_BLOCK":
        items.append("강한 경계 위반 위험이 있어 행동 제한이 최우선으로 적용됩니다.")
    elif safety_gate.level == "HIGH_RISK":
        items.append("현재는 관계 해석보다 행동 제한과 안정화 판단이 우선되는 상태입니다.")
    elif safety_gate.level == "ELEVATED":
        items.append("정서 및 접촉 리스크가 있어 해석보다 행동 보수성이 우선될 수 있습니다.")

    if axis_scores.emotional_fusion >= 80 and axis_scores.contact_pressure >= 70:
        items.append("정서 몰입과 접촉 압박이 함께 높아 자기해석 편향 가능성을 고려해야 합니다.")

    # 중복 제거
    deduped: List[str] = []
    seen = set()
    for s in items:
        if s in seen:
            continue
        seen.add(s)
        deduped.append(s)
    return deduped[:6]


# --------------------------------------------------
# scoring
# --------------------------------------------------

def _score_bonus(
    axis_scores: AxisScores,
    tags: Set[str],
    flags: Set[str],
) -> int:
    bonus = 0

    # 1) 축 선명도 보너스
    strong_axes = 0
    for value in [
        axis_scores.immediate_risk,
        axis_scores.emotional_fusion,
        axis_scores.relationship_foundation,
        axis_scores.closure_strength,
        axis_scores.partner_openness,
        axis_scores.contact_pressure,
        axis_scores.stabilization_priority,
    ]:
        if value >= 70 or value <= 15:
            strong_axes += 1

    if strong_axes >= 4:
        bonus += 6
    elif strong_axes >= 2:
        bonus += 3

    # 2) 닫힘 신호 일치 보너스
    if (
        axis_scores.partner_openness <= 15
        and axis_scores.closure_strength >= 70
        and (
            "all_channels_blocked" in tags
            or "contact_ignored" in tags
            or "cold_rejection_after_contact" in tags
        )
    ):
        bonus += 6

    # 3) 부분 개방 신호 일치 보너스
    if (
        axis_scores.partner_openness >= 45
        and (
            "small_response_signal" in tags
            or "indirect_signal_present" in tags
            or "soft_open_response" in tags
        )
    ):
        bonus += 5

    # 4) 관계 기반이 충분한 경우
    if axis_scores.relationship_foundation >= 65:
        bonus += 4

    # 5) fresh breakup은 현재 상태 파악에는 오히려 일관적일 수 있음
    if "fresh_breakup" in flags and axis_scores.immediate_risk >= 55:
        bonus += 2

    return bonus


def _score_penalty(
    axis_scores: AxisScores,
    tags: Set[str],
    flags: Set[str],
    rule_apps: List[RuleApplication],
    contradictions: List[ContradictionItem],
    safety_gate: SafetyGate,
) -> int:
    penalty = 0

    # 1) 명시 override penalty
    penalty += _sum_override_penalties(rule_apps)

    # 2) contradiction penalty
    penalty += _contradiction_penalty(contradictions)

    # 3) unclear / unknown 신호
    unknown_unclear_count = sum(
        1 for tag in tags if ("unknown" in tag or "unclear" in tag)
    )
    penalty += min(unknown_unclear_count * 4, 12)

    # 4) mixed signal
    if "mixed_signal_repeated" in tags:
        penalty += 6
    if "mixed_response_after_contact" in tags:
        penalty += 5
    if "last_conversation_mixed_closure_and_attachment" in tags:
        penalty += 4

    # 5) safety gate 가 높으면 해석 신뢰도보다 행동 제한이 우선
    if safety_gate.level == "HARD_BLOCK":
        penalty += 15
    elif safety_gate.level == "HIGH_RISK":
        penalty += 10
    elif safety_gate.level == "ELEVATED":
        penalty += 5

    # 6) 과몰입 + 접촉압박 동시 고점
    if axis_scores.emotional_fusion >= 80 and axis_scores.contact_pressure >= 70:
        penalty += 5

    # 7) 관계 기반이 너무 낮고, 신호도 약한 경우
    if (
        axis_scores.relationship_foundation <= 20
        and axis_scores.partner_openness <= 20
        and axis_scores.closure_strength <= 35
    ):
        penalty += 6

    return penalty


# --------------------------------------------------
# public api
# --------------------------------------------------

def calculate_confidence(
    rule_apps: List[RuleApplication],
    axis_scores: AxisScores,
    contradictions: List[ContradictionItem],
    safety_gate: SafetyGate,
) -> Confidence:
    """
    해석 신뢰도 계산

    원칙:
    - axis 점수 수정 금지
    - contradictions는 감점 근거로만 사용
    - 불명확/혼합/리스크가 높을수록 confidence 하향
    """

    tags = _collect_tags(rule_apps)
    flags = _collect_flags(rule_apps)

    base_score = 75
    bonus = _score_bonus(axis_scores=axis_scores, tags=tags, flags=flags)
    penalty = _score_penalty(
        axis_scores=axis_scores,
        tags=tags,
        flags=flags,
        rule_apps=rule_apps,
        contradictions=contradictions,
        safety_gate=safety_gate,
    )

    final_score = _clamp(base_score + bonus - penalty, 0, 100)
    level = _level_from_score(final_score)

    supporting = _supporting_signals(
        axis_scores=axis_scores,
        tags=tags,
        flags=flags,
    )

    weakening = _weakening_factors(
        axis_scores=axis_scores,
        tags=tags,
        flags=flags,
        rule_apps=rule_apps,
        contradictions=contradictions,
        safety_gate=safety_gate,
    )

    contradiction_codes = [item.code for item in contradictions]

    return Confidence(
        score=final_score,
        level=level,
        supporting_signals=supporting,
        weakening_factors=weakening,
        contradictions_found=contradiction_codes,
    )