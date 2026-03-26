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
    build_public_premium_report_url,
    resolve_premium_state,
    run_premium_pipeline,
    submit_paid_survey,
)

router = APIRouter(prefix="/api/premium", tags=["premium"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _raise_for_blocking_state(*, order_id: str, db: Session):
    state = resolve_premium_state(order_id=order_id, db=db)
    if state.state == "ORDER_NOT_FOUND":
        raise HTTPException(status_code=404, detail="ORDER_NOT_FOUND")
    if state.state == "NOT_PAID":
        raise HTTPException(status_code=403, detail="NOT_PAID")
    return state


@router.get("/entry", response_model=PremiumEntryOut)
def premium_entry(
    orderId: str = Query(...),
    db: Session = Depends(get_db),
):
    return build_entry_response(order_id=orderId, db=db)


@router.get("/access-check")
def premium_access_check(
    orderId: str = Query(...),
    db: Session = Depends(get_db),
):
    state = resolve_premium_state(order_id=orderId, db=db)
    if state.state == "ORDER_NOT_FOUND":
        return {"ok": False, "reason": "ORDER_NOT_FOUND"}
    if state.state == "NOT_PAID":
        return {"ok": False, "reason": "NOT_PAID"}
    return {
        "ok": True,
        "state": state.state,
        "order_id": state.order_id,
        "free_report_token": state.free_report_token,
        "premium_report_token": state.premium_report_token,
        "report_url": state.report_url,
    }


@router.post("/survey/paid", response_model=SurveySubmitOut)
@router.post("/survey/submit", response_model=SurveySubmitOut)
def submit_paid_survey_route(
    payload: PaidSurveyRequest,
    db: Session = Depends(get_db),
):
    return submit_paid_survey(
        order_id=payload.order_id,
        answers=payload.answers,
        submitted_at=payload.submitted_at,
        db=db,
    )


@router.post("/report/generate", response_model=PremiumReportGenerateOut)
def generate_premium_report(
    payload: PremiumReportGenerateIn,
    db: Session = Depends(get_db),
):
    _raise_for_blocking_state(order_id=payload.order_id, db=db)
    premium_report, state, preview, reused_existing = run_premium_pipeline(
        order_id=payload.order_id,
        db=db,
        overwrite=payload.overwrite,
    )

    public_report_url = build_public_premium_report_url(
        premium_report_token=premium_report.premium_report_token,
    )

    return PremiumReportGenerateOut(
        ok=True,
        sid=state.sid or "",
        order_id=payload.order_id,
        premium_report_token=premium_report.premium_report_token,
        report_url=public_report_url,
        status=premium_report.status,
        reused_existing=reused_existing,
        prompt=preview["prompt"],
        interpretation_result=preview["interpretation_result"],
        metrics=preview["metrics"],
        meta={
            **preview["meta"],
            "report_url": public_report_url,
            **({"reused_existing": True} if reused_existing else {}),
        },
    )


@router.post("/report/finalize", response_model=PremiumReportFinalizeOut)
def finalize_premium_report(
    payload: PremiumReportFinalizeIn,
    db: Session = Depends(get_db),
):
    _raise_for_blocking_state(order_id=payload.order_id, db=db)
    premium_report, state, preview, reused_existing = run_premium_pipeline(
        order_id=payload.order_id,
        db=db,
        overwrite=payload.overwrite,
    )

    public_report_url = build_public_premium_report_url(
        premium_report_token=premium_report.premium_report_token,
    )

    return PremiumReportFinalizeOut(
        ok=True,
        sid=state.sid or "",
        order_id=payload.order_id,
        premium_report_token=premium_report.premium_report_token,
        saved=not reused_existing and premium_report.status == "READY",
        status=premium_report.status,
        prompt=preview["prompt"],
        interpretation_result=preview["interpretation_result"],
        metrics=preview["metrics"],
        markdown=premium_report.markdown,
        html=premium_report.html,
        meta={
            **preview["meta"],
            "report_url": public_report_url,
            **({"reused_existing": True} if reused_existing else {}),
        },
    )


@router.get("/report/status", response_model=PremiumReportStatusOut)
def get_premium_report_status(
    order_id: str = Query(...),
    db: Session = Depends(get_db),
):
    state = _raise_for_blocking_state(order_id=order_id, db=db)
    return PremiumReportStatusOut(
        ok=True,
        sid=state.sid or "",
        order_id=order_id,
        premium_report_token=state.premium_report_token,
        status=state.state,
        has_html=state.has_report_html,
        has_markdown=state.has_report_markdown,
        report_url=state.report_url,
    )
