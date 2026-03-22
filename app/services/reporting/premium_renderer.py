from __future__ import annotations

from html import escape

from markdown import markdown


PREMIUM_REPORT_CSS = """
:root{
  --bg:#0f1626;
  --bg2:#131C30;
  --card:#1A2438;
  --card-hover:#1E2944;
  --text:#EDE9E4;
  --sub:#8A9BB0;
  --line:rgba(212,145,108,.16);
  --line2:rgba(255,255,255,.07);
  --point:#D4916C;
  --point-dim:rgba(212,145,108,.12);
  --gold:#E8B87A;
  --stable:#22c55e;
  --caution:#facc15;
  --danger:#ef4444;
  --glow-stable:rgba(34,197,94,.10);
  --glow-caution:rgba(250,204,21,.10);
  --glow-danger:rgba(239,68,68,.10);
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:var(--bg);
  color:var(--text);
  font-family:'Noto Sans KR',sans-serif;
  font-size:15px;
  line-height:1.8;
  -webkit-font-smoothing:antialiased;
}
.report-root{
  width:100%;
  min-height:100vh;
  padding:32px 0 8px;
  display:flow-root;
}
.wrap{
  max-width:1180px;
  margin:0 auto;
  padding:16px 14px 56px;
}
.hero{
  position:relative;
  overflow:hidden;
  background:linear-gradient(180deg, #121c33 0%, #0f1626 100%);
  border:1px solid var(--line);
  border-radius:20px;
  padding:24px 22px 20px;
  margin-bottom:20px;
}
.hero::before{
  content:'';
  position:absolute;
  top:0;
  left:0;
  width:4px;
  height:100%;
  background:rgba(212,145,108,.92);
}
.hero-top{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:16px;
  margin-bottom:10px;
}
.hero-title-wrap{min-width:0}
.hero-title-row{
  margin-bottom:6px;
}
.hero-title{
  font-size:20px;
  font-weight:800;
  line-height:1.3;
  color:#fff;
  letter-spacing:-.02em;
}
.hero-meta{
  color:var(--sub);
  font-size:13px;
  letter-spacing:.02em;
}
.hero-badge{
  display:inline-flex;
  align-items:center;
  gap:5px;
  padding:6px 14px;
  border-radius:999px;
  background:linear-gradient(135deg, rgba(232,184,122,.20), rgba(212,145,108,.12));
  border:1px solid rgba(232,184,122,.35);
  color:var(--gold);
  font-size:11px;
  font-weight:800;
  letter-spacing:.12em;
  white-space:nowrap;
  text-transform:uppercase;
}
.hero-badge::before{content:'✦';font-size:9px}
.lead{
  color:var(--sub);
  font-size:14px;
  line-height:1.7;
  border-top:1px solid rgba(255,255,255,.06);
  padding-top:12px;
  margin-top:4px;
}
.metrics-panel{margin:0 0 20px}
.metrics-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:12px;
  margin:0 0 12px;
}
.metric-card{
  position:relative;
  overflow:hidden;
  background:linear-gradient(160deg, rgba(255,255,255,.045) 0%, rgba(255,255,255,.018) 100%);
  border:1px solid var(--line2);
  border-radius:18px;
  padding:18px 16px 16px;
  min-height:136px;
  box-shadow:0 8px 32px rgba(0,0,0,.18), inset 0 1px 0 rgba(255,255,255,.06);
  transition:box-shadow .2s;
}
.metric-card::before{
  content:none;
}
.metric-card[data-tone="stable"]{border-color:var(--line2);box-shadow:0 8px 32px rgba(0,0,0,.18), inset 0 1px 0 rgba(255,255,255,.06)}
.metric-card[data-tone="caution"]{border-color:var(--line2);box-shadow:0 8px 32px rgba(0,0,0,.18), inset 0 1px 0 rgba(255,255,255,.06)}
.metric-card[data-tone="danger"]{border-color:var(--line2);box-shadow:0 8px 32px rgba(0,0,0,.18), inset 0 1px 0 rgba(255,255,255,.06)}
.metric-title{
  font-size:11.5px;
  font-weight:700;
  color:var(--sub);
  letter-spacing:.04em;
  margin-bottom:12px;
  text-transform:uppercase;
}
.metric-value-row{
  display:flex;
  align-items:flex-end;
  justify-content:space-between;
  gap:10px;
  margin-bottom:10px;
}
.metric-value{
  font-size:18px;
  font-weight:800;
  line-height:1.25;
  color:#fff;
  letter-spacing:-.02em;
}
.metric-score{
  font-size:28px;
  font-weight:800;
  line-height:1;
  color:#fff;
  flex:none;
  opacity:.92;
}
.metric-summary{
  font-size:11.5px;
  line-height:1.6;
  color:var(--sub);
  margin-bottom:10px;
}
.card-bar{
  margin-top:auto;
  width:100%;
  height:3px;
  border-radius:999px;
  background:rgba(255,255,255,.06);
  overflow:hidden;
}
.card-bar-fill{
  height:100%;
  border-radius:999px;
}
.metric-card[data-tone="stable"] .card-bar-fill{background:var(--stable);width:var(--score-w, 50%)}
.metric-card[data-tone="caution"] .card-bar-fill{background:var(--caution);width:var(--score-w, 50%)}
.metric-card[data-tone="danger"] .card-bar-fill{background:var(--danger);width:var(--score-w, 50%)}
.bars{display:grid;gap:10px}
.metric-bar{
  position:relative;
  overflow:hidden;
  background:linear-gradient(160deg, rgba(255,255,255,.04) 0%, rgba(255,255,255,.015) 100%);
  border:1px solid var(--line2);
  border-radius:18px;
  padding:18px 20px 16px;
  box-shadow:0 8px 28px rgba(0,0,0,.14), inset 0 1px 0 rgba(255,255,255,.05);
}
.metric-bar::before{
  content:none;
}
.metric-bar[data-tone="stable"]{border-color:var(--line2)}
.metric-bar[data-tone="caution"]{border-color:var(--line2)}
.metric-bar[data-tone="danger"]{border-color:var(--line2)}
.metric-bar-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:16px;
  margin-bottom:12px;
}
.metric-bar-copy{min-width:0}
.metric-bar-title{
  font-size:14px;
  font-weight:700;
  color:#fff;
  margin-bottom:3px;
  letter-spacing:-.01em;
}
.metric-bar-state{
  font-size:12px;
  color:var(--sub);
  line-height:1.45;
}
.metric-bar-score{
  font-size:28px;
  font-weight:800;
  color:#fff;
  line-height:1;
  flex:none;
  letter-spacing:-.02em;
}
.metric-bar-track{
  width:100%;
  height:8px;
  border-radius:999px;
  background:rgba(255,255,255,.07);
  overflow:hidden;
  position:relative;
}
.metric-bar-fill{
  height:100%;
  border-radius:999px;
  transition:width .6s ease;
  position:relative;
}
.metric-bar[data-tone="stable"] .metric-bar-fill{background:var(--stable)}
.metric-bar[data-tone="caution"] .metric-bar-fill{background:var(--caution)}
.metric-bar[data-tone="danger"] .metric-bar-fill{background:var(--danger)}
.metric-bar-fill::after{
  content:'';
  position:absolute;
  right:-1px; top:50%;
  transform:translateY(-50%);
  width:12px; height:12px;
  border-radius:50%;
  background:inherit;
  box-shadow:0 0 8px 2px currentColor;
  filter:blur(1px);
  opacity:.7;
}
.content{
  background:var(--bg2);
  border:1px solid var(--line);
  border-radius:20px;
  padding:28px 26px 32px;
  box-shadow:0 4px 40px rgba(0,0,0,.12);
}
.content h1{
  margin:0 0 20px;
  font-size:22px;
  font-weight:800;
  color:#fff;
  letter-spacing:-.03em;
  line-height:1.3;
}
.content h2{
  display:flex;
  align-items:center;
  gap:10px;
  font-size:17px;
  font-weight:800;
  margin:36px 0 12px;
  padding:20px 0 14px;
  border-top:1px solid rgba(255,255,255,.06);
  color:#fff;
  letter-spacing:-.02em;
  line-height:1.35;
}
.content h2::before{
  content:'';
  display:inline-block;
  width:3px; height:18px;
  border-radius:2px;
  background:var(--point);
  flex:none;
}
.content h3{
  font-size:15px;
  font-weight:700;
  margin:20px 0 8px;
  color:var(--gold);
  letter-spacing:-.01em;
}
.content p{
  margin:0 0 14px;
  color:var(--text);
  font-size:14.5px;
  line-height:1.85;
}
.content ul,.content ol{
  margin:0 0 16px 4px;
  padding:0;
  list-style:none;
}
.content ul li,.content ol li{
  position:relative;
  padding-left:18px;
  margin:0 0 9px;
  font-size:14.5px;
  line-height:1.8;
  color:var(--text);
}
.content ul li::before{
  content:'';
  position:absolute;
  left:2px; top:.75em;
  width:5px; height:5px;
  border-radius:50%;
  background:var(--point);
  opacity:.7;
}
.content ol{counter-reset:li}
.content ol li::before{
  counter-increment:li;
  content:counter(li)'.';
  position:absolute;
  left:0;
  color:var(--point);
  font-weight:700;
  font-size:13px;
}
.content strong{color:#fff;font-weight:700}
.content blockquote{
  margin:16px 0;
  padding:14px 16px;
  border-left:3px solid var(--point);
  background:rgba(212,145,108,.06);
  border-radius:0 10px 10px 0;
  font-size:14px;
  color:var(--text);
}
.content hr{
  border:none;
  border-top:1px solid rgba(255,255,255,.06);
  margin:28px 0;
}
.help-card{
  margin-top:16px;
  border-radius:20px;
  padding:24px 22px;
  border:1px solid rgba(212,145,108,.20);
  background:linear-gradient(180deg, #0f1a2e, #0c1628);
}
.help-tag{
  display:inline-flex;
  align-items:center;
  gap:6px;
  font-size:11px;
  font-weight:700;
  letter-spacing:.10em;
  text-transform:uppercase;
  color:#8ea1b7;
  border:1px solid rgba(159,176,195,.18);
  border-radius:999px;
  padding:4px 12px;
  margin-bottom:12px;
  background:rgba(255,255,255,.03);
}
.help-title{
  margin:0 0 18px;
  font-size:20px;
  font-weight:800;
  line-height:1.3;
  color:#fff;
  letter-spacing:-.02em;
}
.contact-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:12px;
}
.contact-card{
  background:rgba(255,255,255,.04);
  border:1px solid rgba(255,255,255,.08);
  border-radius:16px;
  padding:18px 16px;
  transition:background .2s;
}
.contact-card:hover{background:rgba(255,255,255,.07)}
.contact-num{margin-bottom:8px}
.contact-phone{
  display:inline-block;
  font-size:24px;
  font-weight:800;
  line-height:1;
  color:#fff;
  letter-spacing:-.02em;
}
.contact-phone::before{
  content:'📞';
  display:inline-block;
  font-size:13px;
  margin-right:8px;
  vertical-align:middle;
  opacity:.78;
}
.contact-label{
  font-size:13px;
  line-height:1.65;
  color:var(--sub);
}
.footer{
  margin-top:20px;
  color:var(--sub);
  font-size:12.5px;
  text-align:center;
  line-height:1.7;
  opacity:.75;
}
.state-wrap{
  min-height:100vh;
  display:flex;
  align-items:center;
  justify-content:center;
  padding:24px 18px;
}
.state-card{
  width:100%;
  max-width:560px;
  padding:28px 22px;
  text-align:center;
  background:var(--bg2);
  border:1px solid var(--line);
  border-radius:20px;
}
.state-badge{
  display:inline-block;
  font-size:11px;
  font-weight:700;
  letter-spacing:.12em;
  text-transform:uppercase;
  color:var(--point);
  border:1px solid rgba(212,145,108,.25);
  border-radius:100px;
  padding:4px 12px;
  margin-bottom:14px;
}
.state-title{
  font-size:22px;
  font-weight:800;
  margin-bottom:8px;
  color:#fff;
}
.state-copy{
  font-size:14px;
  color:var(--sub);
  line-height:1.8;
  margin-bottom:18px;
}
.state-cta{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  min-height:48px;
  padding:0 20px;
  border-radius:999px;
  border:none;
  text-decoration:none;
  background:linear-gradient(135deg,var(--point),#BE7D5A);
  color:#fff;
  font-weight:700;
}
@media (max-width:768px){
  .report-root{padding:20px 0 6px}
  .wrap{padding:10px 9px 40px}
  .hero-top{flex-direction:column;align-items:flex-start}
  .metrics-grid{grid-template-columns:1fr}
  .metric-card{min-height:auto}
  .metric-bar-head{align-items:center}
  .contact-grid{grid-template-columns:1fr}
  .content{padding:20px 16px 24px}
  .content h2{font-size:16px}
}
"""


