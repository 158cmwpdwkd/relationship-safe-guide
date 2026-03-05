# app/routes_report.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from .db import SessionLocal
from .models import Report, UserSession
from .report import make_report_html

router = APIRouter()

def load_session_by_token(token: str) -> UserSession:
    db = SessionLocal()
    try:
        rep = db.query(Report).filter(Report.report_token == token).first()
        if not rep:
            raise HTTPException(status_code=404, detail="Invalid token")
        sess = db.query(UserSession).filter(UserSession.sid == rep.sid).first()
        if not sess:
            raise HTTPException(status_code=404, detail="Session not found")
        return sess
    finally:
        db.close()

@router.get("/r/{token}", response_class=HTMLResponse)
async def view_report(token: str):
    sess = load_session_by_token(token)
    html = make_report_html(
        risk_level=sess.risk_level,
        impulse=sess.impulse_index,
        fear_type=sess.fear_type,
    )
    return HTMLResponse(html)

@router.get("/report", response_class=HTMLResponse)
async def view_report_query(token: str = Query(...)):
    sess = load_session_by_token(token)
    html = make_report_html(
        risk_level=sess.risk_level,
        impulse=sess.impulse_index,
        fear_type=sess.fear_type,
    )
    return HTMLResponse(html)