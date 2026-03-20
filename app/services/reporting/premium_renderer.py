from __future__ import annotations

from html import escape

from markdown import markdown


PREMIUM_REPORT_CSS = """
:root{
  --bg:#0B1120;
  --bg2:#131C30;
  --card:#1A2438;
  --card-hover:#1E2944;
  --text:#EDE9E4;
  --sub:#8A9BB0;
  --line:rgba(212,145,108,.16);
  --line2:rgba(255,255,255,.07);
  --point:#d4916c;
  --point-dim:rgba(212,145,108,.12);
  --gold:#d4916c;
  --stable:#4ecb8b;
  --caution:#f0c05a;
  --warning:#e26d6d;
  --danger:#e26d6d;
  --glow-stable:rgba(78,203,139,.10);
  --glow-caution:rgba(240,192,90,.10);
  --glow-warning:rgba(226,109,109,.10);
  --glow-danger:rgba(226,109,109,.10);
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
  padding-bottom:env(safe-area-inset-bottom, 0);
}
.wrap{
  max-width:820px;
  margin:0 auto;
  padding:32px 18px calc(72px + env(safe-area-inset-bottom, 0));
}
.hero{
  position:relative;
  overflow:hidden;
  background:linear-gradient(145deg, rgba(212,145,108,.13) 0%, rgba(212,145,108,.05) 55%, rgba(212,145,108,.02) 100%);
  border:1px solid var(--line);
  border-radius:20px;
  padding:24px 24px 20px;
  margin-bottom:20px;
}
.hero::before{
  content:'';
  position:absolute;
  top:0;
  left:0;
  right:0;
  height:1px;
  background:linear-gradient(90deg, transparent 0%, rgba(212,145,108,.42) 40%, rgba(212,145,108,.24) 70%, transparent 100%);
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
  display:flex;
  align-items:center;
  gap:10px;
  margin-bottom:6px;
}
.hero-icon{
  width:30px;
  height:30px;
  border-radius:10px;
  display:flex;
  align-items:center;
  justify-content:center;
  background:rgba(212,145,108,.18);
  border:1px solid rgba(212,145,108,.30);
  color:var(--gold);
  font-size:14px;
  flex:none;
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
  background:linear-gradient(135deg, rgba(212,145,108,.20), rgba(212,145,108,.12));
  border:1px solid rgba(212,145,108,.35);
  color:var(--gold);
  font-size:11px;
  font-weight:800;
  letter-spacing:.12em;
  white-space:nowrap;
  text-transform:uppercase;
}
.hero-badge::before{
  content:'';
  font-size:9px;
}
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
  grid-template-columns:repeat(2, minmax(0,1fr));
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
  content:'';
  position:absolute;
  top:0;
  left:0;
  right:0;
  height:2px;
  border-radius:18px 18px 0 0;
  opacity:.55;
}
.metric-card[data-tone="stable"]{
  border-color:rgba(212,145,108,.18);
  box-shadow:0 8px 32px rgba(0,0,0,.18), 0 0 0 0 var(--glow-stable);
}
.metric-card[data-tone="caution"]{
  border-color:rgba(212,145,108,.18);
  box-shadow:0 8px 32px rgba(0,0,0,.18), 0 0 0 0 var(--glow-caution);
}
.metric-card[data-tone="warning"]{
  border-color:rgba(212,145,108,.26);
  box-shadow:0 8px 32px rgba(0,0,0,.18), 0 0 0 0 var(--glow-warning);
}
.metric-card[data-tone="danger"]{
  border-color:rgba(212,145,108,.18);
  box-shadow:0 8px 32px rgba(0,0,0,.18), 0 0 0 0 var(--glow-danger);
}
.metric-card[data-tone="stable"]::before{background:var(--point)}
.metric-card[data-tone="caution"]::before{background:var(--point)}
.metric-card[data-tone="warning"]::before{background:var(--point)}
.metric-card[data-tone="danger"]::before{background:var(--point)}
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
.metric-card .card-bar{
  margin-top:auto;
  width:100%;
  height:3px;
  border-radius:999px;
  background:rgba(255,255,255,.06);
  overflow:hidden;
}
.metric-card .card-bar-fill{
  height:100%;
  border-radius:999px;
}
.metric-card[data-tone="stable"] .card-bar-fill{background:var(--stable);width:var(--score-w,50%)}
.metric-card[data-tone="caution"] .card-bar-fill{background:var(--caution);width:var(--score-w,50%)}
.metric-card[data-tone="warning"] .card-bar-fill{background:var(--warning);width:var(--score-w,50%)}
.metric-card[data-tone="danger"] .card-bar-fill{background:var(--danger);width:var(--score-w,50%)}
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
  content:'';
  position:absolute;
  top:0;
  left:0;
  right:0;
  height:2px;
  border-radius:18px 18px 0 0;
  opacity:.5;
}
.metric-bar[data-tone="stable"]{border-color:rgba(212,145,108,.18)}
.metric-bar[data-tone="caution"]{border-color:rgba(212,145,108,.18)}
.metric-bar[data-tone="warning"]{border-color:rgba(212,145,108,.22)}
.metric-bar[data-tone="danger"]{border-color:rgba(212,145,108,.18)}
.metric-bar[data-tone="stable"]::before{background:var(--point)}
.metric-bar[data-tone="caution"]::before{background:var(--point)}
.metric-bar[data-tone="warning"]::before{background:var(--point)}
.metric-bar[data-tone="danger"]::before{background:var(--point)}
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
.metric-bar[data-tone="stable"] .metric-bar-fill{background:linear-gradient(90deg, rgba(78,203,139,.30), var(--stable));color:var(--stable)}
.metric-bar[data-tone="caution"] .metric-bar-fill{background:linear-gradient(90deg, rgba(240,192,90,.30), var(--caution));color:var(--caution)}
.metric-bar[data-tone="warning"] .metric-bar-fill{background:linear-gradient(90deg, rgba(226,109,109,.28), var(--warning));color:var(--warning)}
.metric-bar[data-tone="danger"] .metric-bar-fill{background:linear-gradient(90deg, rgba(226,109,109,.28), var(--danger));color:var(--danger)}
.metric-bar-fill::after{
  content:'';
  position:absolute;
  right:-1px;
  top:50%;
  transform:translateY(-50%);
  width:12px;
  height:12px;
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
  width:3px;
  height:18px;
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
.content ul,
.content ol{
  margin:0 0 16px 4px;
  padding:0;
  list-style:none;
}
.content ul li,
.content ol li{
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
  left:2px;
  top:.75em;
  width:5px;
  height:5px;
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
.content strong{
  color:#fff;
  font-weight:700;
}
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
.section{
  margin-top:16px;
  border-radius:20px;
  padding:24px 22px;
  border:1px solid var(--line);
}
.s-teal{
  background:linear-gradient(145deg, rgba(212,145,108,.10) 0%, rgba(212,145,108,.04) 60%, rgba(11,17,32,0) 100%);
  border-color:rgba(212,145,108,.20);
}
.tag{
  display:inline-flex;
  align-items:center;
  gap:6px;
  font-size:11px;
  font-weight:700;
  letter-spacing:.10em;
  text-transform:uppercase;
  color:var(--gold);
  border:1px solid rgba(212,145,108,.22);
  border-radius:999px;
  padding:4px 12px;
  margin-bottom:12px;
}
.sec-title{
  margin:0 0 18px;
  font-size:20px;
  font-weight:800;
  line-height:1.3;
  color:#fff;
  letter-spacing:-.02em;
}
.contact-grid{
  display:grid;
  grid-template-columns:repeat(2, minmax(0,1fr));
  gap:12px;
}
.contact-card{
  background:rgba(255,255,255,.04);
  border:1px solid rgba(255,255,255,.08);
  border-radius:16px;
  padding:18px 16px;
  transition:background .2s;
}
.contact-card:hover{
  background:rgba(255,255,255,.07);
}
.c-num{margin-bottom:8px}
.c-phone{
  display:inline-block;
  font-size:24px;
  font-weight:800;
  line-height:1;
  color:#fff;
  letter-spacing:-.02em;
}
.c-label{
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
@media (max-width:680px){
  .wrap{padding:20px 14px calc(56px + env(safe-area-inset-bottom, 0))}
  .hero-top{
    flex-direction:column;
    align-items:flex-start;
  }
  .metrics-grid{grid-template-columns:1fr}
  .metric-card{min-height:auto}
  .metric-bar-head{align-items:center}
  .contact-grid{grid-template-columns:1fr}
  .content{padding:20px 16px 24px}
  .content h2{font-size:16px}
}
"""


