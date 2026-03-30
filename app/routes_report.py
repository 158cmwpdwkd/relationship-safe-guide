import json

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse

from .db import SessionLocal
from .models import PremiumReport, Report, UserSession
from .report import make_report_html
from .services.reporting.premium_renderer import (
    render_premium_processing_html,
    render_premium_state_html,
)

router = APIRouter()


def log_kakao_alert(event: str, **payload) -> None:
    try:
        print(f"{event} {json.dumps(payload, ensure_ascii=False, default=str)}")
    except Exception:
        print(f"{event} {payload}")


def _load_free_report_by_token(*, token: str, db):
    report = db.query(Report).filter(Report.report_token == token).first()
    if not report:
        raise HTTPException(status_code=404, detail="INVALID_FREE_REPORT_TOKEN")

    session = db.query(UserSession).filter(UserSession.sid == report.sid).first()
    if not session:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")

    return report, session


def _load_premium_report_by_token(*, token: str, db) -> PremiumReport:
    premium_report = (
        db.query(PremiumReport)
        .filter(PremiumReport.premium_report_token == token)
        .first()
    )
    if not premium_report:
        raise HTTPException(status_code=404, detail="INVALID_PREMIUM_REPORT_TOKEN")
    return premium_report


def resolve_free_report_html(token: str) -> HTMLResponse:
    db = SessionLocal()
    try:
        report, session = _load_free_report_by_token(token=token, db=db)
        if report.free_kakao_sent_at is not None:
            log_kakao_alert(
                "solapi.alert.skip.already_sent",
                type="free",
                sid=report.sid,
                report_token=report.report_token,
                sent_at=report.free_kakao_sent_at,
            )
        return HTMLResponse(
            make_report_html(
                risk_level=session.risk_level,
                impulse=session.impulse_index,
                fear_type=session.fear_type,
            )
        )
    finally:
        db.close()


def resolve_premium_report_html(token: str) -> HTMLResponse:
    db = SessionLocal()
    try:
        premium_report = _load_premium_report_by_token(token=token, db=db)
        if premium_report.status == "READY" and (premium_report.html or "").strip():
            return HTMLResponse(premium_report.html)

        if premium_report.status == "FAILED":
            return HTMLResponse(
                render_premium_state_html(
                    state="FAILED",
                    title="프리미엄 리포트를 생성하지 못했습니다.",
                    message="잠시 후 다시 시도해주세요.",
                ),
                status_code=500,
            )

        return HTMLResponse(
            render_premium_processing_html(message="프리미엄 리포트를 생성 중입니다."),
            status_code=202,
        )
    finally:
        db.close()


@router.get("/r/{token}", response_class=HTMLResponse)
async def view_premium_report(token: str):
    return resolve_premium_report_html(token)


@router.get("/report", response_class=HTMLResponse)
async def view_free_report(token: str = Query(...)):
    return resolve_free_report_html(token)
