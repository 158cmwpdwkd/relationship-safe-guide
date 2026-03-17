from __future__ import annotations

from typing import Dict, List, Set

from .schemas import AxisScores, ContradictionItem, RuleApplication


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _question_answers(rule_apps: List[RuleApplication]) -> Dict[str, Set[str]]:
    answers: Dict[str, Set[str]] = {}
    for app in rule_apps:
        answers.setdefault(app.question_id, set()).add(app.answer_value)
    return answers


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


def _has_any(container: Set[str], *values: str) -> bool:
    return any(v in container for v in values)


def _add(items: List[ContradictionItem], code: str, message: str, severity: str) -> None:
    items.append(ContradictionItem(code=code, message=message, severity=severity))


# --------------------------------------------------
# Public API
# --------------------------------------------------

def detect_contradictions(
    rule_apps: List[RuleApplication],
    axis_scores: AxisScores,
) -> List[ContradictionItem]:
    """
    응답 간 모순/해석 충돌을 탐지한다.

    원칙:
    - 점수 수정 금지
    - confidence / narrative에서 참고할 메타 정보만 생성
    - 노이즈 방지를 위해 강한 충돌만 제한적으로 탐지
    """
    items: List[ContradictionItem] = []

    answers = _question_answers(rule_apps)
    tags = _collect_tags(rule_apps)
    flags = _collect_flags(rule_apps)

    q13 = answers.get("PAID_Q13_channel_state", set())
    q14 = answers.get("PAID_Q14_recent_signal", set())
    q15 = answers.get("PAID_Q15_contact_after_reject", set())
    q16 = answers.get("PAID_Q16_response_after_contact", set())
    q17 = answers.get("PAID_Q17_regret_freq", set())
    q18 = answers.get("PAID_Q18_impulse_action", set())
    q19 = answers.get("PAID_Q19_changes_2w", set())
    q20 = answers.get("PAID_Q20_goal", set())

    # --------------------------------------------------
    # 1) 감정 vs 행동 모순
    #    예: 미련/정서 몰입이 높은데 행동 데이터는 지나치게 비어 있음
    # --------------------------------------------------
    no_impulse_behavior = q18 == {"none"} or not q18
    no_recent_change = q19 == {"none"} or not q19
    no_recontact = q16 == {"no_contact"} or not q16
    high_regret = _has_any(q17, "m70_90", "gt90")

    if (
        axis_scores.emotional_fusion >= 75
        and high_regret
        and no_impulse_behavior
        and no_recent_change
        and no_recontact
    ):
        _add(
            items,
            code="emotion_behavior_gap",
            message="정서 몰입 신호는 강한데 실제 행동/기능 저하 신호는 거의 없어 응답 일관성이 다소 낮습니다.",
            severity="MEDIUM",
        )

    # --------------------------------------------------
    # 2) 상대 신호 vs 해석 모순
    #    차단/명시적 거절/무시가 있는데 개방성이 높게 남아있는 경우
    # --------------------------------------------------
    hard_rejection_signal = (
        _has_any(q13, "all_blocked")
        or _has_any(q16, "ignored", "cold_reject")
        or _has_any(flags, "hard_boundary", "blocked_state", "explicit_rejection_signal", "ignored_after_contact")
    )

    if hard_rejection_signal and axis_scores.partner_openness >= 35:
        severity = "HIGH" if axis_scores.partner_openness >= 50 else "MEDIUM"
        _add(
            items,
            code="signal_openness_conflict",
            message="차단·무응답·명시적 거절 신호가 있는데도 상대 개방성이 비교적 높게 남아 있어 해석 충돌이 있습니다.",
            severity=severity,
        )

    # --------------------------------------------------
    # 3) 관계 기반 vs 종료 강도 충돌
    #    기반이 매우 높고 종료도 매우 강하면 단선적 해석 금지
    # --------------------------------------------------
    if (
        axis_scores.relationship_foundation >= 70
        and axis_scores.closure_strength >= 75
        and _has_any(
            tags,
            "serious_relationship_future_talk",
            "cohabitation_or_marriage_level_relationship",
            "family_level_relationship_duration",
            "deep_relationship",
        )
        and _has_any(
            tags,
            "trust_damage_breakup",
            "last_conversation_cold_but_clear",
            "last_conversation_sudden_cutoff",
            "silent_cutoff_pattern",
            "all_channels_blocked",
            "cold_rejection_after_contact",
        )
    ):
        _add(
            items,
            code="foundation_closure_tension",
            message="관계 기반은 깊었지만 종료 신호도 매우 강해 단순한 긍정/부정 해석으로 보기 어려운 상태입니다.",
            severity="MEDIUM",
        )

    # --------------------------------------------------
    # 4) 접촉 압박 vs 상대 경계 충돌
    #    반복/우회 접촉 + 상대 경계 강화
    # --------------------------------------------------
    pressure_contact = _has_any(q15, "repeated", "bypass") or _has_any(
        flags, "repeat_contact_after_reject", "bypass_contact", "pressure_behavior", "impulse_contact", "repeat_call_risk"
    )
    partner_boundary = _has_any(q13, "all_blocked", "no_reply") or _has_any(q16, "ignored", "cold_reject", "polite_distance") or _has_any(
        flags, "hard_boundary", "blocked_state", "explicit_rejection_signal", "distance_signal", "partner_hard_boundary"
    )

    if pressure_contact and partner_boundary and axis_scores.contact_pressure >= 45:
        severity = "HIGH" if _has_any(q15, "bypass") or axis_scores.contact_pressure >= 65 else "MEDIUM"
        _add(
            items,
            code="pressure_boundary_conflict",
            message="재접촉 압박 신호와 상대 경계 신호가 동시에 강해 추가 접촉 해석에 큰 주의가 필요합니다.",
            severity=severity,
        )

    # --------------------------------------------------
    # 5) 목표 vs 현재 신호 충돌
    #    재연결/재회 목표인데 현재 채널·반응은 강한 닫힘
    # --------------------------------------------------
    reconnect_goal = _has_any(q20, "reconnect", "reconcile")
    closed_state = _has_any(q13, "all_blocked") or _has_any(q16, "ignored", "cold_reject")

    if reconnect_goal and closed_state and axis_scores.partner_openness <= 15:
        _add(
            items,
            code="goal_signal_mismatch",
            message="현재 목표는 재연결 쪽이지만 실제 채널/반응 신호는 매우 닫혀 있어 목표와 현실 신호 사이 간격이 큽니다.",
            severity="MEDIUM",
        )

    # --------------------------------------------------
    # 6) 최근 긍정 신호 vs 종료 강도 과대 상태
    #    작은/부분 개방 신호가 있는데 종료 강도만 극단적으로 높음
    # --------------------------------------------------
    mild_open_signal = _has_any(q14, "small_response", "indirect_signal", "neutral_open") or _has_any(q16, "soft_open")
    hard_close_signal = _has_any(q13, "all_blocked") or _has_any(q16, "cold_reject", "ignored")

    if mild_open_signal and not hard_close_signal and axis_scores.closure_strength >= 85 and axis_scores.partner_openness >= 20:
        _add(
            items,
            code="open_signal_closure_tension",
            message="부분적으로 열린 신호가 있는데 종료 강도가 매우 높아 최근 상호작용 해석이 한쪽으로 과도할 수 있습니다.",
            severity="LOW",
        )

    # --------------------------------------------------
    # 7) 자가 안정화 목표 vs 압박 행동 지속
    #    stabilize 선택 + 접촉 압박 높음 + 충동 접촉 존재
    # --------------------------------------------------
    if (
        _has_any(q20, "stabilize")
        and axis_scores.contact_pressure >= 55
        and _has_any(q18, "contact", "call_repeat")
    ):
        _add(
            items,
            code="stabilize_pressure_gap",
            message="자기 안정화를 원한다고 응답했지만 실제 행동 신호는 접촉 압박 쪽으로 기울어 있어 목표-행동 간 불일치가 있습니다.",
            severity="LOW",
        )

    # 중복 코드 방지
    deduped: List[ContradictionItem] = []
    seen = set()
    for item in items:
        key = (item.code, item.severity)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(item)

    return deduped