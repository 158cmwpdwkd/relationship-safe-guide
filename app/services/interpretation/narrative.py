# app/services/interpretation/narrative.py

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Set

from .schemas import AxisScores, Confidence, ContradictionItem, SafetyGate


def _dedupe_keep_order(items: Sequence[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        if not item:
            continue
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def _tag_set(semantic_tags: List[str]) -> Set[str]:
    return set(semantic_tags or [])


def _situation_summary(
    axis_scores: AxisScores,
    safety_gate: SafetyGate,
    semantic_tags: List[str],
) -> str:
    tags = _tag_set(semantic_tags)

    # 1순위: 강한 종료 국면
    if axis_scores.closure_strength >= 75 and axis_scores.partner_openness <= 15:
        if "all_channels_blocked" in tags:
            return "현재 관계는 종료 강도가 높고 채널 차단 신호까지 겹친 강한 닫힘 국면으로 해석됩니다."
        if "contact_ignored" in tags or "ignored_after_contact" in tags:
            return "현재 관계는 종료 강도가 높고 재접촉 무응답 신호가 확인되는 닫힘 국면으로 해석됩니다."
        return "현재 관계는 종료 강도가 높고 상대 개방성이 매우 낮은 닫힘 국면으로 해석됩니다."

    # 2순위: 부분 개방
    if axis_scores.partner_openness >= 45 and axis_scores.closure_strength < 70:
        if "small_response_signal" in tags or "soft_open_response" in tags:
            return "현재 관계는 완전히 닫힌 상태라기보다 일부 반응 단서가 남아 있는 부분 개방 국면으로 보입니다."
        return "현재 관계는 종료 신호와 별개로 일부 상호작용 가능성이 남아 있는 혼합 국면으로 해석됩니다."

    # 3순위: 안정화 우선
    if axis_scores.stabilization_priority >= 70:
        return "현재는 관계 진전 판단보다 감정 안정화와 행동 조절이 우선되는 국면으로 해석됩니다."

    # 4순위: 관계 기반 깊음
    if axis_scores.relationship_foundation >= 65 and axis_scores.closure_strength >= 60:
        return "관계 기반은 깊었지만 현재 종료 압력도 뚜렷해 단선적으로 해석하기 어려운 국면입니다."

    return "현재 관계는 일부 신호가 섞여 있어 한 방향으로 단정하기보다 상태별로 나눠 해석할 필요가 있습니다."


def _state_summary(
    axis_scores: AxisScores,
    confidence: Confidence,
) -> str:
    parts: List[str] = []

    if axis_scores.emotional_fusion >= 75:
        parts.append("정서 몰입도가 높습니다")
    elif axis_scores.emotional_fusion <= 30:
        parts.append("정서 몰입도가 상대적으로 낮은 편입니다")

    if axis_scores.contact_pressure >= 70:
        parts.append("접촉 압박 욕구가 강합니다")
    elif axis_scores.contact_pressure <= 25:
        parts.append("즉각적인 재접촉 압박은 상대적으로 낮습니다")

    if axis_scores.stabilization_priority >= 70:
        parts.append("현재는 감정 안정화 우선성이 높습니다")

    if confidence.level == "LOW":
        parts.append("응답 해석 신뢰도는 보수적으로 봐야 합니다")
    elif confidence.level == "HIGH":
        parts.append("핵심 신호는 비교적 선명한 편입니다")

    if not parts:
        return "현재 상태는 일부 축이 선명하지만 행동 해석은 신중하게 다뤄야 합니다."

    return " / ".join(parts) + "."


def _risk_summary(
    safety_gate: SafetyGate,
    axis_scores: AxisScores,
) -> str:
    if safety_gate.level == "HARD_BLOCK":
        return "현재는 경계 위반으로 해석될 수 있는 행동 위험이 높아 강한 행동 제한이 필요합니다."

    if safety_gate.level == "HIGH_RISK":
        return "현재는 추가 접촉이나 확인 행동이 상황 악화 요인이 될 수 있어 행동 제한이 우선됩니다."

    if safety_gate.level == "ELEVATED":
        return "현재는 충동적 해석과 행동 가능성이 있어 접근 판단을 보수적으로 다뤄야 합니다."

    if axis_scores.stabilization_priority >= 65:
        return "뚜렷한 고위험은 아니더라도 행동 촉진보다 안정화 중심 접근이 적절합니다."

    return "현재 응답만으로 강한 위험 행동 패턴이 뚜렷하다고 보긴 어렵지만 기본적인 보수성은 유지해야 합니다."


def _contact_guidance_mode(
    safety_gate: SafetyGate,
    axis_scores: AxisScores,
) -> str:
    if safety_gate.level == "HARD_BLOCK":
        return "NO_CONTACT_STRATEGY"
    if safety_gate.level == "HIGH_RISK":
        return "CONTACT_RESTRICTED"
    if safety_gate.level == "ELEVATED":
        return "CAUTIOUS_DELAY"
    if axis_scores.partner_openness <= 15:
        return "CAUTIOUS_DELAY"
    return "STABILIZE_FIRST"


def _focus_points(
    axis_scores: AxisScores,
    safety_gate: SafetyGate,
    contradictions: List[ContradictionItem],
    semantic_tags: List[str],
) -> List[str]:
    tags = _tag_set(semantic_tags)
    items: List[str] = []

    if axis_scores.stabilization_priority >= 70:
        items.append("현재는 상대 반응 해석보다 감정 안정화와 생활 기능 회복을 우선으로 본다.")

    if axis_scores.closure_strength >= 75:
        items.append("종료 강도가 높아 희망 신호를 과대해석하지 않도록 현재 닫힘 신호를 우선 기준으로 둔다.")

    if axis_scores.partner_openness >= 45:
        items.append("부분 개방 신호가 있더라도 이를 관계 회복 신호로 단정하지 않고 범위를 제한해 해석한다.")

    if axis_scores.relationship_foundation >= 65:
        items.append("관계 기반이 깊다는 사실과 현재 종료 상태는 별개로 분리해서 해석한다.")

    if axis_scores.contact_pressure >= 65:
        items.append("재접촉 욕구가 판단을 왜곡할 수 있어 행동보다 충동 관리 기준을 먼저 세운다.")

    if contradictions:
        items.append("응답 간 모순이 있어 단일 서사보다 조건부·양면형 해석을 유지한다.")

    if "all_channels_blocked" in tags:
        items.append("채널 차단 상태는 가장 강한 경계 신호로 간주하고 모든 행동 해석의 기준점으로 둔다.")

    if "trust_damage_breakup" in tags:
        items.append("신뢰 손상 이별은 감정 잔존과 별개로 재접근 허용성을 낮출 수 있음을 반영한다.")

    if safety_gate.level in {"HIGH_RISK", "HARD_BLOCK"}:
        items.append("행동 제안은 최소화하고 위험 완화 중심으로만 정리한다.")

    return _dedupe_keep_order(items)[:6]


def _do_not_do(
    safety_gate: SafetyGate,
    contradictions: List[ContradictionItem],
    confidence: Confidence,
) -> List[str]:
    items: List[str] = list(safety_gate.hard_constraints)

    if contradictions:
        items.append("하나의 긍정 신호만 근거로 전체 관계 상태를 낙관적으로 단정하지 않는다.")

    if confidence.level == "LOW":
        items.append("모호한 신호를 확정적 의미로 번역하지 않는다.")
        items.append("상대 의도나 감정을 단정형 문장으로 표현하지 않는다.")

    items.append("재회 가능성·성공률·확률 표현을 사용하지 않는다.")
    items.append("상대 심리를 읽어주는 식의 단정 서술을 하지 않는다.")
    items.append("즉시 실행할 메시지 문장이나 연락 스크립트를 제공하지 않는다.")

    return _dedupe_keep_order(items)[:10]


def _tone_hints(
    safety_gate: SafetyGate,
    confidence: Confidence,
    axis_scores: AxisScores,
) -> List[str]:
    hints: List[str] = []

    hints.append("공감은 하되 과도한 희망 부여는 피한다.")
    hints.append("심리 단정보다 행동 안전성과 현실 신호를 우선한다.")

    if safety_gate.level in {"HIGH_RISK", "HARD_BLOCK"}:
        hints.append("단호하고 안전 중심의 문체를 사용한다.")
    else:
        hints.append("차분하고 구조화된 안내 문체를 사용한다.")

    if confidence.level == "LOW":
        hints.append("조건부 표현을 늘리고 단정형 문장을 줄인다.")

    if axis_scores.stabilization_priority >= 70:
        hints.append("행동 촉구보다 감정 안정화와 루틴 회복을 먼저 제안한다.")

    return _dedupe_keep_order(hints)[:5]


def _model_notes(
    axis_scores: AxisScores,
    confidence: Confidence,
    contradictions: List[ContradictionItem],
    semantic_tags: List[str],
) -> List[str]:
    tags = _tag_set(semantic_tags)
    notes: List[str] = []

    if confidence.level == "LOW":
        notes.append("서술 강도를 낮추고 여러 가능성을 열어둔 표현을 유지한다.")

    if contradictions:
        notes.append("모순 신호를 명시적으로 반영해 한 방향 서사로 몰아가지 않는다.")

    if axis_scores.partner_openness <= 15:
        notes.append("상대 개방성이 매우 낮으므로 접근 전략보다 경계 존중을 중심으로 서술한다.")

    if axis_scores.partner_openness >= 45 and axis_scores.closure_strength < 70:
        notes.append("부분 개방 신호가 있어도 관계 회복 신호로 확대 해석하지 않는다.")

    if "all_channels_blocked" in tags:
        notes.append("차단 상태에서는 접촉 재개를 돕는 문장이나 우회 아이디어를 생성하지 않는다.")

    if "mixed_signal_repeated" in tags:
        notes.append("혼합 신호는 불확실성으로 처리하고 낙관·비관 어느 한쪽으로 고정하지 않는다.")

    return _dedupe_keep_order(notes)[:6]


def build_narrative_context(
    axis_scores: AxisScores,
    safety_gate: SafetyGate,
    confidence: Confidence,
    contradictions: List[ContradictionItem],
    semantic_tags: List[str],
    primary_labels: List[str] | None = None,
    secondary_labels: List[str] | None = None,
) -> Dict[str, Any]:
    """
    계산 결과를 GPT 리포트 작성용 narrative context로 변환한다.
    점수 수정은 하지 않고, 서술용 구조만 생성한다.
    """
    primary_labels = primary_labels or []
    secondary_labels = secondary_labels or []

    context: Dict[str, Any] = {
        "situation_summary": _situation_summary(
            axis_scores=axis_scores,
            safety_gate=safety_gate,
            semantic_tags=semantic_tags,
        ),
        "state_summary": _state_summary(
            axis_scores=axis_scores,
            confidence=confidence,
        ),
        "risk_summary": _risk_summary(
            safety_gate=safety_gate,
            axis_scores=axis_scores,
        ),
        "contact_guidance_mode": _contact_guidance_mode(
            safety_gate=safety_gate,
            axis_scores=axis_scores,
        ),
        "focus_points": _focus_points(
            axis_scores=axis_scores,
            safety_gate=safety_gate,
            contradictions=contradictions,
            semantic_tags=semantic_tags,
        ),
        "do_not_do": _do_not_do(
            safety_gate=safety_gate,
            contradictions=contradictions,
            confidence=confidence,
        ),
        "tone_hints": _tone_hints(
            safety_gate=safety_gate,
            confidence=confidence,
            axis_scores=axis_scores,
        ),
        "model_notes": _model_notes(
            axis_scores=axis_scores,
            confidence=confidence,
            contradictions=contradictions,
            semantic_tags=semantic_tags,
        ),
        "primary_labels": primary_labels,
        "secondary_labels": secondary_labels,
        "confidence_level": confidence.level,
        "safety_level": safety_gate.level,
    }

    return context