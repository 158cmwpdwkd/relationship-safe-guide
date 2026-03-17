from app.services.interpretation.narrative import build_narrative_context
from app.services.interpretation.schemas import (
    AxisScores,
    Confidence,
    ContradictionItem,
    SafetyGate,
)


def test_narrative_hard_block_case():
    axis = AxisScores(
        immediate_risk=82,
        emotional_fusion=84,
        relationship_foundation=40,
        closure_strength=91,
        partner_openness=0,
        contact_pressure=88,
        stabilization_priority=86,
    )

    safety = SafetyGate(
        level="HARD_BLOCK",
        reasons=["상대의 명확한 경계 이후 우회 접촉 신호가 있습니다."],
        hard_constraints=[
            "직접 재접촉 문장 생성 금지",
            "우회 연락 제안 금지",
        ],
    )

    confidence = Confidence(
        score=41,
        level="LOW",
        supporting_signals=["채널 상태 신호가 분명합니다."],
        weakening_factors=["모순 신호가 존재합니다."],
        contradictions_found=["pressure_boundary_conflict"],
    )

    contradictions = [
        ContradictionItem(
            code="pressure_boundary_conflict",
            message="압박과 경계 충돌",
            severity="HIGH",
        )
    ]

    result = build_narrative_context(
        axis_scores=axis,
        safety_gate=safety,
        confidence=confidence,
        contradictions=contradictions,
        semantic_tags=["all_channels_blocked", "contact_ignored"],
        primary_labels=["강한 행동 제한 필요"],
        secondary_labels=["전채널 차단 상태"],
    )

    assert result["contact_guidance_mode"] == "NO_CONTACT_STRATEGY"
    assert "재회 가능성·성공률·확률 표현을 사용하지 않는다." in result["do_not_do"]
    assert result["safety_level"] == "HARD_BLOCK"


def test_narrative_partial_open_case():
    axis = AxisScores(
        immediate_risk=35,
        emotional_fusion=52,
        relationship_foundation=68,
        closure_strength=48,
        partner_openness=56,
        contact_pressure=30,
        stabilization_priority=45,
    )

    safety = SafetyGate(
        level="LOW",
        reasons=["강한 위험 행동 신호는 두드러지지 않습니다."],
        hard_constraints=["상대 심리 단정 금지"],
    )

    confidence = Confidence(
        score=83,
        level="HIGH",
        supporting_signals=["부분 개방 신호가 있습니다."],
        weakening_factors=[],
        contradictions_found=[],
    )

    result = build_narrative_context(
        axis_scores=axis,
        safety_gate=safety,
        confidence=confidence,
        contradictions=[],
        semantic_tags=["small_response_signal"],
        primary_labels=["부분 개방 신호 존재"],
        secondary_labels=["최근 상호작용 단서 존재"],
    )

    assert result["contact_guidance_mode"] in ("STABILIZE_FIRST", "CAUTIOUS_DELAY")
    assert len(result["focus_points"]) >= 1
    assert result["confidence_level"] == "HIGH"


def test_narrative_low_confidence_adds_caution():
    axis = AxisScores(
        immediate_risk=45,
        emotional_fusion=60,
        relationship_foundation=35,
        closure_strength=55,
        partner_openness=28,
        contact_pressure=32,
        stabilization_priority=52,
    )

    safety = SafetyGate(
        level="ELEVATED",
        reasons=["정서적 흔들림이 있습니다."],
        hard_constraints=["즉시 재접촉 유도 문장 생성 금지"],
    )

    confidence = Confidence(
        score=49,
        level="LOW",
        supporting_signals=[],
        weakening_factors=["혼합 신호가 있습니다."],
        contradictions_found=["signal_openness_conflict"],
    )

    contradictions = [
        ContradictionItem(
            code="signal_openness_conflict",
            message="신호 충돌",
            severity="MEDIUM",
        )
    ]

    result = build_narrative_context(
        axis_scores=axis,
        safety_gate=safety,
        confidence=confidence,
        contradictions=contradictions,
        semantic_tags=["mixed_signal_repeated"],
    )

    assert "모호한 신호를 확정적 의미로 번역하지 않는다." in result["do_not_do"]
    assert any("조건부 표현" in x for x in result["tone_hints"] + result["model_notes"])