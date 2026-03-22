import json
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Order, PaidSurvey, Report, UserSession
from app.schemas import PremiumEntryOut, PremiumStateOut, SurveySubmitOut
from app.services.interpretation.schemas import EngineInput, PaidSurveyAnswers
from app.services.reporting.llm_client import PremiumLLMError
from app.services.reporting.premium_pipeline import (
    finalize_premium_report_record,
    generate_premium_report_artifacts,
    prepare_premium_report_payload,
)

PAYMENT_FAIL_PATH = "/payment-fail"


def _get_report_by_token(*, report_token: str, db: Session) -> Report | None:
    return db.query(Report).filter(Report.report_token == report_token).first()


def _get_order_by_id(*, order_id: str, db: Session) -> Order | None:
    return db.query(Order).filter(Order.order_id == order_id).first()


def _get_preferred_order_for_sid(*, sid: str, db: Session) -> Order | None:
    paid_order = (
        db.query(Order)
        .filter(Order.sid == sid, Order.status == "PAID")
        .order_by(Order.paid_at.desc(), Order.order_id.desc())
        .first()
    )
    if paid_order:
        return paid_order

    return (
        db.query(Order)
        .filter(Order.sid == sid)
        .order_by(Order.paid_at.desc(), Order.order_id.desc())
        .first()
    )


def _get_session_or_raise(*, sid: str, db: Session) -> UserSession:
    session = db.query(UserSession).filter(UserSession.sid == sid).first()
    if not session:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    return session


def _get_paid_survey(*, sid: str, db: Session) -> PaidSurvey | None:
    return db.query(PaidSurvey).filter(PaidSurvey.sid == sid).first()


def _load_paid_answers_or_raise(*, sid: str, db: Session) -> PaidSurveyAnswers:
    paid = _get_paid_survey(sid=sid, db=db)
    if not paid:
        raise HTTPException(status_code=404, detail="PAID_SURVEY_NOT_FOUND")

    try:
        paid_answers_raw = json.loads(paid.answers_json or "{}")
    except Exception:
        raise HTTPException(status_code=500, detail="INVALID_PAID_SURVEY_JSON")

    try:
        return PaidSurveyAnswers(**paid_answers_raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"INVALID_PAID_SURVEY_SCHEMA: {e}")


def _build_engine_input(
    *,
    sid: str,
    order_id: str,
    report_token: str,
    session: UserSession,
    paid_answers: PaidSurveyAnswers,
) -> EngineInput:
    try:
        free_answers = json.loads(session.free_answers_json or "{}")
    except Exception:
        free_answers = {}

    return EngineInput(
        sid=sid,
        order_id=order_id,
        report_token=report_token,
        free_risk_level=session.risk_level or "LOW",
        free_impulse_index=session.impulse_index,
        free_answers=free_answers,
        paid_answers=paid_answers,
    )


def resolve_premium_state(
    *,
    report_token: str,
    order_id: str | None = None,
    db: Session,
) -> PremiumStateOut:
    report = _get_report_by_token(report_token=report_token, db=db)
    if not report:
        return PremiumStateOut(
            state="INVALID_REPORT_TOKEN",
            report_token=report_token,
            next_action="SHOW_ERROR",
            next_url=None,
            user_message="유효하지 않은 리포트 토큰입니다.",
        )

    order = None
    if order_id:
        order = _get_order_by_id(order_id=order_id, db=db)
        if order and order.sid != report.sid:
            return PremiumStateOut(
                state="REPORT_ORDER_MISMATCH",
                sid=report.sid,
                order_id=order_id,
                report_token=report_token,
                report_url=f"/r/{report_token}",
                next_action="SHOW_ERROR",
                next_url=None,
                user_message="주문 정보와 리포트가 일치하지 않습니다.",
            )
    else:
        order = _get_preferred_order_for_sid(sid=report.sid, db=db)

    if not order or order.status != "PAID":
        return PremiumStateOut(
            state="NOT_PAID",
            sid=report.sid,
            order_id=order.order_id if order else order_id,
            report_token=report_token,
            report_url=f"/r/{report_token}",
            next_action="SHOW_ERROR",
            next_url=f"{PAYMENT_FAIL_PATH}?reason=not_paid&report_token={report_token}",
            user_message="결제가 필요합니다.",
        )

    paid = _get_paid_survey(sid=report.sid, db=db)
    if not paid:
        return PremiumStateOut(
            state="NEED_SURVEY",
            sid=report.sid,
            order_id=order.order_id,
            report_token=report_token,
            report_url=f"/r/{report_token}",
            next_action="GO_SURVEY",
            next_url=f"/premium-survey?token={report_token}&orderId={order.order_id}",
            user_message="유료 설문 작성이 필요합니다.",
        )

    has_html = bool((report.html or "").strip())
    has_markdown = bool((report.markdown or "").strip())
    if report.status == "READY" and has_html and has_markdown:
        return PremiumStateOut(
            state="READY",
            sid=report.sid,
            order_id=order.order_id,
            report_token=report_token,
            report_url=f"/r/{report_token}",
            next_action="OPEN_REPORT",
            next_url=f"/r/{report_token}",
            user_message="프리미엄 리포트가 준비되었습니다.",
            has_paid_survey=True,
            has_report_html=has_html,
            has_report_markdown=has_markdown,
        )

    return PremiumStateOut(
        state="PROCESSING",
        sid=report.sid,
        order_id=order.order_id,
        report_token=report_token,
        report_url=f"/r/{report_token}",
        next_action="POLL_STATUS",
        next_url=(
            f"/api/premium/report/status?sid={report.sid}"
            f"&order_id={order.order_id}&report_token={report_token}"
        ),
        user_message="프리미엄 리포트를 생성 중입니다.",
        has_paid_survey=True,
        has_report_html=has_html,
        has_report_markdown=has_markdown,
    )


