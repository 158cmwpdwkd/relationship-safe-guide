from datetime import datetime, timedelta
import secrets


# ──────────────────────────────────────────────────────────────────────────────
# 리커넥트랩 디자인 시스템 (홈페이지 동일)
# ──────────────────────────────────────────────────────────────────────────────

RCL_CSS = """
  @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg:      #0F1626;
    --bg2:     #1A2540;
    --bg3:     #222E4A;
    --rose:    #D4916C;
    --rose-lt: #EAB89A;
    --teal:    #4ECDC4;
    --amber:   #FFB347;
    --red:     #FF6B6B;
    --txt:     #F0ECE8;
    --sub:     #9AAABB;
    --divider: rgba(212,145,108,.18);
    --r:       12px;
  }

  html { scroll-behavior: smooth; }

  body {
    background: var(--bg);
    color: var(--txt);
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 15px;
    line-height: 1.75;
    padding: 24px 16px 48px;
    -webkit-font-smoothing: antialiased;
  }

  /* ── 섹션 공통 ── */
  .section {
    margin-bottom: 24px;
    background: var(--bg2);
    border: 1px solid var(--divider);
    border-radius: var(--r);
    padding: 22px 20px;
  }
  .section-tag {
    display: inline-block;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--rose);
    border: 1px solid var(--divider);
    border-radius: 100px;
    padding: 3px 10px;
    margin-bottom: 12px;
  }
  .section-title {
    font-size: 16px;
    font-weight: 700;
    color: var(--txt);
    margin-bottom: 6px;
    line-height: 1.45;
  }
  .section-sub {
    font-size: 13px;
    color: var(--sub);
    line-height: 1.7;
  }
  .divider { width: 36px; height: 2px; background: var(--rose); border-radius: 2px; margin: 14px 0; }

  /* ── 지표 게이지 ── */
  .gauge-wrap { margin: 16px 0 8px; }
  .gauge-label {
    display: flex;
    justify-content: space-between;
    font-size: 12px;
    color: var(--sub);
    margin-bottom: 6px;
  }
  .gauge-label strong { color: var(--txt); font-size: 13px; }
  .gauge-bar {
    width: 100%; height: 8px;
    background: var(--bg3);
    border-radius: 100px;
    overflow: hidden;
  }
  .gauge-fill {
    height: 100%;
    border-radius: 100px;
    transition: width 1s ease;
  }
  .gauge-fill.rose  { background: linear-gradient(90deg, var(--rose-lt), var(--rose)); }
  .gauge-fill.teal  { background: linear-gradient(90deg, var(--teal), #3ab5ac); }
  .gauge-fill.amber { background: linear-gradient(90deg, var(--amber), #e8a030); }
  .gauge-fill.red   { background: linear-gradient(90deg, #ff9a9a, var(--red)); }

  /* ── 뱃지 ── */
  .badge {
    display: inline-flex; align-items: center; gap: 5px;
    font-size: 12px; font-weight: 700;
    padding: 4px 12px; border-radius: 100px;
  }
  .badge.danger  { background: rgba(255,107,107,.15); color: var(--red);   border: 1px solid rgba(255,107,107,.3); }
  .badge.warning { background: rgba(255,179,71,.15);  color: var(--amber); border: 1px solid rgba(255,179,71,.3); }
  .badge.safe    { background: rgba(78,205,196,.15);  color: var(--teal);  border: 1px solid rgba(78,205,196,.3); }

  /* ── 체크 리스트 ── */
  .check-list { list-style: none; display: flex; flex-direction: column; gap: 10px; margin-top: 14px; }
  .check-list li {
    display: flex; align-items: flex-start; gap: 10px;
    font-size: 13px; color: var(--txt); line-height: 1.6;
  }
  .check-list li .icon {
    flex-shrink: 0; width: 22px; height: 22px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-size: 12px; margin-top: 1px;
  }
  .check-list li .icon.do   { background: rgba(78,205,196,.2);  color: var(--teal); }
  .check-list li .icon.dont { background: rgba(255,107,107,.2); color: var(--red);  }

  /* ── 플랜 카드 (14일) ── */
  .plan-grid { display: flex; flex-direction: column; gap: 10px; margin-top: 14px; }
  .plan-card {
    background: var(--bg3);
    border: 1px solid var(--divider);
    border-radius: var(--r);
    padding: 14px 16px;
    display: flex; align-items: flex-start; gap: 12px;
  }
  .plan-card .day-badge {
    flex-shrink: 0;
    font-size: 11px; font-weight: 700;
    color: var(--rose);
    background: rgba(212,145,108,.12);
    border: 1px solid var(--divider);
    border-radius: 8px;
    padding: 4px 10px;
    text-align: center;
    white-space: nowrap;
  }
  .plan-card .plan-text { font-size: 13px; color: var(--txt); line-height: 1.6; }
  .plan-card .plan-text small { color: var(--sub); font-size: 12px; display: block; margin-top: 2px; }

  /* ── 경고 박스 ── */
  .alert-box {
    background: rgba(255,107,107,.08);
    border: 1px solid rgba(255,107,107,.25);
    border-radius: var(--r);
    padding: 16px;
    display: flex; align-items: flex-start; gap: 10px;
    margin-top: 14px;
  }
  .alert-box .alert-icon { font-size: 18px; flex-shrink: 0; margin-top: 1px; }
  .alert-box .alert-text { font-size: 13px; color: var(--txt); line-height: 1.65; }
  .alert-box .alert-text strong { color: var(--red); }

  /* ── 안전 박스 ── */
  .safe-box {
    background: rgba(78,205,196,.07);
    border: 1px solid rgba(78,205,196,.2);
    border-radius: var(--r);
    padding: 16px;
    display: flex; align-items: flex-start; gap: 10px;
    margin-top: 14px;
  }
  .safe-box .safe-icon { font-size: 18px; flex-shrink: 0; }
  .safe-box .safe-text { font-size: 13px; color: var(--txt); line-height: 1.65; }
  .safe-box .safe-text strong { color: var(--teal); }

  /* ── 비상 연락처 ── */
  .contact-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 14px; }
  .contact-card {
    background: var(--bg3);
    border: 1px solid var(--divider);
    border-radius: var(--r);
    padding: 14px;
    text-align: center;
  }
  .contact-card .c-num { font-size: 20px; font-weight: 700; color: var(--rose); margin-bottom: 4px; }
  .contact-card .c-label { font-size: 11px; color: var(--sub); line-height: 1.5; }

  /* ── 면책 푸터 ── */
  .disclaimer {
    margin-top: 28px;
    padding-top: 20px;
    border-top: 1px solid var(--divider);
    font-size: 11px;
    color: rgba(154,170,187,.55);
    line-height: 1.8;
    text-align: center;
  }

  /* ── postMessage 높이 전송 스크립트용 ── */
  html, body { height: auto !important; }
"""


