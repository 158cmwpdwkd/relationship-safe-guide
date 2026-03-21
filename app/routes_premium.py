from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .db import SessionLocal
from .schemas import (
    PremiumEntryOut,
    PremiumReportFinalizeIn,
    PremiumReportFinalizeOut,
    PremiumReportGenerateIn,
    PremiumReportGenerateOut,
    PremiumReportStatusOut,
    SurveySubmitOut,
)
from .services.interpretation.schemas import PaidSurveyRequest
from .services.premium_report import (
    build_entry_response,
    prepare_premium_preview_or_raise,
    resolve_premium_state,
    run_premium_pipeline,
    submit_paid_survey_and_run_pipeline,
)

router = APIRouter(prefix="/api/premium", tags=["premium"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _raise_for_blocking_state(*, report_token: str, order_id: str, db: Session):
    state = resolve_premium_state(
        report_token=report_token,
        order_id=order_id,
        db=db,
    )
    if state.state == "INVALID_REPORT_TOKEN":
        raise HTTPException(status_code=404, detail="INVALID_REPORT_TOKEN")
    if state.state == "REPORT_ORDER_MISMATCH":
        raise HTTPException(status_code=400, detail="REPORT_ORDER_MISMATCH")
    if state.state == "NOT_PAID":
        raise HTTPException(status_code=403, detail="NOT_PAID")
    return state


@router.get("/entry", response_model=PremiumEntryOut)
def premium_entry(
    token: str = Query(...),
    order_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return build_entry_response(
        report_token=token,
        order_id=order_id,
        db=db,
    )


@router.get("/access-check")
def premium_access_check(
    token: str = Query(...),
    orderId: str = Query(...),
    db: Session = Depends(get_db),
):
    state = resolve_premium_state(
        report_token=token,
        order_id=orderId,
        db=db,
    )
    if state.state == "INVALID_REPORT_TOKEN":
        return {"ok": False, "reason": "INVALID_REPORT_TOKEN"}
    if state.state == "REPORT_ORDER_MISMATCH":
        return {"ok": False, "reason": "SID_MISMATCH"}
    if state.state == "NOT_PAID":
        return {"ok": False, "reason": "NOT_PAID"}
    return {"ok": True}


@router.post("/survey/paid", response_model=SurveySubmitOut)
@router.post("/survey/submit", response_model=SurveySubmitOut)
def submit_paid_survey(
    payload: PaidSurveyRequest,
    db: Session = Depends(get_db),
):
    return submit_paid_survey_and_run_pipeline(
        report_token=payload.report_token,
        order_id=payload.order_id,
        answers=payload.answers,
        submitted_at=payload.submitted_at,
        db=db,
    )


@router.post("/report/generate", response_model=PremiumReportGenerateOut)
def generate_premium_report_payload(
    payload: PremiumReportGenerateIn,
    db: Session = Depends(get_db),
):
    _raise_for_blocking_state(
        report_token=payload.report_token,
        order_id=payload.order_id,
        db=db,
    )

    _, _, _, result = prepare_premium_preview_or_raise(
        report_token=payload.report_token,
        order_id=payload.order_id,
        db=db,
    )

    state = resolve_premium_state(
        report_token=payload.report_token,
        order_id=payload.order_id,
        db=db,
    )

    return PremiumReportGenerateOut(
        ok=True,
        sid=state.sid,
        prompt=result["prompt"],
        interpretation_result=result["interpretation_result"],
        metrics=result["metrics"],
        meta=result["meta"],
    )


@router.post("/report/finalize", response_model=PremiumReportFinalizeOut)
def finalize_premium_report(
    payload: PremiumReportFinalizeIn,
    db: Session = Depends(get_db),
):
    _raise_for_blocking_state(
        report_token=payload.report_token,
        order_id=payload.order_id,
        db=db,
    )

    report, _, _, preview = prepare_premium_preview_or_raise(
        report_token=payload.report_token,
        order_id=payload.order_id,
        db=db,
    )
    reused_existing = (
        not payload.overwrite
        and report.status == "READY"
        and bool((report.html or "").strip())
        and bool((report.markdown or "").strip())
    )

    final_state = run_premium_pipeline(
        report_token=payload.report_token,
        order_id=payload.order_id,
        db=db,
        overwrite=payload.overwrite,
    )
    db.refresh(report)

    return PremiumReportFinalizeOut(
        ok=True,
        sid=final_state.sid,
        report_token=payload.report_token,
        saved=not reused_existing and final_state.state == "READY",
        status=report.status,
        prompt=preview["prompt"],
        interpretation_result=preview["interpretation_result"],
        metrics=preview["metrics"],
        markdown=report.markdown,
        html=report.html,
        meta={
            **preview["meta"],
            "report_url": f"/r/{payload.report_token}",
            **({"reused_existing": True} if reused_existing else {}),
        },
    )


@router.get("/report/status", response_model=PremiumReportStatusOut)
def get_premium_report_status(
    sid: str = Query(...),
    order_id: str = Query(...),
    report_token: str = Query(...),
    db: Session = Depends(get_db),
):
    state = _raise_for_blocking_state(
        report_token=report_token,
        order_id=order_id,
        db=db,
    )

    if state.sid != sid:
        raise HTTPException(status_code=400, detail="SID_MISMATCH")

    return PremiumReportStatusOut(
        ok=True,
        sid=state.sid,
        report_token=report_token,
        status=state.state,
        has_html=state.has_report_html,
        has_markdown=state.has_report_markdown,
        report_url=f"/r/{report_token}",
    )
