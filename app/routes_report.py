from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Order, PaidSurvey, Report, UserSession
from .report import make_report_html
from .services.premium_report import resolve_premium_state
from .services.reporting.premium_renderer import (
    render_premium_processing_html,
    render_premium_state_html,
)

router = APIRouter()
PAYMENT_FAIL_URL = "https://reconnectlab.co.kr/payment-fail"


def _is_free_report_token(token: str) -> bool:
    return (token or "").startswith("t_free_")


def load_report_and_session_by_token(token: str, db: Session):
    rep = db.query(Report).filter(Report.report_token == token).first()
    if not rep:
        raise HTTPException(status_code=404, detail="Invalid token")

    sess = db.query(UserSession).filter(UserSession.sid == rep.sid).first()
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    return rep, sess


def _is_premium_flow_token(*, token: str, report: Report, db: Session) -> bool:
    if _is_free_report_token(token):
        return False
    has_order = db.query(Order).filter(Order.sid == report.sid).first() is not None
    has_paid_survey = db.query(PaidSurvey).filter(PaidSurvey.sid == report.sid).first() is not None
    has_premium_content = bool((report.html or "").strip() or (report.markdown or "").strip())
    return has_order or has_paid_survey or has_premium_content


def resolve_report_html(token: str) -> HTMLResponse:
    db = SessionLocal()
    try:
        report, session = load_report_and_session_by_token(token, db)
        token_type = "free" if _is_free_report_token(token) else "premium"
        print(f"report.route.token_type token={token} token_type={token_type}")

        if _is_free_report_token(token):
            print(f"report.route.free_token_bypass_premium token={token}")
            return HTMLResponse(
                make_report_html(
                    risk_level=session.risk_level,
                    impulse=session.impulse_index,
                    fear_type=session.fear_type,
                )
            )

        state = resolve_premium_state(report_token=token, db=db)
        if state.state == "INVALID_REPORT_TOKEN":
            return HTMLResponse(
                render_premium_state_html(
                    state="INVALID_REPORT_TOKEN",
                    title="유효하지 않은 리포트 링크입니다",
                    message=state.user_message,
                    cta_label="홈으로 이동",
                    cta_href="/",
                ),
                status_code=404,
            )

        is_premium_flow = _is_premium_flow_token(token=token, report=report, db=db)
        print(f"report.route.premium_token_flow token={token} is_premium_flow={is_premium_flow}")

        if state.state == "READY" and (report.html or "").strip():
            return HTMLResponse(report.html)

        if is_premium_flow:
            if state.state == "PROCESSING":
                return HTMLResponse(
                    render_premium_processing_html(message=state.user_message),
                    status_code=202,
                )

            if state.state == "NOT_PAID":
                print(f"report.route.redirect_payment_fail token={token}")
                return RedirectResponse(
                    url=f"{PAYMENT_FAIL_URL}?reason=not_paid&report_token={token}",
                    status_code=302,
                )

            if state.state == "NEED_SURVEY":
                return HTMLResponse(
                    render_premium_state_html(
                        state="NEED_SURVEY",
                        title="유료 설문 작성이 필요합니다",
                        message=state.user_message,
                    ),
                    status_code=409,
                )

            return HTMLResponse(
                render_premium_processing_html(message=state.user_message),
                status_code=202,
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


@router.get("/r/{token}", response_class=HTMLResponse)
async def view_report(token: str):
    return resolve_report_html(token)


@router.get("/report", response_class=HTMLResponse)
async def view_report_query(token: str = Query(...)):
    return resolve_report_html(token)
