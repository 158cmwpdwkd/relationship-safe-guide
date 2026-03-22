from __future__ import annotations

from html import escape

from markdown import markdown


PREMIUM_REPORT_CSS = """
:root{
  --bg:#0F1626;
  --bg2:#1A2540;
  --bg3:#222E4A;
  --txt:#F0ECE8;
  --sub:#9AAABB;
  --rose:#D4916C;
  --rose-lt:#EAB89A;
  --teal:#4ECDC4;
  --amber:#FFB347;
  --red:#FF6B6B;
  --line:rgba(212,145,108,.18);
  --line2:rgba(255,255,255,.07);
  --radius:14px;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:var(--bg);
  color:var(--txt);
  font-family:'Noto Sans KR',sans-serif;
  font-size:16px;
  line-height:1.75;
  -webkit-font-smoothing:antialiased;
}
.report-root{
  width:100%;
  min-height:100vh;
  padding:20px 0 8px;
  display:flow-root;
}
.wrap{
  max-width:680px;
  margin:0 auto;
  padding:28px 20px 60px;
}
.hero,.content,.metric-card,.metric-bar,.help-card,.state-card{
  background:var(--bg2);
  border:1px solid var(--line);
  border-radius:var(--radius);
}
.hero{
  padding:24px 20px 18px;
  margin-bottom:14px;
  position:relative;
  overflow:hidden;
}
.hero::before{
  content:'';
  position:absolute;
  top:0;
  left:0;
  width:4px;
  height:100%;
  background:var(--rose);
}
.hero-top{
  display:flex;
  align-items:flex-start;
  justify-content:space-between;
  gap:16px;
  margin-bottom:10px;
}
.hero-title{
  font-size:21px;
  font-weight:800;
  line-height:1.35;
  margin-bottom:6px;
}
.hero-meta{
  font-size:13px;
  color:var(--sub);
}
.hero-badge{
  display:inline-flex;
  align-items:center;
  gap:6px;
  font-size:11px;
  font-weight:700;
  letter-spacing:.12em;
  text-transform:uppercase;
  color:var(--rose);
  border:1px solid rgba(212,145,108,.25);
  border-radius:100px;
  padding:4px 12px;
  white-space:nowrap;
}
.lead{
  font-size:14px;
  color:var(--sub);
  line-height:1.7;
}
.metrics-panel{margin-bottom:14px}
.metrics-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:10px;
  margin-bottom:10px;
}
.metric-card{
  background:var(--bg3);
  border-color:var(--line2);
  padding:14px 14px 12px;
}
.metric-title{
  font-size:12px;
  color:var(--sub);
  margin-bottom:8px;
}
.metric-value-row{
  display:flex;
  align-items:flex-end;
  justify-content:space-between;
  gap:8px;
  margin-bottom:8px;
}
.metric-value{
  font-size:16px;
  font-weight:700;
  color:var(--rose-lt);
}
.metric-score{
  font-size:24px;
  font-weight:800;
  color:#fff;
}
.metric-summary{
  font-size:12px;
  line-height:1.6;
  color:var(--sub);
}
.card-bar{
  width:100%;
  height:4px;
  background:rgba(255,255,255,.06);
  border-radius:100px;
  overflow:hidden;
  margin-top:10px;
}
.card-bar-fill{
  height:100%;
  border-radius:100px;
  background:linear-gradient(90deg,var(--rose-lt),var(--rose));
}
.bars{display:grid;gap:10px}
.metric-bar{
  padding:16px 18px;
}
.metric-bar-head{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap:12px;
  margin-bottom:10px;
}
.metric-bar-title{
  font-size:14px;
  font-weight:700;
  color:#fff;
  margin-bottom:3px;
}
.metric-bar-state{
  font-size:12px;
  color:var(--sub);
}
.metric-bar-score{
  font-size:26px;
  font-weight:800;
  color:#fff;
}
.metric-bar-track{
  width:100%;
  height:8px;
  background:rgba(255,255,255,.07);
  border-radius:100px;
  overflow:hidden;
}
.metric-bar-fill{
  height:100%;
  border-radius:100px;
  background:linear-gradient(90deg,var(--rose-lt),var(--rose));
}
.content{
  padding:24px 20px 28px;
}
.content h1{
  font-size:22px;
  font-weight:800;
  margin:0 0 18px;
}
.content h2{
  font-size:18px;
  font-weight:800;
  margin:28px 0 12px;
  padding-top:18px;
  border-top:1px solid rgba(255,255,255,.06);
  display:flex;
  align-items:center;
  gap:10px;
}
.content h2::before{
  content:'';
  width:3px;
  height:18px;
  border-radius:2px;
  background:var(--rose);
  flex:none;
}
.content h3{
  font-size:15px;
  font-weight:700;
  margin:18px 0 8px;
  color:var(--rose-lt);
}
.content p{
  margin:0 0 14px;
  font-size:15px;
  line-height:1.8;
  color:var(--txt);
}
.content ul,.content ol{
  margin:0 0 14px;
  padding:0;
  list-style:none;
}
.content li{
  position:relative;
  padding-left:18px;
  margin:0 0 9px;
  color:var(--txt);
}
.content ul li::before{
  content:'';
  position:absolute;
  left:2px;
  top:.75em;
  width:5px;
  height:5px;
  border-radius:50%;
  background:var(--rose);
}
.content blockquote{
  margin:16px 0;
  padding:14px 16px;
  background:rgba(212,145,108,.08);
  border-left:3px solid var(--rose);
  border-radius:0 12px 12px 0;
}
.help-card{
  margin-top:14px;
  padding:20px;
}
.help-title{
  font-size:18px;
  font-weight:800;
  margin-bottom:14px;
}
.contact-grid{
  display:grid;
  grid-template-columns:repeat(2,minmax(0,1fr));
  gap:10px;
}
.contact-card{
  background:var(--bg3);
  border:1px solid var(--line);
  border-radius:14px;
  padding:16px 14px;
}
.contact-num{
  font-size:22px;
  font-weight:800;
  margin-bottom:6px;
}
.contact-label{
  font-size:13px;
  color:var(--sub);
  line-height:1.6;
}
.footer{
  margin-top:22px;
  text-align:center;
  font-size:12px;
  color:rgba(154,170,187,.7);
  line-height:1.8;
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
}
.state-badge{
  display:inline-block;
  font-size:11px;
  font-weight:700;
  letter-spacing:.12em;
  text-transform:uppercase;
  color:var(--rose);
  border:1px solid rgba(212,145,108,.25);
  border-radius:100px;
  padding:4px 12px;
  margin-bottom:14px;
}
.state-title{
  font-size:22px;
  font-weight:800;
  margin-bottom:8px;
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
  background:linear-gradient(135deg,var(--rose),#BE7D5A);
  color:#fff;
  font-weight:700;
}
@media (max-width:680px){
  .report-root{padding:16px 0 8px}
  .wrap{padding:22px 16px 52px}
  .metrics-grid{grid-template-columns:1fr}
  .contact-grid{grid-template-columns:1fr}
}
"""


