# app/routes_report.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from .db import SessionLocal
from .models import Report, UserSession
from .report import make_report_html

router = APIRouter()


def load_report_and_session_by_token(token: str):
    db = SessionLocal()
    try:
        rep = db.query(Report).filter(Report.report_token == token).first()
        if not rep:
            raise HTTPException(status_code=404, detail="Invalid token")

        sess = db.query(UserSession).filter(UserSession.sid == rep.sid).first()
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")

        return rep, sess
    finally:
        db.close()


def resolve_report_html(token: str) -> str:
    rep, sess = load_report_and_session_by_token(token)

    # premium 저장본이 있으면 우선 사용
    if rep.status == "READY" and (rep.html or "").strip():
        return rep.html

    # 없으면 기존 무료 리포트 폴백
    return make_report_html(
        risk_level=sess.risk_level,
        impulse=sess.impulse_index,
        fear_type=sess.fear_type,
    )


@router.get("/r/{token}", response_class=HTMLResponse)
async def view_report(token: str):
    return HTMLResponse(resolve_report_html(token))


@router.get("/report", response_class=HTMLResponse)
async def view_report_query(token: str = Query(...)):
    return HTMLResponse(resolve_report_html(token))