HELP_SECTION_HTML = """
<div class="section s-teal">
  <h2 class="sec-title">혼자 버티기 힘들 때</h2>
  <div class="contact-grid">
    <div class="contact-card">
      <div class="c-num">
        <span class="c-phone">📞 117</span>
      </div>
      <div class="c-label">스토킹 피해<br>상담전화</div>
    </div>
    <div class="contact-card">
      <div class="c-num">
        <span class="c-phone">📞 1577-0199</span>
      </div>
      <div class="c-label">정신건강<br>위기상담전화</div>
    </div>
  </div>
</div>
""".strip()


def _short_summary(text: str) -> str:
    normalized = " ".join((text or "").split())
    if not normalized:
        return ""
    for separator in (". ", ".\n", "입니다. ", "니다. "):
        if separator in normalized:
            head = normalized.split(separator, 1)[0].strip()
            if head:
                return f"{head}."
    return normalized[:80].rstrip() + ("..." if len(normalized) > 80 else "")


def _render_metrics_html(metrics: dict | None) -> str:
    cards = []
    if isinstance(metrics, dict):
        cards = metrics.get("cards") or []

    if not cards:
        return ""

    card_map: dict[str, dict] = {}
    for card in cards:
        if isinstance(card, dict):
            card_id = str(card.get("id") or "").strip()
            if card_id:
                card_map[card_id] = card

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
    bar_title_overrides = {
        "recovery_conditions": "관계 회복 여건 지수",
        "emotional_stability": "현재 감정 안정도",
    }

    card_html = []
    for card_id in card_order:
        card = card_map.get(card_id)
        if not card:
            continue

        title = escape(str(card.get("title") or "").strip())
        value_text = escape(str(card.get("value_text") or "").strip())
        summary = escape(_short_summary(str(card.get("summary") or "").strip()))
        tone_raw = str(card.get("tone") or "caution").strip()
        tone = escape(tone_raw)
        score_value = max(0, min(100, int(card.get("score") or 0)))
        score = escape(str(score_value))

        card_html.append(
            f"""
      <section class="metric-card" data-tone="{tone}" data-metric-id="{escape(card_id)}">
        <div class="metric-title">{title}</div>
        <div class="metric-value-row">
          <div class="metric-value">{value_text}</div>
          <div class="metric-score">{score}</div>
        </div>
        <div class="metric-summary">{summary}</div>
        <div class="card-bar" aria-hidden="true">
          <div class="card-bar-fill" style="--score-w:{score_value}%;"></div>
        </div>
      </section>""".rstrip()
        )

    bar_html = []
    for card_id in bar_order:
        card = card_map.get(card_id)
        if not card:
            continue

        title = escape(bar_title_overrides.get(card_id, str(card.get("title") or "").strip()))
        value_text = escape(str(card.get("value_text") or "").strip())
        tone_raw = str(card.get("tone") or "caution").strip()
        tone = escape(tone_raw)
        score_value = max(0, min(100, int(card.get("score") or 0)))
        score = escape(str(score_value))
        fill_width = escape(str(score_value))

        bar_html.append(
            f"""
      <section class="metric-bar" data-tone="{tone}" data-metric-id="{escape(card_id)}">
        <div class="metric-bar-head">
          <div class="metric-bar-copy">
            <div class="metric-bar-title">{title}</div>
            <div class="metric-bar-state">{value_text}</div>
          </div>
          <div class="metric-bar-score">{score}</div>
        </div>
        <div class="metric-bar-track" aria-hidden="true">
          <div class="metric-bar-fill" style="width:{fill_width}%;"></div>
        </div>
      </section>""".rstrip()
        )

    if not card_html and not bar_html:
        return ""

    return f"""
    <section class="metrics-panel">
      <section class="metrics-grid">
        {''.join(card_html)}
      </section>
      <section class="bars">
        {''.join(bar_html)}
      </section>
    </section>
""".rstrip()


