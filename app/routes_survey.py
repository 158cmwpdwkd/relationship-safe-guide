# app/routes_survey.py
from fastapi import APIRouter, Request, HTTPException
from datetime import datetime
import json

from .schemas import SurveyIn, FreeOut
from .risk import compute_risk
from .db import SessionLocal
from .models import UserSession, Report
from .report import expiry_6_months  # report.py에 있음

router = APIRouter()

def issue_sid() -> str:
    import uuid
    return "S_" + uuid.uuid4().hex[:12]

def issue_token(plan: str) -> str:
    import uuid
    # token prefix는 이미 /r/{token}에서 그대로 보이니까 plan만 유지
    return f"t_{plan}_" + uuid.uuid4().hex[:18]

@router.post("/api/survey/free", response_model=FreeOut)
async def submit_free(payload: SurveyIn, request: Request):
    if not payload.consent.privacy_consent:
        raise HTTPException(status_code=400, detail="privacy_consent required")

    answers = payload.answers

    # 필수키 체크(문서 고정)
    required = [
        "FREE_Q1_stop_work_7d",
        "FREE_Q2_sns_check_yesterday",
        "FREE_Q3_impulse_control_rate",
        "FREE_Q4_main_fear",
        "FREE_Q5_red_flags",
    ]
    for k in required:
        if k not in answers:
            raise HTTPException(status_code=400, detail=f"missing {k}")

    sid = issue_sid()
    risk = compute_risk(answers)

    # ✅ free_token 생성
    free_token = issue_token("free")

    # ✅ request 기반 메타
    ip = getattr(request.client, "host", None)
    ua = request.headers.get("user-agent")

    # ✅ answers 파싱/정규화
    # - Q5는 list여야 함 (문서: multi enum)
    red_flags = answers.get("FREE_Q5_red_flags") or []
    if not isinstance(red_flags, list):
        raise HTTPException(status_code=400, detail="FREE_Q5_red_flags must be list")

    # ✅ DB 저장
    db = SessionLocal()
    try:
        sess = UserSession(
            sid=sid,
            created_at=datetime.utcnow(),
            free_answers_json=json.dumps(answers, ensure_ascii=False),
            impulse_index=int(risk.get("impulse_index", 0)),
            risk_level=str(risk.get("risk_level", "LOW")),
            fear_type=str(answers.get("FREE_Q4_main_fear", "")),
            red_flags_json=json.dumps(red_flags, ensure_ascii=False),

            phone=payload.contact.phone,
            email=getattr(payload.contact, "email", None),

            consent_collection_use=True,
            consent_version=getattr(payload.consent, "consent_version", "v1"),
            consent_at=datetime.utcnow(),
            consent_ip=ip,
            consent_ua=ua,
        )
        db.add(sess)

        rep = Report(
            sid=sid,
            status="BLOCKED" if risk.get("risk_level") == "HARD_BLOCK" else "READY",
            report_token=free_token,
            generated_at=datetime.utcnow(),
            expires_at=expiry_6_months(),
            markdown="",
            html="",
        )
        db.add(rep)

        db.commit()
    finally:
        db.close()

    # ✅ report_url 생성 (base_url은 끝에 / 포함됨)
    base = str(request.base_url).rstrip("/")
    report_url = f"{base}/r/{free_token}"

    next_step = "HARD_BLOCK" if risk["risk_level"] == "HARD_BLOCK" else "PAY"

    return FreeOut(
        sid=sid,
        risk_level=risk["risk_level"],
        free_token=free_token,
        report_url=report_url,
        next=next_step,
    )