def _short_summary(text: str) -> str:
    normalized = " ".join((text or "").split())
    if not normalized:
        return ""
    return normalized[:90].rstrip() + ("..." if len(normalized) > 90 else "")


def _tone_from_score(score: int, *, reverse: bool = False) -> str:
    if reverse:
        if score >= 70:
            return "stable"
        if score >= 50:
            return "caution"
        if score >= 35:
            return "caution"
        return "danger"

    if score <= 29:
        return "stable"
    if score <= 54:
        return "caution"
    if score <= 74:
        return "caution"
    return "danger"


def _shell(inner_html: str, *, state: str) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover" />
  <title>프리미엄 리포트</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap" rel="stylesheet" />
  <style>{PREMIUM_REPORT_CSS}</style>
</head>
<body>
<div class="report-root">
{inner_html}
</div>
<script>
  function calcHeight() {{
    var docEl = document.documentElement;
    var body = document.body;
    if (!docEl || !body) return 0;

    return Math.max(
      docEl.scrollHeight || 0,
      docEl.offsetHeight || 0,
      docEl.clientHeight || 0,
      body.scrollHeight || 0,
      body.offsetHeight || 0,
      body.clientHeight || 0
    );
  }}

  var lastSentHeight = 0;
  var lastMeasuredHeight = 0;
  var lastSentAt = 0;
  var rafId = 0;
  var resizeTimer = 0;
  function sendHeight(force) {{
    var now = Date.now();
    var h = calcHeight();
    if (!h) return;
    if ((now - lastSentAt) < 180) return;
    if (Math.abs(h - lastSentHeight) <= 8) return;
    if (!force && Math.abs(h - lastMeasuredHeight) <= 8) return;
    lastMeasuredHeight = h;
    lastSentHeight = h;
    lastSentAt = now;
    window.parent.postMessage({{ type: "RCL_REPORT_HEIGHT", height: h }}, "*");
  }}

  function requestHeight(force) {{
    if (rafId) {{
      cancelAnimationFrame(rafId);
    }}
    rafId = requestAnimationFrame(function() {{
      rafId = 0;
      sendHeight(!!force);
    }});
  }}

  function scheduleHeightBursts() {{
    requestHeight(true);
    setTimeout(function() {{ requestHeight(true); }}, 160);
    setTimeout(function() {{ requestHeight(true); }}, 420);
    setTimeout(function() {{ requestHeight(true); }}, 1000);
  }}

  document.addEventListener("DOMContentLoaded", function() {{
    scheduleHeightBursts();
  }});

  window.addEventListener("load", function() {{
    window.parent.postMessage({{ type: "RCL_PREMIUM_STATE", state: "{escape(state)}" }}, "*");
    scheduleHeightBursts();
  }});

  window.addEventListener("resize", function() {{
    requestHeight(true);
  }});

  if (document.fonts && document.fonts.ready) {{
    document.fonts.ready.then(function() {{
      scheduleHeightBursts();
    }}).catch(function() {{}});
  }}

  if (window.ResizeObserver) {{
    var ro = new ResizeObserver(function() {{
      if (resizeTimer) {{
        clearTimeout(resizeTimer);
      }}
      resizeTimer = setTimeout(function() {{
        resizeTimer = 0;
        requestHeight(false);
      }}, 140);
    }});
    ro.observe(document.documentElement);
    if (document.body) {{
      ro.observe(document.body);
    }}
  }}
