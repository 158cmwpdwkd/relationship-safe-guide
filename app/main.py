import json
from datetime import datetime, timedelta
import secrets

from fastapi import FastAPI, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine, get_db
from .models import UserSession, Order, PaidSurvey, Report, MessageSchedule
from .schemas import FreeSurveyIn, FreeSurveyOut, ConsentIn, PaidSurveyIn, GenerateIn, GenerateOut
from .risk import compute_risk
from .report import make_report_markdown, markdown_to_html, new_token, expiry_6_months

app = FastAPI(title="Relationship Safe Guide API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # MVP라 전체 허용 (배포 후 아임웹 도메인으로 제한 가능)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"ok": True}

@app.post("/api/free-survey", response_model=FreeSurveyOut)
def free_survey(payload: FreeSurveyIn, db: Session = Depends(get_db)):
    sid = secrets.token_hex(16)

    impulse, red_count, has_threat, level = compute_risk(
        payload.q1_score, payload.q2_score, payload.q3_score, payload.red_flags
    )

    s = UserSession(
        sid=sid,
        free_answers_json=json.dumps(payload.model_dump()),
        impulse_index=impulse,
        risk_level=level,
        fear_type=payload.fear_type,
        red_flags_json=json.dumps(payload.red_flags),
    )
    db.add(s)
    db.commit()

    return FreeSurveyOut(sid=sid, impulse_index=impulse, risk_level=level)

@app.post("/api/consent-and-contact")
def consent_and_contact(payload: ConsentIn, req: Request, db: Session = Depends(get_db)):
    s = db.get(UserSession, payload.sid)
    if not s:
        raise HTTPException(404, "sid not found")
    if not (payload.consent_collection_use and payload.consent_cross_border):
        raise HTTPException(400, "consent required")

    s.consent_collection_use = True
    s.consent_cross_border = True
    s.consent_version = payload.consent_version
    s.consent_at = datetime.utcnow()
    s.consent_ip = req.client.host if req.client else None
    s.consent_ua = req.headers.get("user-agent")

    s.phone = payload.phone
    s.email = payload.email

    db.add(s)
    db.commit()
    return {"ok": True}

@app.post("/api/payment/webhook")
def payment_webhook(payload: dict, db: Session = Depends(get_db)):
    """
    MVP에서는 실제 PG 연동 전이라서 'order_id'와 'sid'를 받아서 PAID로 바꾸는 정도만 둠.
    나중에 토스/PG 붙일 때 payload 검증 로직으로 교체.
    """
    order_id = payload.get("order_id")
    sid = payload.get("sid")
    status = payload.get("status")  # "PAID" etc.
    if not order_id or not sid:
        raise HTTPException(400, "order_id and sid required")

    o = db.get(Order, order_id)
    if not o:
        o = Order(order_id=order_id, sid=sid, status="PENDING", amount=9900)

    if status == "PAID":
        o.status = "PAID"
        o.paid_at = datetime.utcnow()

    o.pg_payload_json = json.dumps(payload)
    db.add(o)
    db.commit()
    return {"ok": True}

@app.post("/api/paid-survey")
def paid_survey(payload: PaidSurveyIn, db: Session = Depends(get_db)):
    o = db.get(Order, payload.order_id)
    if not o or o.status != "PAID":
        raise HTTPException(400, "order not paid")

    s = db.get(UserSession, payload.sid)
    if not s:
        raise HTTPException(404, "sid not found")

    p = PaidSurvey(sid=payload.sid, answers_json=json.dumps(payload.answers))
    db.merge(p)
    db.commit()
    return {"ok": True, "next": "GENERATE"}

@app.post("/api/report/generate", response_model=GenerateOut)
def generate_report(payload: GenerateIn, db: Session = Depends(get_db)):
    s = db.get(UserSession, payload.sid)
    if not s:
        raise HTTPException(404, "sid not found")

    # HARD_BLOCK이면 생성 금지
    if s.risk_level == "HARD_BLOCK":
        # Report 레코드만 남기고 BLOCKED 처리
        token = new_token()
        r = Report(
            sid=s.sid,
            status="BLOCKED",
            markdown=make_report_markdown("HARD_BLOCK", s.impulse_index, s.fear_type),
            html=markdown_to_html(make_report_markdown("HARD_BLOCK", s.impulse_index, s.fear_type)),
            report_token=token,
            generated_at=datetime.utcnow(),
            expires_at=expiry_6_months(),
        )
        db.merge(r)
        db.commit()
        return GenerateOut(status="BLOCKED", report_url=f"/r/{token}")

    # 이미 READY면 재사용
    existing = db.get(Report, s.sid)
    if existing and existing.status == "READY":
        return GenerateOut(status="READY", report_url=f"/r/{existing.report_token}")

    token = new_token()
    md_text = make_report_markdown(s.risk_level, s.impulse_index, s.fear_type)
    html = markdown_to_html(md_text)

    r = Report(
        sid=s.sid,
        status="READY",
        markdown=md_text,
        html=html,
        report_token=token,
        generated_at=datetime.utcnow(),
        expires_at=expiry_6_months(),
    )
    db.merge(r)

    # 알림 예약: 72h, 14d (UTC 기준)
    now = datetime.utcnow()
    m1 = MessageSchedule(
        id=secrets.token_hex(16), sid=s.sid, type="CHECK_72H",
        send_at=now + timedelta(hours=72), status="PENDING", attempts=0
    )
    m2 = MessageSchedule(
        id=secrets.token_hex(16), sid=s.sid, type="CHECK_14D",
        send_at=now + timedelta(days=14), status="PENDING", attempts=0
    )
    db.add(m1); db.add(m2)

    db.commit()
    return GenerateOut(status="READY", report_url=f"/r/{token}")

@app.get("/r/{token}", response_class=HTMLResponse)
def view_report(token: str, db: Session = Depends(get_db)):
    q = select(Report).where(Report.report_token == token)
    r = db.execute(q).scalar_one_or_none()

    if not r:
        raise HTTPException(404, "report not found")
    if r.expires_at and datetime.utcnow() > r.expires_at:
        raise HTTPException(410, "report expired")

    html = f"""<!doctype html>
<html lang="ko">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>관계 안전 가이드</title>
  </head>
  <body style="max-width:720px;margin:0 auto;padding:20px;font-family:system-ui;line-height:1.7">
    {r.html}

    <script>
      (function () {{
        function sendHeight() {{
          var h = Math.max(
            document.body.scrollHeight,
            document.documentElement.scrollHeight
          );
          parent.postMessage({{ type: "RCL_REPORT_HEIGHT", height: h }}, "*");
        }}
        window.addEventListener("load", sendHeight);
        window.addEventListener("resize", sendHeight);
        setTimeout(sendHeight, 300);
        setTimeout(sendHeight, 1200);
      }})();
    </script>

  </body>
</html>
"""
    return HTMLResponse(content=html, status_code=200)