from datetime import datetime, timedelta
import secrets
import markdown as md

def make_report_markdown(risk_level: str, impulse: int, fear_type: str) -> str:
    if risk_level == "HARD_BLOCK":
        return (
            "## ⚠️ 안전 우선 안내\n\n"
            "현재 상황에서는 전문기관 상담이 우선 필요할 수 있어요.\n\n"
            "- 스토킹 피해 상담: 117\n"
            "- 정신건강 위기상담: 1577-0199\n"
        )

    return f"""# 관계 안전 가이드 (MVP)

## 1. 현재 상태 정밀 진단
- 충동 지수: **{impulse}/15**
- 위험도: **{risk_level}**
- 지금 가장 큰 두려움: **{fear_type}**

## 2. 72시간 긴급 행동 가이드
✅ 해야 할 일
- 새벽/밤 충동이면 **실내에서** 스트레칭 3분 + 물 한 컵
- 알림/앱 유혹 차단(앱 알림 끄기)

❌ 금지
- 차단 우회/다른 계정으로 접촉 시도
- 집/직장 주변 방문

## 3. 위험 행동 3가지
(설문 기반으로 이후 개인화)

## 4. 14일 안정화 플랜
(이후 확장)

## 5. 재접촉 관련 안전 기준
(조건 분기)

## 6. 도움 받을 곳
-📞 117 / 1577-0199

---
⚠️ 중요 안내: 본 리포트는 참고자료이며 결과를 보장하지 않습니다.
"""

def markdown_to_html(markdown_text: str) -> str:
    return md.markdown(markdown_text, extensions=["extra"])

def new_token() -> str:
    return secrets.token_urlsafe(32)

def expiry_6_months() -> datetime:
    return datetime.utcnow() + timedelta(days=180)