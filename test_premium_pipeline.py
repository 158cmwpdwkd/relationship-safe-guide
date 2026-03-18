# test_premium_pipeline.py

from app.services.reporting.premium_pipeline import prepare_premium_report_payload


def test_prepare_premium_report_payload(monkeypatch):
    sample_result = {
        "safety_gate": {
            "level": "ELEVATED",
            "reasons": ["감정 기복이 큼"],
            "hard_constraints": ["우회접촉 금지"],
        },
        "axis_scores": {
            "closure_strength": 55,
            "partner_openness": 22,
        },
        "semantic_tags": ["rumination_high"],
        "primary_labels": ["감정 과부하"],
        "secondary_labels": ["접촉 충동 주의"],
        "report_constraints": ["확률 언급 금지"],
        "confidence": {"score": 0.81, "band": "HIGH"},
        "narrative_context": {
            "situation_summary": "관계는 정리 국면에 가깝다.",
            "state_summary": "사용자는 감정 정리가 아직 덜 된 상태다.",
            "risk_summary": "즉시 행동 시 후회 가능성이 있다.",
            "contact_guidance_mode": "STABILIZE_FIRST",
            "focus_points": ["수면 회복", "충동 지연"],
            "do_not_do": ["새벽 연락", "SNS 확인"],
            "tone_hints": ["차분하게", "단정 없이"],
            "model_notes": ["상대 심리 단정 금지"],
        },
    }

    def fake_run_interpretation_engine(engine_input):
        return sample_result

    monkeypatch.setattr(
        "app.services.reporting.premium_pipeline.run_interpretation_engine",
        fake_run_interpretation_engine,
    )

    payload = prepare_premium_report_payload(engine_input={"dummy": "input"})

    assert payload["meta"]["report_type"] == "premium"
    assert payload["meta"]["prompt_version"] == "v1"
    assert isinstance(payload["prompt"], str)
    assert "1. 현재 상태 정밀 진단" in payload["prompt"]
    assert "2. 72시간 행동 가이드" in payload["prompt"]
    assert payload["interpretation_result"]["safety_gate"]["level"] == "ELEVATED"