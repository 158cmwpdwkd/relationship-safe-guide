import json
from datetime import UTC, datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Order, PaidSurvey, PremiumReport, UserSession
from app.report import new_token
from app.schemas import PremiumEntryOut, PremiumStateOut, SurveySubmitOut
from app.services.interpretation.schemas import EngineInput, PaidSurveyAnswers
from app.services.reporting.llm_client import PremiumLLMError
from app.services.reporting.premium_pipeline import (
    finalize_premium_report_record,
    generate_premium_report_artifacts,
    prepare_premium_report_payload,
)

PAYMENT_FAIL_PATH = "/payment-fail"


def _premium_token() -> str:
    return "t_premium_" + new_token()


def _get_order(*, order_id: str, db: Session) -> Order | None:
    return db.query(Order).filter(Order.order_id == order_id).first()


def _get_session_or_raise(*, sid: str, db: Session) -> UserSession:
    session = db.query(UserSession).filter(UserSession.sid == sid).first()
    if not session:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")
    return session


def _get_paid_survey(*, order_id: str, db: Session) -> PaidSurvey | None:
    return db.query(PaidSurvey).filter(PaidSurvey.order_id == order_id).first()


def _get_premium_report(*, order_id: str, db: Session) -> PremiumReport | None:
    return db.query(PremiumReport).filter(PremiumReport.order_id == order_id).first()


def get_premium_report_by_token(*, premium_report_token: str, db: Session) -> PremiumReport | None:
    return (
        db.query(PremiumReport)
        .filter(PremiumReport.premium_report_token == premium_report_token)
        .first()
    )


def _ensure_premium_report(*, order: Order, db: Session) -> PremiumReport:
    premium_report = _get_premium_report(order_id=order.order_id, db=db)
    if premium_report:
        return premium_report

    premium_report = PremiumReport(
        order_id=order.order_id,
        sid=order.sid,
        free_report_token=order.free_report_token,
        premium_report_token=_premium_token(),
        status="GENERATING",
    )
    db.add(premium_report)
    db.commit()
    db.refresh(premium_report)
    return premium_report


def _load_paid_answers_or_raise(*, order_id: str, db: Session) -> PaidSurveyAnswers:
    paid = _get_paid_survey(order_id=order_id, db=db)
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
    order: Order,
    session: UserSession,
    paid_answers: PaidSurveyAnswers,
) -> EngineInput:
    try:
        free_answers = json.loads(session.free_answers_json or "{}")
    except Exception:
        free_answers = {}

    return EngineInput(
        sid=order.sid,
        order_id=order.order_id,
        report_token=order.free_report_token or "",
        free_risk_level=session.risk_level or "LOW",
        free_impulse_index=session.impulse_index,
        free_answers=free_answers,
        paid_answers=paid_answers,
    )


def resolve_premium_state(*, order_id: str, db: Session) -> PremiumStateOut:
    order = _get_order(order_id=order_id, db=db)
    if not order:
        return PremiumStateOut(
            state="ORDER_NOT_FOUND",
            order_id=order_id,
            next_action="SHOW_ERROR",
            next_url=None,
            user_message="주문 정보를 찾을 수 없습니다.",
        )

    if order.status != "PAID":
        return PremiumStateOut(
            state="NOT_PAID",
            sid=order.sid,
            order_id=order.order_id,
            free_report_token=order.free_report_token,
            next_action="GO_PAYMENT",
            next_url=f"{PAYMENT_FAIL_PATH}?reason=not_paid&orderId={order.order_id}",
            user_message="결제가 완료된 주문만 이용할 수 있습니다.",
        )

    paid = _get_paid_survey(order_id=order.order_id, db=db)
    premium_report = _get_premium_report(order_id=order.order_id, db=db)

    if not paid:
        return PremiumStateOut(
            state="NEED_SURVEY",
            sid=order.sid,
            order_id=order.order_id,
            free_report_token=order.free_report_token,
            premium_report_token=(
                premium_report.premium_report_token if premium_report else None
            ),
            next_action="GO_SURVEY",
            next_url=f"/premium-survey?orderId={order.order_id}",
            user_message="유료 설문 작성이 필요합니다.",
        )

    if premium_report and premium_report.status == "READY" and (premium_report.html or "").strip():
        return PremiumStateOut(
            state="READY",
            sid=order.sid,
            order_id=order.order_id,
            free_report_token=order.free_report_token,
            premium_report_token=premium_report.premium_report_token,
            report_url=f"/r/{premium_report.premium_report_token}",
            next_action="OPEN_REPORT",
            next_url=f"/r/{premium_report.premium_report_token}",
            user_message="프리미엄 리포트가 준비되었습니다.",
            has_paid_survey=True,
            has_report_html=True,
            has_report_markdown=bool((premium_report.markdown or "").strip()),
        )

    return PremiumStateOut(
        state="PROCESSING",
        sid=order.sid,
        order_id=order.order_id,
        free_report_token=order.free_report_token,
        premium_report_token=(premium_report.premium_report_token if premium_report else None),
        report_url=(
            f"/r/{premium_report.premium_report_token}"
            if premium_report and premium_report.premium_report_token
            else None
        ),
        next_action="POLL_STATUS",
        next_url=f"/api/premium/report/status?order_id={order.order_id}",
        user_message="프리미엄 리포트를 생성 중입니다.",
        has_paid_survey=True,
        has_report_html=bool(premium_report and (premium_report.html or "").strip()),
        has_report_markdown=bool(premium_report and (premium_report.markdown or "").strip()),
    )


