from datetime import datetime, timedelta
import secrets


# ──────────────────────────────────────────────────────────────────────────────
# 랜딩페이지와 동일한 디자인 시스템
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
    --r:       14px;
  }

  html { scroll-behavior: smooth; }

  body {
    background: var(--bg);
    color: var(--txt);
    font-family: 'Noto Sans KR', sans-serif;
    font-size: 15px;
    line-height: 1.75;
    padding: 28px 20px 60px;
    -webkit-font-smoothing: antialiased;
  }

  /* ── 섹션 공통 카드 (랜딩페이지 .fact-card 동일 패턴) ── */
  .section {
    background: var(--bg2);
    border: 1px solid var(--divider);
    border-radius: var(--r);
    padding: 22px 20px;
    margin-bottom: 14px;
    position: relative;
    overflow: hidden;
  }

  /* ── 좌측 컬러 포인트 바 ── */
  .section.s-rose::before  { content:''; position:absolute; top:0; left:0; width:4px; height:100%; background:var(--rose); }
  .section.s-teal::before  { content:''; position:absolute; top:0; left:0; width:4px; height:100%; background:var(--teal); }
  .section.s-amber::before { content:''; position:absolute; top:0; left:0; width:4px; height:100%; background:var(--amber); }
  .section.s-red::before   { content:''; position:absolute; top:0; left:0; width:4px; height:100%; background:var(--red); }

  /* ── 태그 (랜딩페이지 .tag 동일) ── */
  .tag {
    display: inline-block;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: .12em;
    text-transform: uppercase;
    color: var(--rose);
    border: 1px solid rgba(212,145,108,.25);
    border-radius: 100px;
    padding: 4px 14px;
    margin-bottom: 14px;
  }

  /* ── 섹션 제목 ── */
  .sec-title {
    font-size: clamp(16px, 4vw, 20px);
    font-weight: 700;
    line-height: 1.4;
    color: var(--txt);
    margin-bottom: 6px;
    word-break: keep-all;
  }
  .sec-sub {
    font-size: 13px;
    color: var(--sub);
    line-height: 1.7;
    margin-bottom: 16px;
    word-break: keep-all;
  }

  /* ── 뱃지 ── */
  .badge {
    display: inline-flex; align-items: center; gap: 6px;
    font-size: 12px; font-weight: 700;
    padding: 5px 14px; border-radius: 100px;
    margin-bottom: 16px;
  }
  .badge.danger  { background: rgba(255,107,107,.15); color: var(--red);   border: 1px solid rgba(255,107,107,.3); }
  .badge.warning { background: rgba(255,179,71,.15);  color: var(--amber); border: 1px solid rgba(255,179,71,.3); }
  .badge.safe    { background: rgba(78,205,196,.15);  color: var(--teal);  border: 1px solid rgba(78,205,196,.3); }

  /* ── 지표 카드 그리드 (랜딩페이지 .metrics-grid 동일) ── */
  .metrics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 16px;
  }
  .metric-box {
    background: var(--bg3);
    border: 1px solid rgba(212,145,108,.15);
    border-radius: 10px;
    padding: 14px 12px;
    text-align: center;
  }
  .m-label { font-size: 11px; color: var(--sub); margin-bottom: 6px; letter-spacing: .04em; }
  .m-val   { font-size: 18px; font-weight: 700; color: var(--rose-lt); }
  .m-val.t { color: var(--teal); }
  .m-val.a { color: var(--amber); }
  .m-val.r { color: var(--red); }

  /* ── 게이지 바 (랜딩페이지 .bar-track 동일) ── */
  .bar-sec   { margin-bottom: 14px; }
  .bar-lbl   { font-size: 13px; color: var(--sub); margin-bottom: 8px; display: flex; justify-content: space-between; }
  .bar-lbl strong { color: var(--txt); }
  .bar-track { width: 100%; height: 8px; background: var(--bg3); border-radius: 100px; overflow: hidden; }
  .bar-fill       { height:100%; border-radius:100px; background:linear-gradient(90deg, var(--rose-lt), var(--rose)); }
  .bar-fill-teal  { height:100%; border-radius:100px; background:linear-gradient(90deg, var(--teal), #3ab5ac); }
  .bar-fill-amber { height:100%; border-radius:100px; background:linear-gradient(90deg, var(--amber), #e8a030); }
  .bar-fill-red   { height:100%; border-radius:100px; background:linear-gradient(90deg, #ff9a9a, var(--red)); }

  /* ── 체크 리스트 (랜딩페이지 .check-item 동일) ── */
  .check-list { display: flex; flex-direction: column; gap: 10px; }
  .check-item {
    display: flex;
    align-items: center;
    gap: 14px;
    background: var(--bg3);
    border: 1px solid var(--divider);
    border-radius: var(--r);
    padding: 14px 16px;
  }
  .check-dot {
    width: 22px; height: 22px; min-width: 22px;
    border-radius: 50%;
    position: relative;
    flex-shrink: 0;
  }
  .check-dot.do   { border: 2px solid var(--teal); }
  .check-dot.dont { border: 2px solid var(--red); }
  .check-dot.do::after {
    content: '✓';
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%,-50%);
    font-size: 11px; color: var(--teal); font-weight: 700;
  }
  .check-dot.dont::after {
    content: '✕';
    position: absolute; top: 50%; left: 50%;
    transform: translate(-50%,-50%);
    font-size: 11px; color: var(--red); font-weight: 700;
  }
  .check-txt { font-size: 13px; line-height: 1.6; color: var(--txt); word-break: keep-all; }
  .check-sub { display: block; font-size: 11px; color: var(--sub); margin-top: 2px; }

  /* ── 스텝 (랜딩페이지 .step 동일) ── */
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
    width: 36px; height: 36px; min-width: 36px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--rose), #BE7D5A);
    color: #fff;
    font-size: 14px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4px 14px rgba(212,145,108,.35);
    flex-shrink: 0;
  }
  .step-content {}
  .step-title { font-size: 14px; font-weight: 700; color: var(--txt); margin-bottom: 4px; }
  .step-title .day { font-size: 11px; font-weight: 700; color: var(--rose); background: rgba(212,145,108,.12); border: 1px solid var(--divider); border-radius: 6px; padding: 2px 8px; margin-right: 8px; }
  .step-desc  { font-size: 13px; color: var(--sub); line-height: 1.65; word-break: keep-all; }

  /* ── 알림 박스 (랜딩페이지 .bridge 동일) ── */
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
  .alert-icon { font-size: 20px; flex-shrink: 0; margin-top: 1px; }
  .alert-text { font-size: 13px; color: var(--txt); line-height: 1.65; word-break: keep-all; }
  .alert-text strong.r { color: var(--red); }
  .alert-text strong.t { color: var(--teal); }
  .alert-text strong.a { color: var(--amber); }

  /* ── 연락처 그리드 ── */
  .contact-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 14px; }
  .contact-card {
    background: var(--bg3);
    border: 1px solid var(--divider);
    border-radius: var(--r);
    padding: 16px 12px;
    text-align: center;
  }
  .c-num   { font-size: 22px; font-weight: 700; color: var(--rose); margin-bottom: 6px; }
  .c-label { font-size: 12px; color: var(--sub); line-height: 1.5; }

  /* ── 면책 푸터 ── */
  .disclaimer {
    margin-top: 24px;
    padding: 16px 18px;
    background: var(--bg2);
    border: 1px solid var(--divider);
    border-radius: var(--r);
    font-size: 11px;
    color: rgba(154,170,187,.6);
    line-height: 1.8;
    text-align: center;
    word-break: keep-all;
  }

  /* postMessage 높이 전송용 */
  html, body { height: auto !important; overflow-x: hidden; }
"""


def _badge_for_risk(risk_level: str) -> str:
    if risk_level == "HIGH":
        return '<span class="badge danger">⚠ 주의 필요 · 충동 지수 높음</span>'
    elif risk_level == "MEDIUM":
        return '<span class="badge warning">◐ 중간 단계 · 관리 필요</span>'
    else:
        return '<span class="badge safe">✓ 안정적 · 감정 조절 양호</span>'


def _gauge_class(risk_level: str) -> str:
    if risk_level == "HIGH":   return "bar-fill-red"
    elif risk_level == "MEDIUM": return "bar-fill-amber"
    else:                        return "bar-fill-teal"


def _m_val_class(risk_level: str) -> str:
    if risk_level == "HIGH":   return "r"
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
        <div class="contact-card"><div class="c-num">117</div><div class="c-label">스토킹 피해<br>상담전화</div></div>
        <div class="contact-card"><div class="c-num">1577-0199</div><div class="c-label">정신건강<br>위기상담전화</div></div>
      </div>
    </div>
    <p class="disclaimer">본 서비스는 정보 제공 목적으로만 운영됩니다.</p>
    """
        return _wrap_html(body)

    # ── 수치 계산 ───────────────────────────────────────────
    impulse_pct  = min(round((impulse / 15) * 100), 100)
    stable_pct   = max(100 - impulse_pct, 10)
    gauge_cls    = _gauge_class(risk_level)
    badge_html   = _badge_for_risk(risk_level)
    mv_cls       = _m_val_class(risk_level)

    fear_map = {
        "new_partner": "새로운 사람이 생길까봐",
        "forget":      "완전히 잊혀질까봐",
        "regret":      "나중에 후회할까봐",
        "other":       "기타 / 혼합",
    }
    fear_label = fear_map.get(fear_type, fear_type or "기타")

    risk_label = {"HIGH": "주의", "MEDIUM": "보통", "LOW": "안정"}.get(risk_level, risk_level)

    # ── 위험도별 알림 박스 ───────────────────────────────────
    if risk_level == "HIGH":
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

    # ── 행동 가이드 리스트 ───────────────────────────────────
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
        ("1–3일",   "72시간 완전 차단 유지",    "가장 충동이 강한 시기예요. 버티는 것 자체가 진전이에요."),
        ("4–7일",   "하루 루틴 만들기",          "기상 시간 고정 · 산책 10분 · 잠들기 전 노트 쓰기"),
        ("8–12일",  "감정 거리두기 연습",        "상대 생각이 올라올 때 — 3초 멈추고 숨 한 번 내쉬기"),
        ("13–14일", "현재 상태 재점검",          "충동 지수가 낮아졌다면 프리미엄 리포트로 다음 단계 확인"),
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
    if risk_level == "HIGH":
        contact_cond = "충동 지수 6 이하 + 최소 2주 이상 지난 시점"
        contact_box_cls = "danger"
        contact_icon = "🚫"
    elif risk_level == "MEDIUM":
        contact_cond = "충동 지수 4 이하 + 감정이 차분한 낮 시간대"
        contact_box_cls = "warn"
        contact_icon = "⏳"
    else:
        contact_cond = "감정이 안정된 상태 + 상대가 연락을 거부하지 않았을 때"
        contact_box_cls = "safe"
        contact_icon = "📋"

    # ── 최종 body HTML ───────────────────────────────────────
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
          <div class="m-val {mv_cls}">{impulse}<span style="font-size:13px;font-weight:400;color:var(--sub)"> / 15</span></div>
        </div>
        <div class="metric-box">
          <div class="m-label">위험 단계</div>
          <div class="m-val {mv_cls}">{risk_label}</div>
        </div>
        <div class="metric-box">
          <div class="m-label">주요 두려움</div>
          <div class="m-val" style="font-size:12px;color:var(--rose-lt)">{fear_label}</div>
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

    <!-- ④ 재접촉 안전 기준 -->
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

    <!-- ⑤ 도움 받을 곳 -->
    <div class="section s-teal">
      <span class="tag">05 · 도움 받을 곳</span>
      <h2 class="sec-title">혼자 버티기 힘들 때</h2>
      <div class="contact-grid">
        <div class="contact-card"><div class="c-num">117</div><div class="c-label">스토킹 피해<br>상담전화</div></div>
        <div class="contact-card"><div class="c-num">1577-0199</div><div class="c-label">정신건강<br>위기상담전화</div></div>
      </div>
    </div>

    <p class="disclaimer">
      본 리포트는 자체 분석 모델 기반의 참고 추정치이며, 법적 효력을 갖는 통계가 아닙니다.<br>
      개인별 상황에 따라 결과가 다를 수 있으며, 본 서비스는 연애 상담이 아닌 정보 제공 서비스입니다.
    </p>
    """

    return _wrap_html(body)


def _wrap_html(body: str) -> str:
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
  // 부모 창으로 콘텐츠 높이 전송 (iframe 자동 리사이즈)
  function sendHeight() {{
    var h = document.documentElement.scrollHeight;
    window.parent.postMessage({{ type: 'RCL_REPORT_HEIGHT', height: h }}, '*');
  }}
  window.addEventListener('load', function() {{
    sendHeight();
    setTimeout(sendHeight, 500);
    setTimeout(sendHeight, 1200);
  }});
  window.addEventListener('resize', sendHeight);
</script>
</body>
</html>"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from .report import make_report_html

app = FastAPI()

@app.get("/report/{token}", response_class=HTMLResponse)
async def view_report(token: str):
    report_data = await db.fetch_one(
        "SELECT * FROM reports WHERE token = :token", 
        {"token": token}
    )
    
    if not report_data:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다")
    
    if report_data["expires_at"] < datetime.utcnow():
        raise HTTPException(status_code=410, detail="만료된 리포트입니다")
    
    return make_report_html(
        risk_level=report_data["risk_level"],
        impulse=report_data["impulse"],
        fear_type=report_data["fear_type"]
    )
# ── 레거시 호환 유지 ──────────────────────────────────────────────────────────

def make_report_markdown(risk_level: str, impulse: int, fear_type: str) -> str:
    if risk_level == "HARD_BLOCK":
        return (
            "## ⚠️ 안전 우선 안내\n\n"
            "현재 상황에서는 전문기관 상담이 우선 필요할 수 있어요.\n\n"
            "- 스토킹 피해 상담: 117\n"
            "- 정신건강 위기상담: 1577-0199\n"
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
