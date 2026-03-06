from datetime import datetime, timedelta
import secrets


# ──────────────────────────────────────────────────────────────────────────────
# 랜딩페이지와 동일한 디자인 시스템 (정리본 / 복붙용)
# - padding 중복/충돌 제거
# - 모바일/터치/iframe 패딩 "한 군데"에서만 최종 결정
# - 연락처 숫자/그리드 깨짐 방지 유지
# ──────────────────────────────────────────────────────────────────────────────

RCL_CSS = """
  /* ──────────────────────────
     RESET / TOKENS
     ────────────────────────── */
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
    --r:       14px;

    /* ✅ 패딩 토큰(여기만 만지면 전체 조절됨) */
    --body-px: 20px;
    --body-pt: 28px;
    --body-pb: 60px;

    --sec-px:  20px;
    --sec-py:  22px;
  }

  html { scroll-behavior: smooth; }

  body {
    background: var(--bg);
    color: var(--txt);
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 17px;
    line-height: 1.75;
    padding: var(--body-pt) var(--body-px) var(--body-pb);
    -webkit-font-smoothing: antialiased;
  }

  /* ──────────────────────────
     SECTION (카드)
     ────────────────────────── */
  .section {
    background: var(--bg2);
    border: 1px solid var(--divider);
    border-radius: var(--r);
    padding: var(--sec-py) var(--sec-px);
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
  }

  /* 좌측 컬러 포인트 바 */
  .section.s-rose::before,
  .section.s-teal::before,
  .section.s-amber::before,
  .section.s-red::before{
    content:'';
    position:absolute; top:0; left:0;
    width:4px; height:100%;
  }
  .section.s-rose::before  { background: var(--rose); }
  .section.s-teal::before  { background: var(--teal); }
  .section.s-amber::before { background: var(--amber); }
  .section.s-red::before   { background: var(--red); }

  /* ──────────────────────────
     TYPO / TAG / TITLE
     ────────────────────────── */
  .tag {
    display: inline-block;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--rose);
    border: 1px solid rgba(212,145,108,.25);
    border-radius: 100px;
    padding: 4px 14px;
    margin-bottom: 14px;
  }

  .sec-title {
    font-size: clamp(18px, 4vw, 22px);
    font-weight: 700;
    line-height: 1.4;
    color: var(--txt);
    margin-bottom: 6px;
    word-break: keep-all;
  }
  .sec-sub {
    font-size: 15px;
    color: var(--sub);
    line-height: 1.7;
    margin-bottom: 16px;
    word-break: keep-all;
  }

  /* ──────────────────────────
     BADGE
     ────────────────────────── */
  .badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 700;
    padding: 5px 14px;
    border-radius: 100px;
    margin-bottom: 16px;
  }
  .badge.danger  { background: rgba(255,107,107,.15); color: var(--red);   border: 1px solid rgba(255,107,107,.3); }
  .badge.warning { background: rgba(255,179,71,.15);  color: var(--amber); border: 1px solid rgba(255,179,71,.3); }
  .badge.safe    { background: rgba(78,205,196,.15);  color: var(--teal);  border: 1px solid rgba(78,205,196,.3); }

  /* ──────────────────────────
     METRICS
     ────────────────────────── */
  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(110px, 1fr));
    gap: 10px;
    margin-bottom: 16px;
  }
  .metric-box {
    background: var(--bg3);
    border: 1px solid rgba(212,145,108,.15);
    border-radius: 10px;
    padding: 14px 12px;
    text-align: center;
    min-width: 0;
    overflow: hidden;
  }
  .m-label { font-size: 13px; color: var(--sub); margin-bottom: 6px; letter-spacing: .04em; }
  .m-val   { font-size: clamp(16px, 4vw, 20px); font-weight: 700; color: var(--rose-lt); }
  .m-val.t { color: var(--teal); }
  .m-val.a { color: var(--amber); }
  .m-val.r { color: var(--red); }

  /* ──────────────────────────
     BARS
     ────────────────────────── */
  .bar-sec { margin-bottom: 14px; }
  .bar-lbl {
    font-size: 15px;
    color: var(--sub);
    margin-bottom: 8px;
    display: flex;
    justify-content: space-between;
  }
  .bar-lbl strong { color: var(--txt); }

  .bar-track {
    width: 100%;
    height: 8px;
    background: var(--bg3);
    border-radius: 100px;
    overflow: hidden;
  }
  .bar-fill       { height:100%; border-radius:100px; background:linear-gradient(90deg, var(--rose-lt), var(--rose)); }
  .bar-fill-teal  { height:100%; border-radius:100px; background:linear-gradient(90deg, var(--teal), #3ab5ac); }
  .bar-fill-amber { height:100%; border-radius:100px; background:linear-gradient(90deg, var(--amber), #e8a030); }
  .bar-fill-red   { height:100%; border-radius:100px; background:linear-gradient(90deg, #ff9a9a, var(--red)); }

  /* ──────────────────────────
     CHECK LIST
     ────────────────────────── */
  .check-list { display: flex; flex-direction: column; gap: 10px; }

  .check-item {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    background: var(--bg3);
    border: 1px solid var(--divider);
    border-radius: var(--r);
    padding: 14px 16px;
  }

  .check-dot {
    width: 24px; height: 24px; min-width: 24px;
    border-radius: 50%;
    position: relative;
    flex-shrink: 0;
  }
  .check-dot.do   { border: 2px solid var(--teal); }
  .check-dot.dont { border: 2px solid var(--red); }

  .check-dot.do::after,
  .check-dot.dont::after{
    position:absolute; top:50%; left:50%;
    transform: translate(-50%,-50%);
    font-size: 12px;
    font-weight: 700;
  }
  .check-dot.do::after   { content:'✓'; color: var(--teal); }
  .check-dot.dont::after { content:'✕'; color: var(--red); }

  .check-txt { font-size: 15px; line-height: 1.6; color: var(--txt); word-break: keep-all; }
  .check-sub { display: block; font-size: 13px; color: var(--sub); margin-top: 2px; }

  /* ──────────────────────────
     STEPS
     ────────────────────────── */
  .steps { display: flex; flex-direction: column; }

  .step {
    display: flex;
    gap: 16px;
    align-items: flex-start;
    padding: 16px 0;
    border-bottom: 1px solid rgba(212,145,108,.15);
  }
  .step:last-child { border-bottom: none; padding-bottom: 0; }

  .step-num {
    width: 38px; height: 38px; min-width: 38px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--rose), #BE7D5A);
    color: #fff;
    font-size: 16px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 14px rgba(212,145,108,.35);
    flex-shrink: 0;
  }

  .step-title { font-size: 16px; font-weight: 700; color: var(--txt); margin-bottom: 4px; }
  .step-title .day {
    font-size: 13px;
    font-weight: 700;
    color: var(--rose);
    background: rgba(212,145,108,.12);
    border: 1px solid var(--divider);
    border-radius: 6px;
    padding: 2px 8px;
    margin-right: 8px;
  }
  .step-desc { font-size: 15px; color: var(--sub); line-height: 1.65; word-break: keep-all; }

  /* ──────────────────────────
     ALERT BOX
     ────────────────────────── */
  .alert-box {
    padding: 16px 18px;
    border-radius: 0 var(--r) var(--r) 0;
    display: flex;
    align-items: flex-start;
    gap: 12px;
    margin-top: 14px;
  }
  .alert-box.danger { background: rgba(255,107,107,.08); border-left: 3px solid var(--red); }
  .alert-box.warn   { background: rgba(255,179,71,.08);  border-left: 3px solid var(--amber); }
  .alert-box.safe   { background: rgba(78,205,196,.08);  border-left: 3px solid var(--teal); }

  .alert-icon { font-size: 22px; flex-shrink: 0; margin-top: 1px; }
  .alert-text { font-size: 15px; color: var(--txt); line-height: 1.65; word-break: keep-all; }
  .alert-text strong.r { color: var(--red); }
  .alert-text strong.t { color: var(--teal); }
  .alert-text strong.a { color: var(--amber); }

  /* ──────────────────────────
     CONTACT GRID
     ────────────────────────── */
  .contact-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 10px;
    margin-top: 14px;
  }

  .contact-card {
    background: var(--bg3);
    border: 1px solid var(--divider);
    border-radius: var(--r);
    padding: 16px 12px;
    text-align: center;
    overflow: hidden;  /* 튀어나옴 방지 */
    min-width: 0;
  }

  .c-num {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-size: clamp(18px, 5.2vw, 24px);
    font-weight: 700;
    color: var(--rose);
    margin-bottom: 6px;
    min-width: 0;
  }

  .c-phone{
    white-space: nowrap;           /* 숫자 한 줄 고정 */
    min-width: 0;
    max-width: 100%;
    line-height: 1.1;
    letter-spacing: -0.03em;
    font-variant-numeric: tabular-nums;
    word-break: keep-all;
    overflow-wrap: normal;
  }

  .c-label {
    font-size: 13px;
    color: var(--sub);
    line-height: 1.5;
    word-break: keep-all;
  }

  /* ──────────────────────────
     DISCLAIMER
     ────────────────────────── */
  .disclaimer {
    margin-top: 24px;
    padding: 16px 18px;
    background: var(--bg2);
    border: 1px solid var(--divider);
    border-radius: var(--r);
    font-size: 13px;
    color: rgba(154,170,187,.6);
    line-height: 1.8;
    text-align: center;
    word-break: keep-all;
  }

  /* ──────────────────────────
     MOBILE / TOUCH (최종값)
     ────────────────────────── */

  /* 모바일(768 이하): 답답함 방지용 기본 패딩 상향 */
  @media (max-width: 768px){
    :root{
      --body-px: 18px;
      --body-pt: 22px;
      --body-pb: 56px;

      --sec-px:  18px;
      --sec-py:  22px;
    }

    body       { font-size: 16px; }
    .tag       { font-size: 11px; }
    .badge     { font-size: 12px; }
    .m-label   { font-size: 11px; }
    .sec-title { font-size: 17px; }
    .sec-sub   { font-size: 13px; }
    .check-txt { font-size: 13px; }
    .check-sub { font-size: 12px; }
    .step-num  { width: 32px; height: 32px; min-width: 32px; font-size: 13px; }
    .step-title{ font-size: 14px; }
    .step-desc { font-size: 13px; }
    .alert-text{ font-size: 14px; }
    .disclaimer{ font-size: 12px; padding: 14px 12px; }
  }

  /* 터치기기: 가독성/여백 조금 더(필요하면 여기만 조절) */
  @media (hover: none) and (pointer: coarse){
    :root{
      --body-px: 20px;
      --body-pt: 26px;
      --sec-px:  20px;
      --sec-py:  24px;
      --sub: rgba(240,236,232,0.78);
    }

    body{ line-height: 1.9; }
    .sec-title{ font-size: 19px; line-height: 1.35; }
    .sec-sub, .step-desc, .alert-text, .check-txt{ font-size: 15px; line-height: 1.85; }

    /* 터치 환경에서 연락처는 1열이 더 안정적 */
    .contact-grid{ grid-template-columns: 1fr; }
  }

  /* 아주 좁은 폰 */
  @media (max-width: 360px){
    :root{ --body-px: 16px; --sec-px: 16px; }
    .c-phone{ font-size: clamp(17px, 5.8vw, 22px); }
  }

  /* ✅ iframe 내 모바일: 좌우 패딩만 안전하게 조정(답답함 방지: 18px) */
  @media (max-width: 768px){
    html.in-iframe body{
      padding-left: 18px !important;
      padding-right: 18px !important;
    }
    html.in-iframe .section{
      padding-left: 18px !important;
      padding-right: 18px !important;
    }
  }
"""


