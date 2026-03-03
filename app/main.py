import json
from datetime import datetime, timedelta
import secrets

from fastapi import FastAPI, Depends, Request, HTTPException, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import select
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from .db import Base, engine, get_db
from .models import UserSession, Order, PaidSurvey, Report, MessageSchedule
from .schemas import FreeSurveyIn, FreeSurveyOut, ConsentIn, PaidSurveyIn, GenerateIn, GenerateOut
from .risk import compute_risk
from .report import make_report_html, make_report_markdown, new_token, expiry_6_months

app = FastAPI(title="Relationship Safe Guide API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    s.consent_cross_border    = True
    s.consent_version         = payload.consent_version
    s.consent_at              = datetime.utcnow()
    s.consent_ip              = req.client.host if req.client else None
    s.consent_ua              = req.headers.get("user-agent")
    s.phone                   = payload.phone
    s.email                   = payload.email
    db.add(s)
    db.commit()
    return {"ok": True}


@app.post("/api/payment/webhook")
def payment_webhook(payload: dict, db: Session = Depends(get_db)):
    order_id = payload.get("order_id")
    sid      = payload.get("sid")
    status   = payload.get("status")
    if not order_id or not sid:
        raise HTTPException(400, "order_id and sid required")
    o = db.get(Order, order_id)
    if not o:
        o = Order(order_id=order_id, sid=sid, status="PENDING", amount=29000)
    if status == "PAID":
        o.status  = "PAID"
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

    if s.risk_level == "HARD_BLOCK":
        token = new_token()
        r = Report(
            sid=s.sid,
            status="BLOCKED",
            markdown=make_report_markdown("HARD_BLOCK", s.impulse_index, s.fear_type),
            html=make_report_html("HARD_BLOCK", s.impulse_index, s.fear_type),
            report_token=token,
            generated_at=datetime.utcnow(),
            expires_at=expiry_6_months(),
        )
        db.merge(r)
        db.commit()
        return GenerateOut(status="BLOCKED", report_url=f"/r/{token}")

    existing = db.get(Report, s.sid)
    if existing and existing.status == "READY":
        return GenerateOut(status="READY", report_url=f"/r/{existing.report_token}")

    token = new_token()
    r = Report(
        sid=s.sid,
        status="READY",
        markdown=make_report_markdown(s.risk_level, s.impulse_index, s.fear_type),
        html=make_report_html(s.risk_level, s.impulse_index, s.fear_type),
        report_token=token,
        generated_at=datetime.utcnow(),
        expires_at=expiry_6_months(),
    )
    db.merge(r)

    now = datetime.utcnow()
    db.add(MessageSchedule(
        id=secrets.token_hex(16), sid=s.sid, type="CHECK_72H",
        send_at=now + timedelta(hours=72), status="PENDING", attempts=0
    ))
    db.add(MessageSchedule(
        id=secrets.token_hex(16), sid=s.sid, type="CHECK_14D",
        send_at=now + timedelta(days=14), status="PENDING", attempts=0
    ))
    db.commit()
    return GenerateOut(status="READY", report_url=f"/r/{token}")


@app.get("/r/{token}", response_class=HTMLResponse)
def view_report(token: str, db: Session = Depends(get_db)):
    r = db.execute(
        select(Report).where(Report.report_token == token)
    ).scalar_one_or_none()

    if not r:
        raise HTTPException(404, "리포트를 찾을 수 없습니다")
    if r.expires_at and datetime.utcnow() > r.expires_at:
        raise HTTPException(410, "만료된 리포트입니다")

    # 항상 세션 데이터로 실시간 렌더링 → 구형 토큰도 새 디자인 자동 적용
    session = db.get(UserSession, r.sid)
    if session and session.risk_level:
        return HTMLResponse(
            content=make_report_html(
                session.risk_level,
                session.impulse_index or 0,
                session.fear_type or "other"
            )
        )

    if r.html and r.html.strip().startswith("<!DOCTYPE html"):
        return HTMLResponse(content=r.html)

    return HTMLResponse(content=make_report_html("MEDIUM", 0, "other"))


router = APIRouter()

@router.post("/admin/init-db")
def init_db():
    Base.metadata.create_all(bind=engine)
    return {"ok": True}

app.include_router(router)