def _get_validated_context(
    *,
    report_token: str,
    order_id: str,
    db: Session,
):
    state = resolve_premium_state(report_token=report_token, order_id=order_id, db=db)
    if state.state == "INVALID_REPORT_TOKEN":
        raise HTTPException(status_code=404, detail="INVALID_REPORT_TOKEN")
    if state.state == "REPORT_ORDER_MISMATCH":
        raise HTTPException(status_code=400, detail="REPORT_ORDER_MISMATCH")
    if state.state == "NOT_PAID":
        raise HTTPException(status_code=403, detail="NOT_PAID")

    report = _get_report_by_token(report_token=report_token, db=db)
    order = _get_order_by_id(order_id=order_id, db=db)
    session = _get_session_or_raise(sid=report.sid, db=db)
    paid = _get_paid_survey(sid=report.sid, db=db)
    return report, order, session, paid, state


def build_entry_response(
    *,
    report_token: str,
    order_id: str | None,
    db: Session,
) -> PremiumEntryOut:
    state = resolve_premium_state(report_token=report_token, order_id=order_id, db=db)
    return PremiumEntryOut(
        ok=True,
        state=state.state,
        sid=state.sid,
        order_id=state.order_id,
        report_token=state.report_token,
        next_action=state.next_action,
        next_url=state.next_url,
        user_message=state.user_message,
        report_url=state.report_url,
    )


def prepare_premium_preview_or_raise(
    *,
    report_token: str,
    order_id: str,
    db: Session,
):
    report, order, session, paid, _ = _get_validated_context(
        report_token=report_token,
        order_id=order_id,
        db=db,
    )
    if not paid:
        raise HTTPException(status_code=404, detail="PAID_SURVEY_NOT_FOUND")

    paid_answers = _load_paid_answers_or_raise(sid=report.sid, db=db)
    engine_input = _build_engine_input(
        sid=report.sid,
        order_id=order.order_id,
        report_token=report.report_token,
        session=session,
        paid_answers=paid_answers,
    )
    preview = prepare_premium_report_payload(engine_input)
    return report, order, session, preview


def run_premium_pipeline(
    *,
    report_token: str,
    order_id: str,
    db: Session,
    overwrite: bool = True,
) -> PremiumStateOut:
    report, order, _, preview = prepare_premium_preview_or_raise(
        report_token=report_token,
        order_id=order_id,
        db=db,
    )

    existing_html = (report.html or "").strip()
    existing_markdown = (report.markdown or "").strip()
    if (
        not overwrite
        and report.status == "READY"
        and existing_html
        and existing_markdown
    ):
        return resolve_premium_state(report_token=report_token, order_id=order_id, db=db)

    try:
        artifacts = generate_premium_report_artifacts(
            prompt=preview["prompt"],
            metrics=preview["metrics"],
        )
        finalize_premium_report_record(
            report=report,
            markdown_text=artifacts["markdown"],
            html_text=artifacts["html"],
            db=db,
            overwrite=overwrite,
        )
    except PremiumLLMError as e:
        db.rollback()
        failed = _get_report_by_token(report_token=report_token, db=db)
        if failed:
            failed.status = "FAILED"
            db.commit()
        raise HTTPException(status_code=502, detail=f"LLM_CALL_FAILED: {e}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        failed = _get_report_by_token(report_token=report_token, db=db)
        if failed:
            failed.status = "FAILED"
            db.commit()
        raise HTTPException(status_code=500, detail=f"PREMIUM_REPORT_FINALIZE_FAILED: {e}")

    return resolve_premium_state(report_token=report_token, order_id=order_id, db=db)


def submit_paid_survey_and_run_pipeline(
    *,
    report_token: str,
    order_id: str,
    answers: PaidSurveyAnswers,
    submitted_at: datetime | None,
    db: Session,
) -> SurveySubmitOut:
    report, order, _, paid, _ = _get_validated_context(
        report_token=report_token,
        order_id=order_id,
        db=db,
    )

    payload_json = json.dumps(answers.model_dump(mode="json"), ensure_ascii=False)
    saved_at = submitted_at or datetime.now(UTC)

    if paid:
        paid.answers_json = payload_json
        paid.submitted_at = saved_at
        saved = True
    else:
        paid = PaidSurvey(
            sid=report.sid,
            answers_json=payload_json,
            submitted_at=saved_at,
        )
        db.add(paid)
        saved = True

    db.commit()

    final_state = run_premium_pipeline(
        report_token=report_token,
        order_id=order_id,
        db=db,
        overwrite=True,
    )

    next_value = "OPEN_REPORT" if final_state.state == "READY" else "POLL_STATUS"
    return SurveySubmitOut(
        ok=True,
        sid=report.sid,
        saved=saved,
        next=next_value,
        order_id=order.order_id,
        report_token=report.report_token,
        state=final_state.state,
        next_action=final_state.next_action,
        next_url=final_state.next_url,
        user_message=final_state.user_message,
        report_url=final_state.report_url,
    )