</script>
</body>
</html>"""


def _render_metrics_html(metrics: dict | None) -> str:
    cards = metrics.get("cards") if isinstance(metrics, dict) else []
    if not cards:
        return ""

    card_map = {}
    for card in cards:
        if isinstance(card, dict) and card.get("id"):
            card_map[str(card["id"])] = card

    card_order = [
        "relationship_distance",
        "emotional_temperature",
        "contact_timing",
        "current_risk_signal",
    ]
    bar_order = [
        "recovery_conditions",
        "emotional_stability",
    ]
    reverse_good_ids = {"recovery_conditions", "emotional_stability"}

    card_html = []
    for card_id in card_order:
        card = card_map.get(card_id)
        if not card:
            continue
        score = max(0, min(100, int(card.get("score") or 0)))
        tone = _tone_from_score(score)
        card_html.append(
            f"""
      <section class="metric-card" data-tone="{tone}" data-metric-id="{escape(card_id)}">
        <div class="metric-title">{escape(str(card.get("title") or ""))}</div>
        <div class="metric-value-row">
          <div class="metric-value">{escape(str(card.get("value_text") or ""))}</div>
          <div class="metric-score">{score}</div>
        </div>
        <div class="metric-summary">{escape(_short_summary(str(card.get("summary") or "")))}</div>
        <div class="card-bar"><div class="card-bar-fill" style="--score-w:{score}%"></div></div>
      </section>
