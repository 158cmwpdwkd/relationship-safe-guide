# app/routes_survey.py
import os
import json
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException

from .schemas import SurveyIn, FreeOut
from .risk import compute_risk
from .db import SessionLocal
from .models import UserSession, Report
from .report import expiry_6_months  # report.py에 있음
from .services.kakao_alert import normalize_phone, send_kakao_alert

router = APIRouter()

# ✅ Render 환경변수 (KEY=PUBLIC_REPORT_BASE, VALUE=https://reconnectlab.co.kr)
PUBLIC_REPORT_BASE = (os.getenv("PUBLIC_REPORT_BASE") or "").strip().rstrip("/")
FREE_REPORT_PUBLIC_BASE_URL = "https://reconnectlab.co.kr"


def _resolve_free_template_config() -> tuple[str, str]:
    direct_value = (os.getenv("SOLAPI_TEMPLATE_FREE") or "").strip()
    if direct_value:
        return direct_value, "SOLAPI_TEMPLATE_FREE"
    fallback_value = (os.getenv("KAKAO_ALERT_FREE_TEMPLATE_CODE") or "").strip()
    if fallback_value:
        return fallback_value, "KAKAO_ALERT_FREE_TEMPLATE_CODE"
    return "", "missing"


SOLAPI_TEMPLATE_FREE, SOLAPI_TEMPLATE_FREE_SOURCE = _resolve_free_template_config()


def log_kakao_alert(event: str, **payload) -> None:
    try:
        print(f"{event} {json.dumps(payload, ensure_ascii=False, default=str)}")
    except Exception:
        print(f"{event} {payload}")

def issue_sid() -> str:
    import uuid
    return "S_" + uuid.uuid4().hex[:12]

def issue_token(plan: str) -> str:
    import uuid
    return f"t_{plan}_" + uuid.uuid4().hex[:18]

def build_public_report_url(token: str) -> str:
    """
    사용자가 보게 될 '브랜딩 도메인' 결과 페이지 URL.
    예: https://reconnectlab.co.kr/report?token=xxxx
    """
    if PUBLIC_REPORT_BASE:
        return f"{PUBLIC_REPORT_BASE}/report?token={token}"
    # 폴백(로컬/환경변수 미설정): 현재 서버에서 직접 보기
    return f"/r/{token}"


def _build_free_report_kakao_url(*, token: str) -> str:
    return f"{FREE_REPORT_PUBLIC_BASE_URL}/report?token={token}"


def _send_free_report_kakao_alert(*, report: Report, session: UserSession, db) -> None:
    phone = normalize_phone(session.phone)
    if not phone:
        log_kakao_alert(
            "solapi.alert.skip.phone_missing",
            type="free",
            sid=report.sid,
            report_token=report.report_token,
        )
        return
    if report.free_kakao_sent_at is not None:
        log_kakao_alert(
            "solapi.alert.skip.already_sent",
            type="free",
            sid=report.sid,
            report_token=report.report_token,
            sent_at=report.free_kakao_sent_at,
        )
        return

    report_url = _build_free_report_kakao_url(token=report.report_token)
    log_kakao_alert(
        "solapi.alert.template.resolve",
        type="free",
        template_id=SOLAPI_TEMPLATE_FREE,
        template_source=SOLAPI_TEMPLATE_FREE_SOURCE,
        template_missing=not bool(SOLAPI_TEMPLATE_FREE),
    )
    sent = send_kakao_alert(
        phone=phone,
        template_id=SOLAPI_TEMPLATE_FREE,
        url_value=report_url,
        alert_type="free",
        template_source=SOLAPI_TEMPLATE_FREE_SOURCE,
    )
    if not sent:
        log_kakao_alert(
            "solapi.alert.fail",
            type="free",
            sid=report.sid,
            report_token=report.report_token,
            to_preview=f"{phone[:5]}***{phone[-3:]}",
            template_id=SOLAPI_TEMPLATE_FREE,
            template_source=SOLAPI_TEMPLATE_FREE_SOURCE,
        )
        return

    report.free_kakao_sent_at = datetime.utcnow()
    db.commit()
    log_kakao_alert(
        "solapi.alert.free.send",
        sid=report.sid,
        report_token=report.report_token,
        to_preview=f"{phone[:5]}***{phone[-3:]}",
        template_id=SOLAPI_TEMPLATE_FREE,
        template_source=SOLAPI_TEMPLATE_FREE_SOURCE,
    )

@router.post("/api/survey/free", response_model=FreeOut)
async def submit_free(payload: SurveyIn, request: Request):
    if not payload.consent.privacy_consent:
        raise HTTPException(status_code=400, detail="privacy_consent required")

    answers = payload.answers

    # ✅ 필수키 체크(문서 고정)
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

    # ✅ Q5 정규화: list 강제
    red_flags = answers.get("FREE_Q5_red_flags") or []
    if not isinstance(red_flags, list):
        raise HTTPException(status_code=400, detail="FREE_Q5_red_flags must be list")

    sid = issue_sid()
    risk = compute_risk(answers)

    # ✅ free token 생성
    free_token = issue_token("free")

    # ✅ request 기반 메타
    ip = getattr(request.client, "host", None)
    ua = request.headers.get("user-agent")

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
        _send_free_report_kakao_alert(report=rep, session=sess, db=db)
    finally:
        db.close()

    # ✅ 사용자가 이동할 URL은 'reconnectlab 결과 페이지'로 고정
    # (그 페이지가 iframe으로 Render /r/{token}을 불러오면 됨)
    report_url = build_public_report_url(free_token)

    next_step = "HARD_BLOCK" if risk.get("risk_level") == "HARD_BLOCK" else "PAY"

    return FreeOut(
        sid=sid,
        risk_level=risk.get("risk_level", "LOW"),
        free_token=free_token,
        report_url=report_url,
        next=next_step,
    )