def _get_validated_context(*, order_id: str, db: Session):
    state = resolve_premium_state(order_id=order_id, db=db)
    if state.state == "ORDER_NOT_FOUND":
        raise HTTPException(status_code=404, detail="ORDER_NOT_FOUND")
    if state.state == "NOT_PAID":
        raise HTTPException(status_code=403, detail="NOT_PAID")

    order = _get_order(order_id=order_id, db=db)
    session = _get_session_or_raise(sid=order.sid, db=db)
    paid = _get_paid_survey(order_id=order.order_id, db=db)
    premium_report = _get_premium_report(order_id=order.order_id, db=db)
    return order, session, paid, premium_report, state


def build_entry_response(*, order_id: str, db: Session) -> PremiumEntryOut:
    state = resolve_premium_state(order_id=order_id, db=db)
    return PremiumEntryOut(
        ok=True,
        state=state.state,
        sid=state.sid,
        order_id=state.order_id,
        free_report_token=state.free_report_token,
        premium_report_token=state.premium_report_token,
        next_action=state.next_action,
        next_url=state.next_url,
        user_message=state.user_message,
        report_url=state.report_url,
    )


def prepare_premium_preview_or_raise(*, order_id: str, db: Session):
    order, session, paid, premium_report, _ = _get_validated_context(order_id=order_id, db=db)
    if not paid:
        raise HTTPException(status_code=404, detail="PAID_SURVEY_NOT_FOUND")

    paid_answers = _load_paid_answers_or_raise(order_id=order.order_id, db=db)
    engine_input = _build_engine_input(
        order=order,
        session=session,
        paid_answers=paid_answers,
    )
    preview = prepare_premium_report_payload(engine_input)
    return order, session, paid, premium_report, preview


def run_premium_pipeline(
    *,
    order_id: str,
    db: Session,
    overwrite: bool = False,
):
    order, _, _, premium_report, preview = prepare_premium_preview_or_raise(
        order_id=order_id,
        db=db,
    )
    premium_report = premium_report or _ensure_premium_report(order=order, db=db)

    existing_html = (premium_report.html or "").strip()
    existing_markdown = (premium_report.markdown or "").strip()
    if (
        not overwrite
        and premium_report.status == "READY"
        and existing_html
        and existing_markdown
    ):
        return premium_report, resolve_premium_state(order_id=order_id, db=db), preview, True

    try:
        artifacts = generate_premium_report_artifacts(
            prompt=preview["prompt"],
            metrics=preview["metrics"],
        )
        premium_report.updated_at = datetime.utcnow()
        finalize_premium_report_record(
            report=premium_report,
            markdown_text=artifacts["markdown"],
            html_text=artifacts["html"],
            db=db,
            overwrite=True,
        )
        premium_report.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(premium_report)
    except PremiumLLMError as e:
        db.rollback()
        failed = _get_premium_report(order_id=order_id, db=db)
        if failed:
            failed.status = "FAILED"
            failed.updated_at = datetime.utcnow()
            db.commit()
        raise HTTPException(status_code=502, detail=f"LLM_CALL_FAILED: {e}")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        failed = _get_premium_report(order_id=order_id, db=db)
        if failed:
            failed.status = "FAILED"
            failed.updated_at = datetime.utcnow()
            db.commit()
        raise HTTPException(status_code=500, detail=f"PREMIUM_REPORT_FINALIZE_FAILED: {e}")

    return premium_report, resolve_premium_state(order_id=order_id, db=db), preview, False


def submit_paid_survey(
    *,
    order_id: str,
    answers: PaidSurveyAnswers,
    submitted_at: datetime | None,
    db: Session,
) -> SurveySubmitOut:
    order, _, paid, premium_report, _ = _get_validated_context(order_id=order_id, db=db)

    payload_json = json.dumps(answers.model_dump(mode="json"), ensure_ascii=False)
    saved_at = submitted_at or datetime.now(UTC)

    if paid:
        paid.answers_json = payload_json
        paid.submitted_at = saved_at
        saved = True
    else:
        paid = PaidSurvey(
            order_id=order.order_id,
            sid=order.sid,
            answers_json=payload_json,
            submitted_at=saved_at,
        )
        db.add(paid)
        saved = True

    order.updated_at = datetime.utcnow()
    db.commit()

    state = resolve_premium_state(order_id=order_id, db=db)
    return SurveySubmitOut(
        ok=True,
        sid=order.sid,
        saved=saved,
        next="OPEN_REPORT" if premium_report and premium_report.premium_report_token else "GENERATE_REPORT",
        order_id=order.order_id,
        free_report_token=order.free_report_token,
        premium_report_token=(premium_report.premium_report_token if premium_report else None),
        state=state.state,
        next_action=state.next_action,
        next_url=state.next_url,
        user_message="유료 설문이 저장되었습니다.",
        report_url=state.report_url,
    )
