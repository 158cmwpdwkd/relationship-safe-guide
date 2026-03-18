# app/routes_premium.py

import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Order, PaidSurvey, Report, UserSession
from .schemas import (
    PaidSurveySaveOut,
    PremiumReportFinalizeIn,
    PremiumReportFinalizeOut,
    PremiumReportGenerateIn,
    PremiumReportGenerateOut,
    PremiumReportStatusOut,
)
from .services.interpretation.schemas import (
    EngineInput,
    PaidSurveyAnswers,
    PaidSurveyRequest,
)
from .services.reporting.llm_client import PremiumLLMError, generate_premium_markdown
from .services.reporting.premium_pipeline import prepare_premium_report_payload
from .services.reporting.premium_renderer import render_premium_report_html

router = APIRouter(prefix="/api/premium", tags=["premium"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _get_report_order_session_or_raise(
    *,
    token: str,
    order_id: str,
    db: Session,
):
    report = db.query(Report).filter(Report.report_token == token).first()
    if not report:
        raise HTTPException(status_code=404, detail="INVALID_REPORT_TOKEN")

    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="ORDER_NOT_FOUND")

    if order.status != "PAID":
        raise HTTPException(status_code=403, detail="NOT_PAID")

    if report.sid != order.sid:
        raise HTTPException(status_code=400, detail="REPORT_ORDER_MISMATCH")

    session = db.query(UserSession).filter(UserSession.sid == report.sid).first()
    if not session:
        raise HTTPException(status_code=404, detail="SESSION_NOT_FOUND")

    return report, order, session


def _load_paid_answers_or_raise(*, sid: str, db: Session) -> PaidSurveyAnswers:
    paid = db.query(PaidSurvey).filter(PaidSurvey.sid == sid).first()
    if not paid:
        raise HTTPException(status_code=404, detail="PAID_SURVEY_NOT_FOUND")

    try:
        paid_answers_raw = json.loads(paid.answers_json or "{}")
    except Exception:
        raise HTTPException(status_code=500, detail="INVALID_PAID_SURVEY_JSON")

    try:
        paid_answers = PaidSurveyAnswers(**paid_answers_raw)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"INVALID_PAID_SURVEY_SCHEMA: {e}")

    return paid_answers


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


def _prepare_preview_result(
    *,
    sid: str,
    order_id: str,
    report_token: str,
    session: UserSession,
    db: Session,
):
    paid_answers = _load_paid_answers_or_raise(sid=sid, db=db)
    engine_input = _build_engine_input(
        sid=sid,
        order_id=order_id,
        report_token=report_token,
        session=session,
        paid_answers=paid_answers,
    )
    return prepare_premium_report_payload(engine_input)


@router.get("/access-check")
def premium_access_check(
    token: str = Query(...),
    orderId: str = Query(...),
    db: Session = Depends(get_db),
):
    report = db.query(Report).filter(Report.report_token == token).first()

    if not report:
        return {"ok": False, "reason": "INVALID_REPORT_TOKEN"}

    order = db.query(Order).filter(Order.order_id == orderId).first()

    if not order:
        return {"ok": False, "reason": "ORDER_NOT_FOUND"}

    if order.sid != report.sid:
        return {"ok": False, "reason": "SID_MISMATCH"}

    if order.status != "PAID":
        return {"ok": False, "reason": "NOT_PAID"}

    return {"ok": True}


@router.post("/survey/paid", response_model=PaidSurveySaveOut)
def submit_paid_survey(
    payload: PaidSurveyRequest,
    db: Session = Depends(get_db),
):
    report, order, session = _get_report_order_session_or_raise(
        token=payload.report_token,
        order_id=payload.order_id,
        db=db,
    )

    resolved_sid = report.sid
    answers_dict = payload.answers.model_dump(mode="json")
    submitted_at = payload.submitted_at or datetime.utcnow()

    paid = db.query(PaidSurvey).filter(PaidSurvey.sid == resolved_sid).first()

    if paid:
        paid.answers_json = json.dumps(answers_dict, ensure_ascii=False)
        paid.submitted_at = submitted_at
        saved = True
    else:
        paid = PaidSurvey(
            sid=resolved_sid,
            answers_json=json.dumps(answers_dict, ensure_ascii=False),
            submitted_at=submitted_at,
        )
        db.add(paid)
        saved = True

    db.commit()

    return PaidSurveySaveOut(
        ok=True,
        sid=resolved_sid,
        saved=saved,
        next="GENERATE_REPORT",
    )


