# app/services/interpretation/safety_gate.py

from __future__ import annotations

from typing import List, Set

from .schemas import AxisScores, RuleApplication, SafetyGate


# --------------------------------------------------
# helpers
# --------------------------------------------------

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


def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


# --------------------------------------------------
# rule evaluation
# --------------------------------------------------

def build_safety_gate(
    rule_apps: List[RuleApplication],
    axis_scores: AxisScores,
) -> SafetyGate:
    """
    유료 해석용 safety gate

    원칙:
    - 리포트 제공 차단용이 아니라 행동 제한 생성용
    - 점수 수정 금지
    - narrative / premium_report에서 안전 제한을 걸 수 있도록
      level / reasons / hard_constraints 생성
    """

    tags = _collect_tags(rule_apps)
    flags = _collect_flags(rule_apps)

    reasons: List[str] = []
    hard_constraints: List[str] = []

    level = "LOW"

    # --------------------------------------------------
    # HARD_BLOCK 조건
    # --------------------------------------------------
    hard_block = False

    if _has_any(
        flags,
        "threat_or_intimidation",
        "revenge_intent",
        "surveillance_behavior",
        "stalking_pattern",
        "offline_visit_risk",
        "coercive_contact",
    ):
        hard_block = True
        reasons.append("위협·감시·보복성 접근으로 해석될 수 있는 고위험 신호가 확인됩니다.")

    if _has_any(
        flags,
        "bypass_contact",
        "high_boundary_risk",
    ) and _has_any(
        flags,
        "hard_boundary",
        "blocked_state",
        "explicit_rejection_signal",
    ):
        hard_block = True
        reasons.append("상대의 명확한 경계 이후 우회 접촉 신호가 있어 안전 제한이 강하게 필요합니다.")

    if (
        axis_scores.contact_pressure >= 85
        and axis_scores.immediate_risk >= 75
        and _has_any(flags, "repeat_contact_after_reject", "bypass_contact", "impulse_contact")
    ):
        hard_block = True
        reasons.append("접촉 압박과 즉시 리스크가 모두 높고 반복 접근 신호가 동반됩니다.")

    if hard_block:
        level = "HARD_BLOCK"

        hard_constraints.extend([
            "직접 재접촉 문장 생성 금지",
            "우회 연락 제안 금지",
            "집 앞 방문/대면 시도 제안 금지",
            "감시·확인·추적 행동 정당화 금지",
            "상대 반응을 떠보는 실험성 접근 제안 금지",
        ])

    # --------------------------------------------------
    # HIGH_RISK 조건
    # --------------------------------------------------
    if level != "HARD_BLOCK":
        high_risk = False

        if _has_any(flags, "repeat_contact_after_reject") and _has_any(
            flags, "hard_boundary", "blocked_state", "explicit_rejection_signal"
        ):
            high_risk = True
            reasons.append("거절 또는 차단 이후 반복 접촉 신호가 확인됩니다.")

        if (
            axis_scores.contact_pressure >= 70
            and axis_scores.partner_openness <= 15
            and _has_any(flags, "impulse_contact", "repeat_call_risk", "pressure_behavior")
        ):
            high_risk = True
            reasons.append("상대 개방성은 낮은데 접촉 압박이 높아 추가 접근이 악화 요인이 될 수 있습니다.")

        if (
            axis_scores.immediate_risk >= 70
            and axis_scores.emotional_fusion >= 80
            and axis_scores.stabilization_priority >= 75
        ):
            high_risk = True
            reasons.append("감정 과부하가 높아 현재는 관계 해석보다 안정화가 우선입니다.")

        if high_risk:
            level = "HIGH_RISK"
            hard_constraints.extend([
                "직접 재접촉 문장 생성 금지",
                "관계 회복을 위한 즉시 행동 제안 금지",
                "확인성 메시지·시험성 연락 제안 금지",
                "침묵을 깨기 위한 추가 압박 행동 제안 금지",
            ])

    # --------------------------------------------------
    # ELEVATED 조건
    # --------------------------------------------------
    if level == "LOW":
        elevated = False

        if axis_scores.immediate_risk >= 50:
            elevated = True
            reasons.append("정서적 흔들림이 커 충동적 판단 가능성을 고려해야 합니다.")

        if axis_scores.emotional_fusion >= 70:
            elevated = True
            reasons.append("상대 중심 몰입도가 높아 자기해석 편향 가능성이 있습니다.")

        if axis_scores.contact_pressure >= 50:
            elevated = True
            reasons.append("접촉 욕구 또는 압박 신호가 있어 행동 가이드를 보수적으로 볼 필요가 있습니다.")

        if axis_scores.stabilization_priority >= 65:
            elevated = True
            reasons.append("현재는 관계 개선보다 감정 안정화 우선성이 비교적 높습니다.")

        if _has_any(flags, "blocked_state", "distance_signal", "ignored_after_contact"):
            elevated = True
            reasons.append("상대 경계/거리두기 신호가 있어 신중한 접근이 필요합니다.")

        if elevated:
            level = "ELEVATED"
            hard_constraints.extend([
                "즉시 재접촉 유도 문장 생성 금지",
                "상대 의도를 단정하는 해석 금지",
            ])

    # --------------------------------------------------
    # LOW 보조 reason
    # --------------------------------------------------
    if level == "LOW":
        reasons.append("현재 응답에서는 강한 위험 행동 신호가 두드러지지 않습니다.")
        hard_constraints.extend([
            "재회 가능성 단정 금지",
            "상대 심리 단정 금지",
        ])

    # --------------------------------------------------
    # 공통 제약 추가
    # --------------------------------------------------
    hard_constraints.extend([
        "재회 성공 확률 제시 금지",
        "상대 심리 단정 금지",
        "강압적 행동 정당화 금지",
    ])

    # 상대가 닫혀 있으면 공통 강화
    if axis_scores.partner_openness <= 10 or _has_any(flags, "hard_boundary", "blocked_state"):
        hard_constraints.append("거절/차단 상태를 무시하는 접근 제안 금지")

    # 안정화 우선이면 추가 강화
    if axis_scores.stabilization_priority >= 75:
        hard_constraints.append("행동 촉진보다 감정 안정화 중심으로만 가이드")

    return SafetyGate(
        level=level,
        reasons=_dedupe_keep_order(reasons)[:6],
        hard_constraints=_dedupe_keep_order(hard_constraints)[:10],
    )