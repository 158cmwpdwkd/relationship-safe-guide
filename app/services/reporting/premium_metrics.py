from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _as_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, (tuple, set)):
        return list(value)
    return [value]


def _clamp_int(value: float, low: int = 0, high: int = 100) -> int:
    return int(max(low, min(high, round(value))))


def _tone_from_score(score: int) -> str:
    if score >= 85:
        return "danger"
    if score >= 65:
        return "warning"
    if score >= 40:
        return "caution"
    return "stable"


def _inverse_tone_from_score(score: int) -> str:
    if score <= 20:
        return "danger"
    if score <= 40:
        return "warning"
    if score <= 65:
        return "caution"
    return "stable"


def _label_by_steps(
    score: int,
    *,
    steps: Sequence[tuple[int, str]],
    default: str,
) -> str:
    for min_score, label in steps:
        if score >= min_score:
            return label
    return default


def _safety_penalty(level: str) -> int:
    normalized = (level or "").upper().strip()
    if normalized == "HARD_BLOCK":
        return 20
    if normalized == "HIGH_RISK":
        return 12
    if normalized == "ELEVATED":
        return 6
    return 0


def _risk_base_score(level: str, immediate_risk: int, contact_pressure: int) -> int:
    normalized = (level or "").upper().strip()
    if normalized == "HARD_BLOCK":
        return max(90, immediate_risk)
    if normalized == "HIGH_RISK":
        return max(78, int((immediate_risk * 0.7) + (contact_pressure * 0.3)))
    if normalized == "ELEVATED":
        return max(58, int((immediate_risk * 0.65) + (contact_pressure * 0.35)))
    return max(28, int((immediate_risk * 0.6) + (contact_pressure * 0.4)))


def _make_card(
    *,
    card_id: str,
    title: str,
    score: int,
    value_text: str,
    tone: str,
    summary: str,
    source_keys: List[str],
) -> Dict[str, Any]:
    return {
        "id": card_id,
        "title": title,
        "score": int(score),
        "value_text": value_text,
        "tone": tone,
        "summary": summary,
        "source_keys": source_keys,
    }


def _build_relationship_distance_card(
    *,
    axis_scores: Dict[str, Any],
    safety_level: str,
    semantic_tags: List[str],
) -> Dict[str, Any]:
    closure_strength = int(axis_scores.get("closure_strength", 0))
    partner_openness = int(axis_scores.get("partner_openness", 0))
    immediate_risk = int(axis_scores.get("immediate_risk", 0))
    contact_pressure = int(axis_scores.get("contact_pressure", 0))

    tag_set = set(str(x).strip() for x in semantic_tags if str(x).strip())

    score = (
        (closure_strength * 0.45)
        + ((100 - partner_openness) * 0.35)
        + (immediate_risk * 0.10)
        + (contact_pressure * 0.10)
    )
    score += _safety_penalty(safety_level)

    if "all_channels_blocked" in tag_set:
        score += 8
    if "contact_ignored" in tag_set or "ignored_after_contact" in tag_set:
        score += 6
    if "cold_rejection_after_contact" in tag_set:
        score += 5

    score = _clamp_int(score)

    return _make_card(
        card_id="relationship_distance",
        title="📏 관계 거리감",
        score=score,
        value_text=_label_by_steps(
            score,
            steps=[(80, "🚫 매우 높음"), (60, "📉 높음"), (40, "📍 벌어짐")],
            default="🤝 상대적으로 낮음",
        ),
        tone=_tone_from_score(score),
        summary=(
            "현재 관계가 얼마나 멀어진 상태로 보이는지 정리한 지표입니다. 종료감, 상대의 개방성, "
            "경계 관련 신호를 바탕으로 해석하며, 성공 가능성을 뜻하지는 않습니다."
        ),
        source_keys=[
            "axis_scores.closure_strength",
            "axis_scores.partner_openness",
            "axis_scores.immediate_risk",
            "axis_scores.contact_pressure",
            "safety_gate.level",
            "semantic_tags",
        ],
    )