@router.post("/report/generate", response_model=PremiumReportGenerateOut)
def generate_premium_report_payload(
    payload: PremiumReportGenerateIn,
    db: Session = Depends(get_db),
):
    """
    preview 전용:
    저장된 유료설문 + 무료설문 결과를 이용해서
    interpretation_result + GPT prompt를 생성한다.
    """
    report, _, session = _get_report_order_session_or_raise(
        token=payload.report_token,
        order_id=payload.order_id,
        db=db,
    )
    paid = db.query(PaidSurvey).filter(PaidSurvey.sid == report.sid).first()
    if not paid:
        raise HTTPException(status_code=404, detail="PAID_SURVEY_NOT_FOUND")
    result = _prepare_preview_result(
        sid=report.sid,
        order_id=payload.order_id,
        report_token=payload.report_token,
        session=session,
        db=db,
    )

    return PremiumReportGenerateOut(
        ok=True,
        sid=report.sid,
        prompt=result["prompt"],
        interpretation_result=result["interpretation_result"],
        meta=result["meta"],
    )


@router.post("/report/finalize", response_model=PremiumReportFinalizeOut)
def finalize_premium_report(
    payload: PremiumReportFinalizeIn,
    db: Session = Depends(get_db),
):
    """
    최종 저장 전용:
    1) preview payload 생성
    2) GPT 호출
    3) markdown/html 생성
    4) reports 테이블 저장
    """
    report, _, session = _get_report_order_session_or_raise(
        token=payload.report_token,
        order_id=payload.order_id,
        db=db,
    )

    preview = _prepare_preview_result(
        sid=report.sid,
        order_id=payload.order_id,
        report_token=payload.report_token,
        session=session,
        db=db,
    )

    existing_html = (report.html or "").strip()
    existing_markdown = (report.markdown or "").strip()

    if (
        not payload.overwrite
        and report.status == "READY"
        and existing_html
        and existing_markdown
    ):
        return PremiumReportFinalizeOut(
            ok=True,
            sid=report.sid,
            report_token=payload.report_token,
            saved=False,
            status=report.status,
            prompt=preview["prompt"],
            interpretation_result=preview["interpretation_result"],
            markdown=report.markdown,
            html=report.html,
            meta={**preview["meta"], "reused_existing": True},
        )

    # 기존 결과는 지우지 않고 상태만 먼저 전환
    report.status = "GENERATING"
    db.commit()

    try:
        markdown_text = generate_premium_markdown(preview["prompt"])
        html_text = render_premium_report_html(markdown_text)

        report.markdown = markdown_text
        report.html = html_text
        report.generated_at = datetime.utcnow()
        report.status = "READY"

        db.commit()
        db.refresh(report)

        return PremiumReportFinalizeOut(
            ok=True,
            sid=report.sid,
            report_token=payload.report_token,
            saved=True,
            status=report.status,
            prompt=preview["prompt"],
            interpretation_result=preview["interpretation_result"],
            markdown=report.markdown,
            html=report.html,
            meta={**preview["meta"], "report_url": f"/r/{payload.report_token}"},
        )

    except PremiumLLMError as e:
        db.rollback()

        failed = db.query(Report).filter(Report.sid == report.sid).first()
        if failed:
            failed.status = "FAILED"
            db.commit()

        raise HTTPException(status_code=502, detail=f"LLM_CALL_FAILED: {e}")

    except Exception as e:
        db.rollback()

        failed = db.query(Report).filter(Report.sid == report.sid).first()
        if failed:
            failed.status = "FAILED"
            db.commit()

        raise HTTPException(status_code=500, detail=f"PREMIUM_REPORT_FINALIZE_FAILED: {e}")


@router.get("/report/status", response_model=PremiumReportStatusOut)
def get_premium_report_status(
    sid: str = Query(...),
    order_id: str = Query(...),
    report_token: str = Query(...),
    db: Session = Depends(get_db),
):
    report, order, _ = _get_report_order_session_or_raise(
        token=report_token,
        order_id=order_id,
        db=db,
    )

    if report.sid != sid:
        raise HTTPException(status_code=400, detail="SID_MISMATCH")

    has_html = bool((report.html or "").strip())
    has_markdown = bool((report.markdown or "").strip())

    return PremiumReportStatusOut(
        ok=True,
        sid=report.sid,
        report_token=report_token,
        status=report.status or "PENDING",
        has_html=has_html,
        has_markdown=has_markdown,
        report_url=f"/r/{report_token}",
    )


def _resolve_sid_from_token_and_order(
    *,
    token: str,
    order_id: str,
    db: Session,
) -> str:
    report = db.query(Report).filter(Report.report_token == token).first()
    if not report:
        raise HTTPException(status_code=404, detail="INVALID_REPORT_TOKEN")

    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="ORDER_NOT_FOUND")

    if order.status != "PAID":
        raise HTTPException(status_code=403, detail="NOT_PAID")

    if report.sid != order.sid:
        raise HTTPException(status_code=400, detail="REPORT_ORDER_MISMATCH")

    return report.sid