def _badge_for_risk(risk_level: str) -> str:
    if risk_level == "HARD_BLOCK":
        return '<span class="badge danger">🚫 접촉 중단 · 안전 우선</span>'
    if risk_level in ("HIGH", "SOFT_GATE"):
        return '<span class="badge danger">⚠ 주의 필요 · 접촉 제한</span>'
    elif risk_level == "MEDIUM":
        return '<span class="badge warning">◐ 중간 단계 · 관리 필요</span>'
    else:
        return '<span class="badge safe">✓ 안정적 · 감정 조절 양호</span>'


def _gauge_class(risk_level: str) -> str:
    if risk_level in(("HIGH", "SOFT_GATE")): return "bar-fill-red"
    elif risk_level == "MEDIUM": return "bar-fill-amber"
    else:                        return "bar-fill-teal"


def _m_val_class(risk_level: str) -> str:
    if risk_level in ("HIGH", "SOFT_GATE"): return "r"
    elif risk_level == "MEDIUM": return "a"
    else:                        return "t"


def make_report_html(risk_level: str, impulse: int, fear_type: str) -> str:
    """랜딩페이지 디자인과 통일된 완전한 HTML 리포트"""

    # ── 긴급 차단 ──────────────────────────────────────────
    if risk_level == "HARD_BLOCK":
        body = """
    <div class="section s-red">
      <span class="tag">⚠ 안전 우선</span>
      <h2 class="sec-title">지금은 전문 도움이 먼저예요</h2>
      <p class="sec-sub">현재 상황에서는 아래 전문기관에 먼저 연락해보시길 권장드려요.</p>
      <div class="contact-grid">
        <div class="contact-card">
          <div class="c-num">📞 117</div>
          <div class="c-label">스토킹 피해<br>상담전화</div>
        </div>
        <div class="contact-card">
          <div class="c-num">📞 1577-0199</div>
          <div class="c-label">정신건강<br>위기상담전화</div>
        </div>
      </div>
    </div>
    <p class="disclaimer">본 서비스는 정보 제공 목적으로만 운영됩니다.</p>
    """
        return _wrap_html(body, risk_level)

    # ── 수치 계산 ───────────────────────────────────────────
    impulse_pct  = min(round((impulse / 15) * 100), 100)
    stable_pct   = max(100 - impulse_pct, 10)
    gauge_cls    = _gauge_class(risk_level)
    badge_html   = _badge_for_risk(risk_level)
    mv_cls       = _m_val_class(risk_level)

    fear_map = {
        "fear_end_forever": "영원히 끝날까봐",
        "fear_breakdown": "내가 무너질까봐",
        "fear_legal_issue": "법적 문제가 생길까봐",
        "fear_be_hated": "미움받을까봐",
    }
    fear_label = fear_map.get(fear_type, "기타")
    risk_label = {
        "SOFT_GATE":"접촉 제한", "HIGH": "주의", "MEDIUM": "보통", "LOW": "안정"}.get(risk_level, risk_level)

    # ── 위험도별 알림 박스 ───────────────────────────────────
    if risk_level == "SOFT_GATE":
        alert_html = """
      <div class="alert-box danger">
       <div class="alert-icon">🚫</div>
       <div class="alert-text">
        <strong class="r">접촉 관련 조언을 제한합니다.</strong><br>
        상대가 불편함을 느끼거나 거부 의사를 보인 상태일 수 있어요.
        지금은 <strong class="r">연락/접근 시도</strong>보다
        <strong class="r">위험 행동 차단</strong>에만 집중해 주세요.
     </div>
    </div>"""
    
    elif risk_level == "HIGH":
        alert_html = """
    <div class="alert-box danger">
      <div class="alert-icon">🚨</div>
      <div class="alert-text">
        <strong class="r">충동 지수가 높아요.</strong><br>
        지금 연락을 시도하면 관계 회복 가능성이 낮아질 수 있어요.
        최소 <strong class="r">72시간</strong> 동안 연락을 자제해보세요.
      </div>
    </div>"""
    elif risk_level == "MEDIUM":
        alert_html = """
    <div class="alert-box warn">
      <div class="alert-icon">💡</div>
      <div class="alert-text">
        <strong class="a">중간 단계예요.</strong><br>
        충동이 올라오는 순간을 인식하고 있어요.
        아래 행동 가이드를 참고해보세요.
      </div>
    </div>"""
    else:
        alert_html = """
    <div class="alert-box safe">
      <div class="alert-icon">✅</div>
      <div class="alert-text">
        <strong class="t">상대적으로 안정적인 상태예요.</strong><br>
        현재 감정 조절이 잘 유지되고 있어요.
        이 상태를 유지하는 것이 중요합니다.
      </div>
    </div>"""

    # ── 행동 가이드 ───────────────────────────────────────────
    guide_do = [
        ("새벽·밤 충동이 올 때", "스트레칭 3분 + 물 한 컵"),
        ("알림 끄고 화면 보지 않는 시간 확보", "하루 2시간 이상 권장"),
        ("오늘 느낀 감정을 짧게 기록", "노트앱 또는 메모장 활용"),
    ]
    guide_dont = [
        ("차단 우회 / 다른 계정·번호로 연락", "상대에게 압박감으로 작용해요"),
        ("상대의 집·직장·자주 가던 장소 방문", "법적 문제로 이어질 수 있어요"),
        ("SNS 프로필·스토리 의도적으로 확인", "충동을 더 키울 수 있어요"),
    ]

    def render_checks(items, dot_cls):
        return "\n".join(
            f'<div class="check-item">'
            f'<div class="check-dot {dot_cls}"></div>'
            f'<div class="check-txt">{title}<span class="check-sub">{sub}</span></div>'
            f'</div>'
            for title, sub in items
        )

    # ── 14일 플랜 ────────────────────────────────────────────
    plans = [
        ("1–3일",   "72시간 완전 차단 유지",  "가장 충동이 강한 시기예요. 버티는 것 자체가 진전이에요."),
        ("4–7일",   "하루 루틴 만들기",        "기상 시간 고정 · 산책 10분 · 잠들기 전 노트 쓰기"),
        ("8–12일",  "감정 거리두기 연습",      "상대 생각이 올라올 때 — 3초 멈추고 숨 한 번 내쉬기"),
        ("13–14일", "현재 상태 재점검",        "충동 지수가 낮아졌다면 프리미엄 리포트로 다음 단계 확인"),
    ]
    plan_html = "\n".join(
        f"""<div class="step">
          <div class="step-num">{i+1}</div>
          <div class="step-content">
            <div class="step-title"><span class="day">{d}</span>{t}</div>
            <div class="step-desc">{s}</div>
          </div>
        </div>"""
        for i, (d, t, s) in enumerate(plans)
    )

    # ── 재접촉 조건 ──────────────────────────────────────────
    if risk_level == "SOFT_GATE":
       contact_section_html = """
    <div class="section s-red">
      <span class="tag">04 · 재접촉 기준</span>
      <h2 class="sec-title">현재는 접촉 관련 안내를 제공하지 않아요</h2>
      <div class="alert-box danger" style="margin-top:0">
        <div class="alert-icon">🚫</div>
        <div class="alert-text">
          상대의 거부/불편 신호가 있는 상황에서는 접촉 가이드를 제공하면
          오히려 법적·안전 리스크를 키울 수 있어요.<br>
          지금은 <strong class="r">연락 시도</strong>를 멈추고,
          <strong class="r">충동 차단 루틴</strong>에 집중해 주세요.
        </div>
      </div>
    </div>
    """
    else:
      if risk_level == "HIGH":
          contact_cond    = "충동 지수 6 이하 + 최소 2주 이상 지난 시점"
          contact_box_cls = "danger"
          contact_icon    = "🚫"
      elif risk_level == "MEDIUM":
          contact_cond    = "충동 지수 4 이하 + 감정이 차분한 낮 시간대"
          contact_box_cls = "warn"
          contact_icon    = "⏳"
      else:
          contact_cond    = "감정이 안정된 상태 + 상대가 연락을 거부하지 않았을 때"
          contact_box_cls = "safe"
          contact_icon    = "📋"

      contact_section_html = f"""
<div class="section s-rose">
  <span class="tag">04 · 재접촉 기준</span>
  <h2 class="sec-title">언제 연락해도 괜찮을까요?</h2>
  <div class="alert-box {contact_box_cls}" style="margin-top:0">
    <div class="alert-icon">{contact_icon}</div>
    <div class="alert-text">
      <strong>추천 재접촉 조건:</strong><br>
      {contact_cond}
    </div>
  </div>
  <p class="sec-sub" style="margin-top:12px;margin-bottom:0">
    ※ 구체적인 연락 방법 · 타이밍 · 첫 메시지 전략은 프리미엄 리포트에서 확인하세요.
  </p>
</div>
"""

    body = f"""

    <!-- ① 현재 상태 진단 -->
    <div class="section s-rose">
      <span class="tag">01 · 현재 상태</span>
      <h2 class="sec-title">나의 관계 진단 결과</h2>
      <p class="sec-sub">입력하신 데이터를 기반으로 분석한 결과예요.</p>

      {badge_html}

      <div class="metrics-grid">
        <div class="metric-box">
          <div class="m-label">충동 지수</div>
          <div class="m-val {mv_cls}">{impulse}<span style="font-size:14px;font-weight:400;color:var(--sub)"> / 15</span></div>
        </div>
        <div class="metric-box">
          <div class="m-label">위험 단계</div>
          <div class="m-val {mv_cls}">{risk_label}</div>
        </div>
        <div class="metric-box">
          <div class="m-label">주요 두려움</div>
          <div class="m-val" style="font-size:18px;color:var(--rose-lt)">{fear_label}</div>
        </div>
        <div class="metric-box">
          <div class="m-label">감정 안정도</div>
          <div class="m-val t">{stable_pct}%</div>
        </div>
      </div>

      <div class="bar-sec">
        <div class="bar-lbl">충동 지수 <strong>{impulse} / 15</strong></div>
        <div class="bar-track"><div class="{gauge_cls}" style="width:{impulse_pct}%"></div></div>
      </div>
      <div class="bar-sec">
        <div class="bar-lbl">감정 안정도 <strong>{stable_pct}%</strong></div>
        <div class="bar-track"><div class="bar-fill-teal" style="width:{stable_pct}%"></div></div>
      </div>

      {alert_html}
    </div>

    <!-- ② 72시간 행동 가이드 -->
    <div class="section s-teal">
      <span class="tag">02 · 72시간 가이드</span>
      <h2 class="sec-title">지금 당장 해야 할 것 / 하지 말아야 할 것</h2>
      <p class="sec-sub" style="margin-bottom:12px">감정이 아닌 행동이 결과를 만듭니다.</p>
      <div class="check-list" style="margin-bottom:12px">
        {render_checks(guide_do, "do")}
      </div>
      <div class="check-list">
        {render_checks(guide_dont, "dont")}
      </div>
    </div>

    <!-- ③ 14일 안정화 플랜 -->
    <div class="section s-amber">
      <span class="tag">03 · 14일 플랜</span>
      <h2 class="sec-title">단계별 감정 회복 로드맵</h2>
      <p class="sec-sub">하루씩 따라가다 보면 달라지는 걸 느낄 수 있어요.</p>
      <div class="steps">
        {plan_html}
      </div>
    </div>

   {contact_section_html}

    <!-- ⑤ 도움 받을 곳 -->
    <div class="section s-teal">
      <span class="tag">05 · 도움 받을 곳</span>
      <h2 class="sec-title">혼자 버티기 힘들 때</h2>
      <div class="contact-grid">
        <div class="contact-card">
          <div class="c-num">
             <span class="c-phone">117</span>
          </div>
          <div class="c-label">스토킹 피해<br>상담전화</div>
        </div>
        <div class="contact-card">
          <div class="c-num">
            <span class="c-phone">1577-0199</span>
          </div>
          <div class="c-label">정신건강<br>위기상담전화</div>
        </div>
      </div>
    </div>

    <p class="disclaimer">
      본 리포트는 자체 분석 모델 기반의 참고 추정치이며, 법적 효력을 갖는 통계가 아닙니다.<br>
      개인별 상황에 따라 결과가 다를 수 있으며, 본 서비스는 연애 상담이 아닌 정보 제공 서비스입니다.
    </p>
    """

    return _wrap_html(body, risk_level)