def _badge_for_risk(risk_level: str) -> str:
    if risk_level == "HIGH":
        return '<span class="badge danger">⚠ 주의 필요</span>'
    elif risk_level == "MEDIUM":
        return '<span class="badge warning">◐ 중간 단계</span>'
    else:
        return '<span class="badge safe">✓ 안정적</span>'


def _gauge_color(risk_level: str) -> str:
    if risk_level == "HIGH":
        return "red"
    elif risk_level == "MEDIUM":
        return "amber"
    else:
        return "teal"


def make_report_html(risk_level: str, impulse: int, fear_type: str) -> str:
    """
    홈페이지 디자인과 통일된 완전한 HTML 리포트를 반환합니다.
    (iframe 내부에서 직접 렌더링)
    """

    # ── 긴급 차단 케이스 ──────────────────────────────────
    if risk_level == "HARD_BLOCK":
        body = f"""
        <div class="section">
          <span class="section-tag">⚠ 안전 우선</span>
          <h2 class="section-title">지금은 전문 도움이 필요할 수 있어요</h2>
          <p class="section-sub">현재 상황에서는 아래 전문기관에 먼저 연락해보시길 권장드려요.</p>
          <div class="divider"></div>
          <div class="contact-grid">
            <div class="contact-card">
              <div class="c-num">117</div>
              <div class="c-label">스토킹 피해<br>상담전화</div>
            </div>
            <div class="contact-card">
              <div class="c-num">1577-0199</div>
              <div class="c-label">정신건강<br>위기상담전화</div>
            </div>
          </div>
        </div>
        <p class="disclaimer">본 서비스는 정보 제공 목적으로만 운영됩니다.</p>
        """
        return _wrap_html(body)

    # ── 충동 지수 비율 계산 (최대 15) ────────────────────
    impulse_pct = min(round((impulse / 15) * 100), 100)
    gauge_color = _gauge_color(risk_level)
    badge_html  = _badge_for_risk(risk_level)

    # ── 두려움 유형 한국어 매핑 ───────────────────────────
    fear_map = {
        "new_partner": "새로운 사람이 생길까봐",
        "forget":      "완전히 잊혀질까봐",
        "regret":      "나중에 후회할까봐",
        "other":       "기타 / 혼합",
    }
    fear_label = fear_map.get(fear_type, fear_type)

    # ── 위험도별 행동 가이드 문구 ─────────────────────────
    guide_do = [
        ("do", "새벽·밤 충동이 올 때 — 스트레칭 3분 + 물 한 컵"),
        ("do", "앱 알림을 끄고 화면을 보지 않는 시간 만들기"),
        ("do", "오늘 느낀 감정을 짧게 노트에 적어두기"),
    ]
    guide_dont = [
        ("dont", "차단 우회 / 다른 계정·번호로 연락 시도"),
        ("dont", "상대의 집 · 직장 · 자주 가던 장소 방문"),
        ("dont", "SNS 프로필 · 스토리 의도적으로 확인"),
    ]

    # 위험도가 높을수록 금지 사항 강조
    if risk_level == "HIGH":
        alert_html = f"""
        <div class="alert-box">
          <div class="alert-icon">🚨</div>
          <div class="alert-text">
            <strong>충동 지수가 높아요.</strong><br>
            지금 연락을 시도하면 관계 회복 가능성이 낮아질 수 있어요.
            최소 <strong>72시간</strong> 동안 연락을 자제해보세요.
          </div>
        </div>"""
    elif risk_level == "MEDIUM":
        alert_html = f"""
        <div class="safe-box">
          <div class="safe-icon">💡</div>
          <div class="safe-text">
            <strong>중간 단계예요.</strong><br>
            충동이 올라오는 순간을 잘 인식하고 있어요.
            아래 행동 가이드를 참고해보세요.
          </div>
        </div>"""
    else:
        alert_html = f"""
        <div class="safe-box">
          <div class="safe-icon">✅</div>
          <div class="safe-text">
            <strong>상대적으로 안정적인 상태예요.</strong><br>
            현재 감정 조절 능력이 잘 유지되고 있어요.
            이 상태를 유지하는 것이 중요합니다.
          </div>
        </div>"""

    # ── 14일 안정화 플랜 ──────────────────────────────────
    plans = [
        ("1–3일",  "72시간 완전 차단 유지", "가장 충동이 강한 시기예요. 버티는 것 자체가 진전이에요."),
        ("4–7일",  "하루 루틴 만들기", "기상 시간 고정 · 산책 10분 · 잠들기 전 노트 쓰기"),
        ("8–12일", "감정 거리두기 연습", "상대 생각이 올라올 때 — 3초 멈추고 숨 한 번 내쉬기"),
        ("13–14일","현재 상태 재점검", "충동 지수가 낮아졌다면 프리미엄 리포트로 다음 단계 확인"),
    ]

    plan_html = "\n".join(
        f"""<div class="plan-card">
              <div class="day-badge">{d}</div>
              <div class="plan-text">{t}<small>{s}</small></div>
           </div>"""
        for d, t, s in plans
    )

    # ── 재접촉 안전 기준 ──────────────────────────────────
    if risk_level == "HIGH":
        contact_cond = "충동 지수가 6 이하로 내려간 뒤, 최소 2주 이상 지난 시점"
    elif risk_level == "MEDIUM":
        contact_cond = "충동 지수가 4 이하이고, 감정이 차분한 낮 시간대"
    else:
        contact_cond = "감정이 안정된 상태에서, 상대가 연락을 거부하지 않았을 때"

    # ── do / dont 리스트 렌더 ─────────────────────────────
    def render_items(items):
        return "\n".join(
            f'<li><span class="icon {cls}">'
            f'{"✓" if cls=="do" else "✕"}'
            f'</span>{text}</li>'
            for cls, text in items
        )

    body = f"""

    <!-- ① 현재 상태 진단 -->
    <div class="section">
      <span class="section-tag">01 · 현재 상태</span>
      <h2 class="section-title">나의 관계 진단 결과</h2>
      <p class="section-sub">입력하신 데이터를 기반으로 분석한 결과예요.</p>
      <div class="divider"></div>

      {badge_html}

      <div class="gauge-wrap">
        <div class="gauge-label">
          <span>충동 지수</span>
          <strong>{impulse} / 15</strong>
        </div>
        <div class="gauge-bar">
          <div class="gauge-fill {gauge_color}" style="width:{impulse_pct}%"></div>
        </div>
      </div>

      <div class="gauge-wrap">
        <div class="gauge-label">
          <span>주요 두려움</span>
          <strong>{fear_label}</strong>
        </div>
      </div>

      {alert_html}
    </div>

    <!-- ② 72시간 행동 가이드 -->
    <div class="section">
      <span class="section-tag">02 · 72시간 행동 가이드</span>
      <h2 class="section-title">지금 당장 해야 할 것 / 하지 말아야 할 것</h2>
      <ul class="check-list">
        {render_items(guide_do)}
      </ul>
      <ul class="check-list" style="margin-top:12px">
        {render_items(guide_dont)}
      </ul>
    </div>

    <!-- ③ 14일 안정화 플랜 -->
    <div class="section">
      <span class="section-tag">03 · 14일 안정화 플랜</span>
      <h2 class="section-title">단계별 감정 회복 로드맵</h2>
      <p class="section-sub">하루씩 따라가다 보면 달라지는 걸 느낄 수 있어요.</p>
      <div class="plan-grid">
        {plan_html}
      </div>
    </div>

    <!-- ④ 재접촉 안전 기준 -->
    <div class="section">
      <span class="section-tag">04 · 재접촉 기준</span>
      <h2 class="section-title">언제 연락해도 괜찮을까요?</h2>
      <div class="safe-box" style="margin-top:0">
        <div class="safe-icon">📋</div>
        <div class="safe-text">
          <strong>추천 재접촉 조건:</strong><br>
          {contact_cond}
        </div>
      </div>
      <p class="section-sub" style="margin-top:12px">
        ※ 구체적인 연락 방법 · 타이밍 · 첫 메시지 전략은 프리미엄 리포트에서 확인하세요.
      </p>
    </div>

    <!-- ⑤ 도움 받을 곳 -->
    <div class="section">
      <span class="section-tag">05 · 도움 받을 곳</span>
      <h2 class="section-title">혼자 버티기 힘들 때</h2>
      <div class="contact-grid">
        <div class="contact-card">
          <div class="c-num">117</div>
          <div class="c-label">스토킹 피해<br>상담전화</div>
        </div>
        <div class="contact-card">
          <div class="c-num">1577-0199</div>
          <div class="c-label">정신건강<br>위기상담전화</div>
        </div>
      </div>
    </div>

    <p class="disclaimer">
      본 리포트는 자체 분석 모델 기반의 참고 추정치이며, 법적 효력을 갖는 통계가 아닙니다.<br>
      개인별 상황에 따라 결과가 다를 수 있으며, 본 서비스는 연애 상담이 아닌 정보 제공 서비스입니다.
    </p>
    """

    return _wrap_html(body)


