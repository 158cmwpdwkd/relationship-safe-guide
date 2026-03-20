from pathlib import Path

from app.services.reporting.premium_renderer import render_premium_report_html

markdown_text = """
# 테스트 리포트

## 1. 현재 상태 정밀 진단
테스트용 본문입니다.

## 2. 72시간 행동 가이드
테스트용 본문입니다.
"""

metrics_green = {
    "version": "v1",
    "cards": [
        {"id": "relationship_distance", "label": "📏 관계 거리감", "display": "🤝 낮음", "state": "🤝 낮음", "score": 18, "tone": "stable", "summary": "현재 관계가 비교적 덜 멀어진 상태로 보입니다."},
        {"id": "emotional_temperature", "label": "🌡 감정 온도", "display": "🌿 차분함", "state": "🌿 차분함", "score": 22, "tone": "stable", "summary": "현재 감정 강도와 흔들림이 비교적 낮은 편입니다."},
        {"id": "contact_timing", "label": "⏳ 연락 타이밍", "display": "🟢 신중 검토 가능", "state": "🟢 신중 검토 가능", "score": 25, "tone": "stable", "summary": "과도한 지연이 꼭 필요한 상태는 아닙니다."},
        {"id": "current_risk_signal", "label": "🚨 현재 위험 신호", "display": "🟢 낮음", "state": "🟢 낮음", "score": 15, "tone": "stable", "summary": "현재 위험 패턴은 비교적 낮은 수준입니다."},
        {"id": "recovery_conditions", "label": "관계 회복 여건 지수", "display": "🌤 일부 여건 있음", "state": "🌤 일부 여건 있음", "score": 78, "tone": "stable", "summary": "관계 회복을 검토할 수 있는 여건이 일부 남아 있습니다."},
        {"id": "emotional_stability", "label": "현재 감정 안정도", "display": "🟢 안정적", "state": "🟢 안정적", "score": 81, "tone": "stable", "summary": "현재 감정 조절 여력이 비교적 안정적입니다."},
    ],
}

metrics_yellow = {
    "version": "v1",
    "cards": [
        {"id": "relationship_distance", "label": "📏 관계 거리감", "display": "📍 벌어짐", "state": "📍 벌어짐", "score": 58, "tone": "caution", "summary": "현재 관계가 다소 멀어진 상태로 보입니다."},
        {"id": "emotional_temperature", "label": "🌡 감정 온도", "display": "💫 불안정함", "state": "💫 불안정함", "score": 47, "tone": "caution", "summary": "현재 감정 강도와 흔들림이 주의가 필요한 수준입니다."},
        {"id": "contact_timing", "label": "⏳ 연락 타이밍", "display": "⏸ 기다리며 재평가", "state": "⏸ 기다리며 재평가", "score": 43, "tone": "caution", "summary": "어느 정도의 시간 간격과 자제가 필요한 상태입니다."},
        {"id": "current_risk_signal", "label": "🚨 현재 위험 신호", "display": "🟡 주의 필요", "state": "🟡 주의 필요", "score": 58, "tone": "caution", "summary": "현재 위험 패턴을 안전 우선 관점에서 해석한 결과입니다."},
        {"id": "recovery_conditions", "label": "관계 회복 여건 지수", "display": "🔒 매우 제한적", "state": "🔒 매우 제한적", "score": 42, "tone": "caution", "summary": "작동 가능한 조건이 어느 정도 남아 있는지를 보수적으로 본 지표입니다."},
        {"id": "emotional_stability", "label": "현재 감정 안정도", "display": "🌀 흔들리는 상태", "state": "🌀 흔들리는 상태", "score": 49, "tone": "caution", "summary": "사용자의 현재 감정 조절 여력을 보여주는 지표입니다."},
    ],
}

metrics_red = {
    "version": "v1",
    "cards": [
        {"id": "relationship_distance", "label": "📏 관계 거리감", "display": "🚫 매우 멀어짐", "state": "🚫 매우 멀어짐", "score": 91, "tone": "danger", "summary": "현재 관계가 매우 멀어진 상태로 보입니다."},
        {"id": "emotional_temperature", "label": "🌡 감정 온도", "display": "🚨 과열", "state": "🚨 과열", "score": 88, "tone": "danger", "summary": "현재 감정 강도와 흔들림이 매우 높은 상태입니다."},
        {"id": "contact_timing", "label": "⏳ 연락 타이밍", "display": "⛔ 접근 비권장", "state": "⛔ 접근 비권장", "score": 89, "tone": "danger", "summary": "지금은 접근 시도보다 충분한 지연과 자제가 필요합니다."},
        {"id": "current_risk_signal", "label": "🚨 현재 위험 신호", "display": "🔴 높음", "state": "🔴 높음", "score": 93, "tone": "danger", "summary": "현재 위험 패턴이 높게 감지되는 상태입니다."},
        {"id": "recovery_conditions", "label": "관계 회복 여건 지수", "display": "🔒 거의 없음", "state": "🔒 거의 없음", "score": 12, "tone": "danger", "summary": "현재는 회복을 검토할 수 있는 여건이 매우 부족합니다."},
        {"id": "emotional_stability", "label": "현재 감정 안정도", "display": "🌀 매우 불안정", "state": "🌀 매우 불안정", "score": 18, "tone": "danger", "summary": "현재 감정 조절 여력이 크게 흔들리는 상태입니다."},
    ],
}

for name, metrics in {
    "green": metrics_green,
    "yellow": metrics_yellow,
    "red": metrics_red,
}.items():
    html = render_premium_report_html(markdown_text, metrics=metrics)
    Path(f"output_preview_{name}.html").write_text(html, encoding="utf-8")
    print(f"saved: output_preview_{name}.html")