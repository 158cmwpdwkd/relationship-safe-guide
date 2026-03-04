# app/routes_survey.py
from fastapi import APIRouter, Request, HTTPException
from .schemas import SurveyIn, FreeOut
from .risk import compute_risk

router = APIRouter()

def issue_sid() -> str:
    # TODO: 실제로는 ULID/UUID + "S_" prefix
    import uuid
    return "S_" + uuid.uuid4().hex[:12]

def issue_token(sid: str, plan: str) -> str:
    # TODO: 실제로는 JWT/HMAC 서명 + exp
    import uuid
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
    free_token = issue_token(sid, "free")

    # TODO: DB 저장 (sid, schema_version, stage, answers_json, contact, consent, risk 파생값, free_token)
    # payload.consent.ip/user_agent는 request에서 채워 넣는 걸 권장
    # ip = request.client.host, ua = request.headers.get("user-agent")

    report_url = f"{request.base_url}r/{free_token}".rstrip("/")

    next_step = "HARD_BLOCK" if risk["risk_level"] == "HARD_BLOCK" else "PAY"

    return FreeOut(
        sid=sid,
        risk_level=risk["risk_level"],
        free_token=free_token,
        report_url=report_url,
        next=next_step,
    )