def _wrap_html(body: str) -> str:
    """body 내용을 완전한 HTML 페이지로 감싸고 postMessage로 높이를 전송합니다."""
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width,initial-scale=1.0"/>
  <title>관계 진단 리포트 | 리커넥트랩</title>
  <style>{RCL_CSS}</style>
</head>
<body>
{body}

<script>
  // 부모 창으로 콘텐츠 높이 전송 (iframe 자동 리사이즈용)
  function sendHeight() {{
    const h = document.documentElement.scrollHeight;
    window.parent.postMessage({{ type: 'RCL_REPORT_HEIGHT', height: h }}, '*');
  }}
  // 로드 후 + 폰트 렌더링 후 두 번 전송
  window.addEventListener('load', () => {{
    sendHeight();
    setTimeout(sendHeight, 600);
  }});
</script>
</body>
</html>"""


# ──────────────────────────────────────────────────────────────────────────────
# 기존 함수 유지 (호환성)
# ──────────────────────────────────────────────────────────────────────────────

def make_report_markdown(risk_level: str, impulse: int, fear_type: str) -> str:
    """기존 마크다운 버전 (레거시 호환용)"""
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
- 새벽/밤 충동이면 스트레칭 3분 + 물 한 컵
- 알림/앱 유혹 차단
❌ 금지
- 차단 우회/다른 계정으로 접촉 시도
- 집/직장 주변 방문
"""


def new_token() -> str:
    return secrets.token_urlsafe(32)


def expiry_6_months() -> datetime:
    return datetime.utcnow() + timedelta(days=180)
