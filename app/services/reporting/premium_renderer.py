# app/services/reporting/premium_renderer.py

from __future__ import annotations

from markdown import markdown


PREMIUM_REPORT_CSS = """
:root{
  --bg:#0F1626;
  --bg2:#1A2540;
  --card:#222E4A;
  --text:#F0ECE8;
  --sub:#9AAABB;
  --line:rgba(212,145,108,.18);
  --point:#D4916C;
}

*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{
  background:var(--bg);
  color:var(--text);
  font-family:'Noto Sans KR',sans-serif;
  line-height:1.75;
}
.wrap{
  max-width:820px;
  margin:0 auto;
  padding:28px 18px 56px;
}
.hero{
  background:linear-gradient(180deg, rgba(212,145,108,.14), rgba(212,145,108,.05));
  border:1px solid var(--line);
  border-radius:18px;
  padding:22px 20px;
  margin-bottom:16px;
}
.kicker{
  display:inline-block;
  font-size:12px;
  letter-spacing:.12em;
  color:var(--point);
  border:1px solid var(--line);
  border-radius:999px;
  padding:4px 10px;
  margin-bottom:10px;
}
h1{
  margin:0 0 6px;
  font-size:28px;
  line-height:1.35;
}
.lead{
  color:var(--sub);
  font-size:15px;
}
.content{
  background:var(--bg2);
  border:1px solid var(--line);
  border-radius:18px;
  padding:22px 20px;
}
.content h1{
  font-size:24px;
  margin:0 0 16px;
}
.content h2{
  font-size:20px;
  margin:28px 0 10px;
  padding-top:4px;
  border-top:1px solid var(--line);
}
.content h3{
  font-size:17px;
  margin:18px 0 8px;
}
.content p{
  margin:0 0 12px;
  color:var(--text);
}
.content ul,
.content ol{
  margin:0 0 14px 20px;
  padding:0;
}
.content li{
  margin:0 0 8px;
}
.content strong{
  color:#fff;
}
.content blockquote{
  margin:14px 0;
  padding:12px 14px;
  border-left:4px solid var(--point);
  background:rgba(255,255,255,.03);
  border-radius:10px;
}
.content hr{
  border:none;
  border-top:1px solid var(--line);
  margin:24px 0;
}
.footer{
  margin-top:16px;
  color:var(--sub);
  font-size:13px;
  text-align:center;
}
"""

def render_premium_report_html(markdown_text: str) -> str:
    md = (markdown_text or "").strip()
    if not md:
        raise ValueError("premium markdown is empty")

    body_html = markdown(
        md,
        extensions=["extra", "nl2br", "sane_lists"],
    )

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>리커넥트랩 프리미엄 리포트</title>
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;800&display=swap" rel="stylesheet" />
  <style>{PREMIUM_REPORT_CSS}</style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="kicker">PREMIUM REPORT</div>
      <h1>리커넥트랩 프리미엄 리포트</h1>
      <div class="lead">
        관계 해석보다 행동 안정화와 리스크 관리에 초점을 둔 개인 맞춤 가이드
      </div>
    </section>

    <main class="content">
      {body_html}
    </main>

    <div class="footer">
      본 리포트는 감정 자극이 아닌 안전 중심 행동 가이드를 목적으로 제공합니다.
    </div>
  </div>
</body>
</html>
"""