"""
        )

    bar_html = []
    for card_id in bar_order:
        card = card_map.get(card_id)
        if not card:
            continue
        score = max(0, min(100, int(card.get("score") or 0)))
        tone = _tone_from_score(score, reverse=card_id in reverse_good_ids)
        bar_html.append(
            f"""
      <section class="metric-bar" data-tone="{tone}" data-metric-id="{escape(card_id)}">
        <div class="metric-bar-head">
          <div class="metric-bar-copy">
            <div class="metric-bar-title">{escape(str(card.get("title") or ""))}</div>
            <div class="metric-bar-state">{escape(str(card.get("value_text") or ""))}</div>
          </div>
          <div class="metric-bar-score">{score}</div>
        </div>
        <div class="metric-bar-track"><div class="metric-bar-fill" style="width:{score}%"></div></div>
      </section>
"""
        )

    return f"""
    <section class="metrics-panel">
      <section class="metrics-grid">
        {''.join(card_html)}
      </section>
      <section class="bars">
        {''.join(bar_html)}
      </section>
    </section>
"""


def render_premium_report_html(markdown_text: str, metrics: dict | None = None) -> str:
    md = (markdown_text or "").strip()
    if not md:
        raise ValueError("premium markdown is empty")

    body_html = markdown(md, extensions=["extra", "nl2br", "sane_lists"])
    metrics_html = _render_metrics_html(metrics)

    inner_html = f"""
  <div class="wrap">
    <section class="hero">
      <div class="hero-top">
        <div class="hero-title-wrap">
          <div class="hero-title-row">
            <div class="hero-title">관계 진단 리포트</div>
          </div>
          <div class="hero-meta">분석 완료 &nbsp;&nbsp; 리커넥트랩</div>
        </div>
        <div class="hero-badge">프리미엄</div>
      </div>
      <div class="lead">관계 해석보다 행동 안정성, 회복 가능성, 리스크 관리에 초점을 둔 개인 맞춤 가이드</div>
    </section>

    {metrics_html}

    <main class="content">
      {body_html}
    </main>

    <section class="help-card">
      <span class="help-tag">도움 받을 곳</span>
      <div class="help-title">혼자 버티기 어렵다면</div>
      <div class="contact-grid">
        <div class="contact-card">
          <div class="contact-num"><span class="contact-phone">117</span></div>
          <div class="contact-label">스토킹·피해 상담전화</div>
        </div>
        <div class="contact-card">
          <div class="contact-num"><span class="contact-phone">1577-0199</span></div>
          <div class="contact-label">정신건강 위기상담전화</div>
        </div>
      </div>
    </section>

    <div class="footer">
      본 리포트는 감정 자극이 아닌 안전 중단과 행동 가이드를 목적으로 제공합니다.
    </div>
  </div>
"""
    return _shell(inner_html, state="READY")


def render_premium_processing_html(*, message: str = "프리미엄 리포트를 생성 중입니다.") -> str:
    inner_html = f"""
  <div class="state-wrap">
    <section class="state-card">
      <div class="state-badge">PROCESSING</div>
      <div class="state-title">리포트를 생성하는 중입니다</div>
      <div class="state-copy">{escape(message)}</div>
    </section>
  </div>
"""
    return _shell(inner_html, state="PROCESSING")


def render_premium_state_html(
    *,
    state: str,
    title: str,
    message: str,
    cta_label: str | None = None,
    cta_href: str | None = None,
) -> str:
    cta_html = ""
    if cta_label and cta_href:
        cta_html = f'<a class="state-cta" href="{escape(cta_href)}">{escape(cta_label)}</a>'

    inner_html = f"""
  <div class="state-wrap">
    <section class="state-card">
      <div class="state-badge">{escape(state)}</div>
      <div class="state-title">{escape(title)}</div>
      <div class="state-copy">{escape(message)}</div>
      {cta_html}
    </section>
  </div>
"""
    return _shell(inner_html, state=state)