def _short_summary(text: str) -> str:
    normalized = " ".join((text or "").split())
    if not normalized:
        return ""
    return normalized[:90].rstrip() + ("..." if len(normalized) > 90 else "")


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
  var rafId = 0;
  function sendHeight(force) {{
    var h = calcHeight();
    if (!h) return;
    if (!force && Math.abs(h - lastSentHeight) <= 4) return;
    lastSentHeight = h;
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
    setTimeout(function() {{ requestHeight(true); }}, 80);
    setTimeout(function() {{ requestHeight(true); }}, 200);
    setTimeout(function() {{ requestHeight(true); }}, 400);
    setTimeout(function() {{ requestHeight(true); }}, 800);
    setTimeout(function() {{ requestHeight(true); }}, 1400);
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
      requestHeight(false);
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

    card_html = []
    for card_id in card_order:
        card = card_map.get(card_id)
        if not card:
            continue
        score = max(0, min(100, int(card.get("score") or 0)))
        card_html.append(
            f"""
      <section class="metric-card" data-metric-id="{escape(card_id)}">
        <div class="metric-title">{escape(str(card.get("title") or ""))}</div>
        <div class="metric-value-row">
          <div class="metric-value">{escape(str(card.get("value_text") or ""))}</div>
          <div class="metric-score">{score}</div>
        </div>
        <div class="metric-summary">{escape(_short_summary(str(card.get("summary") or "")))}</div>
        <div class="card-bar"><div class="card-bar-fill" style="width:{score}%"></div></div>
      </section>
"""
        )

    bar_html = []
    for card_id in bar_order:
        card = card_map.get(card_id)
        if not card:
            continue
        score = max(0, min(100, int(card.get("score") or 0)))
        bar_html.append(
            f"""
      <section class="metric-bar" data-metric-id="{escape(card_id)}">
        <div class="metric-bar-head">
          <div>
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
        <div>
          <div class="hero-title">관계 진단 리포트</div>
          <div class="hero-meta">분석 완료 · ReconnectLab</div>
        </div>
        <div class="hero-badge">PREMIUM</div>
      </div>
      <div class="lead">무료 진단보다 더 구체적인 관계 해석과 행동 가이드를 정리한 프리미엄 리포트입니다.</div>
    </section>

    {metrics_html}

    <main class="content">
      {body_html}
    </main>

    <section class="help-card">
      <div class="help-title">도움이 더 필요할 때</div>
      <div class="contact-grid">
        <div class="contact-card">
          <div class="contact-num">117</div>
          <div class="contact-label">스토킹·피해 상담전화</div>
        </div>
        <div class="contact-card">
          <div class="contact-num">1577-0199</div>
          <div class="contact-label">정신건강 위기상담전화</div>
        </div>
      </div>
    </section>

    <div class="footer">
      본 리포트는 감정 자극이 아니라 안전 중심의 행동 가이드를 목적으로 제공합니다.
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