def render_premium_report_html(markdown_text: str, metrics: dict | None = None) -> str:
    md = (markdown_text or "").strip()
    if not md:
        raise ValueError("premium markdown is empty")

    body_html = markdown(
        md,
        extensions=["extra", "nl2br", "sane_lists"],
    )
    metrics_html = _render_metrics_html(metrics)

    html = f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>\ud504\ub9ac\ubbf8\uc5c4 \ub9ac\ud3ec\ud2b8</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap" rel="stylesheet" />
  <style>{PREMIUM_REPORT_CSS}</style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="hero-top">
        <div class="hero-title-wrap">
          <div class="hero-title-row">
            <div class="hero-icon">✦</div>
            <div class="hero-title">\uad00\uacc4 \uc9c4\ub2e8 \ub9ac\ud3ec\ud2b8</div>
          </div>
          <div class="hero-meta">\ubd84\uc11d \uc644\ub8cc &nbsp;&nbsp; \ub9ac\ucee4\ub125\ud2b8\ub7a9</div>
        </div>
        <div class="hero-badge">\ud504\ub9ac\ubbf8\uc5c4</div>
      </div>
      <div class="lead">
        \uad00\uacc4 \ud574\uc11d\ubcf4\ub2e4 \ud589\ub3d9 \uc548\uc815\ud654\uc640 \ub9ac\uc2a4\ud06c \uad00\ub9ac\uc5d0 \ucd08\uc810\uc744 \ub454 \uac1c\uc778 \ub9de\ucda4 \uac00\uc774\ub4dc
      </div>
    </section>

    {metrics_html}

    <main class="content">
      {body_html}
    </main>
"""
    html += HELP_SECTION_HTML
    html += """

    <div class="footer">
      \ubcf8 \ub9ac\ud3ec\ud2b8\ub294 \uac10\uc815 \uc790\uadf9\uc774 \uc544\ub2c8\ub77c \uc548\uc804 \uc911\uc2ec\uc758 \ud589\ub3d9 \uac00\uc774\ub4dc\ub97c \ubaa9\uc801\uc73c\ub85c \uc81c\uacf5\ud569\ub2c8\ub2e4.
    </div>
  </div>
</body>
</html>
"""
    return html