def _build_emotional_temperature_card(
    *,
    axis_scores: Dict[str, Any],
    safety_level: str,
) -> Dict[str, Any]:
    emotional_fusion = int(axis_scores.get("emotional_fusion", 0))
    immediate_risk = int(axis_scores.get("immediate_risk", 0))
    contact_pressure = int(axis_scores.get("contact_pressure", 0))
    stabilization_priority = int(axis_scores.get("stabilization_priority", 0))

    score = (
        (emotional_fusion * 0.55)
        + (immediate_risk * 0.20)
        + (contact_pressure * 0.15)
        + (stabilization_priority * 0.10)
    )
    score += int(_safety_penalty(safety_level) * 0.5)
    score = _clamp_int(score)

    return _make_card(
        card_id="emotional_temperature",
        title="🌡 감정 온도",
        score=score,
        value_text=_label_by_steps(
            score,
            steps=[(80, "🚨 매우 뜨거움"), (60, "🔥 높아진 상태"), (40, "💫 불안정함")],
            default="🌿 비교적 차분함",
        ),
        tone=_tone_from_score(score),
        summary=(
            "현재 상태의 감정 강도와 흔들림을 보여주는 지표입니다. "
            "관계의 좋고 나쁨이 아니라 감정 조절 필요성을 반영합니다."
        ),
        source_keys=[
            "axis_scores.emotional_fusion",
            "axis_scores.immediate_risk",
            "axis_scores.contact_pressure",
            "axis_scores.stabilization_priority",
            "safety_gate.level",
        ],
    )


def _build_contact_timing_card(
    *,
    axis_scores: Dict[str, Any],
    safety_level: str,
    narrative_context: Dict[str, Any],
) -> Dict[str, Any]:
    relationship_foundation = int(axis_scores.get("relationship_foundation", 0))
    partner_openness = int(axis_scores.get("partner_openness", 0))
    closure_strength = int(axis_scores.get("closure_strength", 0))
    immediate_risk = int(axis_scores.get("immediate_risk", 0))
    stabilization_priority = int(axis_scores.get("stabilization_priority", 0))

    contact_mode = str(narrative_context.get("contact_guidance_mode", "")).upper().strip()

    raw_score = (
        (relationship_foundation * 0.35)
        + (partner_openness * 0.30)
        + ((100 - closure_strength) * 0.20)
        + ((100 - immediate_risk) * 0.10)
        + ((100 - stabilization_priority) * 0.05)
    )

    if safety_level == "HARD_BLOCK":
        score = min(12, _clamp_int(raw_score))
        value_text = "⛔ 지금은 보류"
        tone = "danger"
    elif safety_level == "HIGH_RISK":
        score = min(28, _clamp_int(raw_score))
        value_text = "🧊 당분간 미루기"
        tone = "warning"
    elif contact_mode == "CAUTIOUS_DELAY" or partner_openness <= 15:
        score = min(45, _clamp_int(raw_score))
        value_text = "⏸ 기다리며 재평가"
        tone = "warning"
    elif contact_mode == "STABILIZE_FIRST" or stabilization_priority >= 65:
        score = min(55, _clamp_int(raw_score))
        value_text = "⏸ 안정화 우선"
        tone = "caution"
    else:
        score = _clamp_int(raw_score)
        value_text = "🟡 신중한 판단 필요"
        tone = "stable" if score >= 60 else "caution"

    return _make_card(
        card_id="contact_timing",
        title="⏳ 연락 타이밍",
        score=score,
        value_text=value_text,
        tone=tone,
        summary=(
            "어떤 접근이든 시도하기 전에 어느 정도의 시간 간격과 자제가 필요한지 보여주는 지표입니다. "
            "행동을 권하는 신호가 아니라 판단을 제한하는 기준입니다."
        ),
        source_keys=[
            "axis_scores.relationship_foundation",
            "axis_scores.partner_openness",
            "axis_scores.closure_strength",
            "axis_scores.immediate_risk",
            "axis_scores.stabilization_priority",
            "narrative_context.contact_guidance_mode",
            "safety_gate.level",
        ],
    )


def _build_risk_signal_card(
    *,
    axis_scores: Dict[str, Any],
    safety_gate: Dict[str, Any],
) -> Dict[str, Any]:
    safety_level = str(safety_gate.get("level", "")).upper().strip()
    immediate_risk = int(axis_scores.get("immediate_risk", 0))
    contact_pressure = int(axis_scores.get("contact_pressure", 0))
    reasons = [str(x).strip() for x in _as_list(safety_gate.get("reasons", [])) if str(x).strip()]

    score = _risk_base_score(safety_level, immediate_risk, contact_pressure)

    if safety_level == "HARD_BLOCK":
        value_text = "🔴 강한 제한 필요"
        tone = "danger"
    elif safety_level == "HIGH_RISK":
        value_text = "🟠 높은 주의 필요"
        tone = "warning"
    elif safety_level == "ELEVATED":
        value_text = "🟡 주의 필요"
        tone = "caution"
    else:
        value_text = "🟢 상대적으로 낮음"
        tone = "stable"

    first_reason = reasons[0] if reasons else "현재 응답에서는 두드러지는 고위험 행동 신호가 확인되지 않습니다."

    return _make_card(
        card_id="current_risk_signal",
        title="🚨 현재 위험 신호",
        score=score,
        value_text=value_text,
        tone=tone,
        summary=f"현재 위험 패턴을 안전 우선 관점에서 해석한 결과입니다. {first_reason}",
        source_keys=[
            "safety_gate.level",
            "safety_gate.reasons",
            "axis_scores.immediate_risk",
            "axis_scores.contact_pressure",
        ],
    )


