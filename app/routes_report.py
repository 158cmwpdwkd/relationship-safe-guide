# app/routes_report.py
from fastapi import APIRouter, Query
from fastapi.responses import HTMLResponse

from .report import make_report_html

router = APIRouter()

@router.get("/r/{token}", response_class=HTMLResponse)
async def report_by_path(token: str):
    """
    기존 호환: /r/{token}
    현재는 데모로 token을 risk/impulse/fear로 매핑하지 않고,
    토큰이 들어와도 '샘플 리포트'를 보여주는 구조로 복구만 먼저.
    다음 단계에서 token -> DB(sid) -> risk/impulse/fear로 연결.
    """
    # TODO: token 검증 + DB 조회로 아래 값 채우기
    risk_level = "LOW"
    impulse = 6
    fear_type = "forget"

    html = make_report_html(risk_level=risk_level, impulse=impulse, fear_type=fear_type)
    return HTMLResponse(html)

@router.get("/report", response_class=HTMLResponse)
async def report_by_query(token: str = Query(...)):
    """
    기존 호환: /report?token=...
    """
    # TODO: token 검증 + DB 조회로 아래 값 채우기
    risk_level = "LOW"
    impulse = 6
    fear_type = "forget"

    html = make_report_html(risk_level=risk_level, impulse=impulse, fear_type=fear_type)
    return HTMLResponse(html)