def _wrap_html(body: str, risk_level: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"/>
  <title>관계 진단 리포트 | 리커넥트랩</title>

  <!-- 폰트 -->
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap" rel="stylesheet">

  <style>
{RCL_CSS}

  @media (hover: none) and (pointer: coarse) {{
    body {{ font-size: 15px; padding: 16px 14px 48px; }}
    .section {{ padding: 24px 18px; }}
    .sec-title {{ font-size: 17px; }}
    .sec-sub {{ font-size: 13px; }}
  }}
  </style>
</head>
<body>

<script>
  // ✅ iframe 안에서 열렸는지 감지
  if (window.self !== window.top) {{
    document.documentElement.classList.add('in-iframe');
  }}
</script>

{body}

<script>
  function sendHeight() {{
    var h = document.documentElement.scrollHeight;
    window.parent.postMessage({{ type: 'RCL_REPORT_HEIGHT', height: h }}, '*');
  }}

  function sendRiskLevel() {{
    window.parent.postMessage({{ type: 'RCL_RISK_LEVEL', risk: "{risk_level}" }}, '*');
  }}

  window.addEventListener('load', function() {{
    sendRiskLevel();

    sendHeight();
    setTimeout(sendHeight, 200);
    setTimeout(sendHeight, 600);
    setTimeout(sendHeight, 1200);
  }});

  window.addEventListener('resize', sendHeight);
</script>

</body>
</html>"""


# ── 레거시 호환 유지 ──────────────────────────────────────────────────────────

def make_report_markdown(risk_level: str, impulse: int, fear_type: str) -> str:
    if risk_level == "HARD_BLOCK":
        return (
            "## ⚠️ 안전 우선 안내\n\n"
            "현재 상황에서는 전문기관 상담이 우선 필요할 수 있어요.\n\n"
            "- 스토킹 피해 상담: 📞 117\n"
            "- 정신건강 위기상담: 📞 1577-0199\n"
        )
    return f"""# 관계 안전 가이드
## 1. 현재 상태
- 충동 지수: **{impulse}/15**
- 위험도: **{risk_level}**
- 두려움: **{fear_type}**
## 2. 72시간 행동 가이드
✅ 해야 할 일 — 스트레칭 3분, 알림 차단
❌ 금지 — 차단 우회, 접근 시도
"""


def markdown_to_html(md: str) -> str:
    """레거시 폴백용 (단순 변환)"""
    import re
    html = md
    html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
    html = re.sub(r'^## (.+)$',  r'<h2>\1</h2>', html, flags=re.MULTILINE)
    html = re.sub(r'^# (.+)$',   r'<h1>\1</h1>', html, flags=re.MULTILINE)
    html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
    html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
    html = html.replace('\n\n', '<br><br>')
    return html


def new_token() -> str:
    return secrets.token_urlsafe(32)


def expiry_6_months() -> datetime:
    return datetime.utcnow() + timedelta(days=180)

