from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse

from .db import SessionLocal
from .models import Report, UserSession
from .report import make_report_html
from .services.premium_report import resolve_premium_state

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


def resolve_report_html(token: str) -> HTMLResponse | RedirectResponse:
    db = SessionLocal()
    try:
        rep, sess = load_report_and_session_by_token(token)
        state = resolve_premium_state(report_token=token, db=db)

        if state.state == "INVALID_REPORT_TOKEN":
            return HTMLResponse("<h1>Invalid report token</h1>", status_code=404)

        if state.state == "NEED_SURVEY" and state.next_url:
            return RedirectResponse(state.next_url, status_code=302)

        if state.state == "NOT_PAID":
            has_order = state.order_id is not None
            if has_order:
                return HTMLResponse("<h1>Payment required</h1>", status_code=403)

        if state.state == "READY" and (rep.html or "").strip():
            return HTMLResponse(rep.html)

        if state.state == "PROCESSING":
            return HTMLResponse("<h1>Premium report is processing</h1>", status_code=202)

        return HTMLResponse(
            make_report_html(
                risk_level=sess.risk_level,
                impulse=sess.impulse_index,
                fear_type=sess.fear_type,
            )
        )
    finally:
        db.close()


@router.get("/r/{token}", response_class=HTMLResponse)
async def view_report(token: str):
    return resolve_report_html(token)


@router.get("/report", response_class=HTMLResponse)
async def view_report_query(token: str = Query(...)):
    return resolve_report_html(token)