def _build_recovery_conditions_card(
    *,
    axis_scores: Dict[str, Any],
    safety_level: str,
) -> Dict[str, Any]:
    relationship_foundation = int(axis_scores.get("relationship_foundation", 0))
    partner_openness = int(axis_scores.get("partner_openness", 0))
    closure_strength = int(axis_scores.get("closure_strength", 0))
    immediate_risk = int(axis_scores.get("immediate_risk", 0))

    score = (
        (relationship_foundation * 0.45)
        + (partner_openness * 0.30)
        + ((100 - closure_strength) * 0.15)
        + ((100 - immediate_risk) * 0.10)
    )

    if safety_level == "HARD_BLOCK":
        score = min(15, _clamp_int(score))
    elif safety_level == "HIGH_RISK":
        score = min(35, _clamp_int(score))
    else:
        score = _clamp_int(score)

    return _make_card(
        card_id="recovery_conditions",
        title="🌱 회복 가능 조건",
        score=score,
        value_text=_label_by_steps(
            score,
            steps=[(70, "🌤 어느 정도 기반 있음"), (50, "🌥 제한적 기반"), (30, "🔒 매우 제한적")],
            default="🍂 거의 없음",
        ),
        tone=_inverse_tone_from_score(score),
        summary=(
            "실제로 작동 가능한 조건이 어느 정도 남아 있는지를 보수적으로 본 지표입니다. "
            "재회나 성공 확률을 의미하지는 않습니다."
        ),
        source_keys=[
            "axis_scores.relationship_foundation",
            "axis_scores.partner_openness",
            "axis_scores.closure_strength",
            "axis_scores.immediate_risk",
            "safety_gate.level",
        ],
    )


def _build_emotional_stability_card(
    *,
    axis_scores: Dict[str, Any],
    confidence: Dict[str, Any],
) -> Dict[str, Any]:
    stabilization_priority = int(axis_scores.get("stabilization_priority", 0))
    immediate_risk = int(axis_scores.get("immediate_risk", 0))
    contact_pressure = int(axis_scores.get("contact_pressure", 0))
    confidence_level = str(confidence.get("level", "")).upper().strip()

    instability = (
        (stabilization_priority * 0.50)
        + (immediate_risk * 0.30)
        + (contact_pressure * 0.20)
    )

    if confidence_level == "LOW":
        instability += 5
    elif confidence_level == "HIGH":
        instability -= 3

    score = _clamp_int(100 - instability)

    return _make_card(
        card_id="emotional_stability",
        title="🧠 감정 안정도",
        score=score,
        value_text=_label_by_steps(
            score,
            steps=[(70, "🟢 비교적 안정적"), (50, "🙂 보통 수준"), (30, "🌀 흔들리는 상태")],
            default="🌊 안정도 낮음",
        ),
        tone=_inverse_tone_from_score(score),
        summary=(
            "사용자의 현재 감정 조절 여력을 보여주는 지표입니다. "
            "자기 안정성이 낮을수록 행동 속도를 늦추기 위한 기준으로 사용됩니다."
        ),
        source_keys=[
            "axis_scores.stabilization_priority",
            "axis_scores.immediate_risk",
            "axis_scores.contact_pressure",
            "confidence.level",
        ],
    )


def build_premium_metrics(result: Any) -> Dict[str, Any]:
    safety_gate = _as_dict(_get(result, "safety_gate", {}))
    axis_scores = _as_dict(_get(result, "axis_scores", {}))
    confidence = _as_dict(_get(result, "confidence", {}))
    narrative_context = _as_dict(_get(result, "narrative_context", {}))
    semantic_tags = [str(x).strip() for x in _as_list(_get(result, "semantic_tags", [])) if str(x).strip()]

    safety_level = str(safety_gate.get("level", "")).upper().strip()

    cards = [
        _build_relationship_distance_card(
            axis_scores=axis_scores,
            safety_level=safety_level,
            semantic_tags=semantic_tags,
        ),
        _build_emotional_temperature_card(
            axis_scores=axis_scores,
            safety_level=safety_level,
        ),
        _build_contact_timing_card(
            axis_scores=axis_scores,
            safety_level=safety_level,
            narrative_context=narrative_context,
        ),
        _build_risk_signal_card(
            axis_scores=axis_scores,
            safety_gate=safety_gate,
        ),
        _build_recovery_conditions_card(
            axis_scores=axis_scores,
            safety_level=safety_level,
        ),
        _build_emotional_stability_card(
            axis_scores=axis_scores,
            confidence=confidence,
        ),
    ]

    return {
        "version": "v1",
        "cards": cards,
    }
