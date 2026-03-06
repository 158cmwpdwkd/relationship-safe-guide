import os
import asyncpg
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials

router = APIRouter(prefix="/_admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")

security = HTTPBasic()


def require_admin(credentials: HTTPBasicCredentials = Depends(security)):
    admin_user = os.getenv("ADMIN_USER", "admin")
    admin_pass = os.getenv("ADMIN_PASS", "admin")

    correct_user = secrets.compare_digest(credentials.username, admin_user)
    correct_pass = secrets.compare_digest(credentials.password, admin_pass)

    if not (correct_user and correct_pass):
        raise HTTPException(status_code=401, headers={"WWW-Authenticate": "Basic"})


async def get_pool(request: Request) -> asyncpg.Pool:
    pool = request.app.state.db_pool
    return pool


# 관리자 홈
@router.get("", response_class=HTMLResponse)
async def admin_home(
    request: Request,
    _: HTTPBasicCredentials = Depends(require_admin),
    pool: asyncpg.Pool = Depends(get_pool)
):

    sql = """
    SELECT
    u.sid,
    u.phone,
    u.email,
    u.risk_level,
    u.created_at,
    r.report_token,
    r.status
    FROM user_sessions u
    LEFT JOIN reports r ON u.sid = r.sid
    ORDER BY u.created_at DESC
    LIMIT 50
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql)

    sessions = [dict(r) for r in rows]

    return templates.TemplateResponse(
        "admin.html",
        {
            "request": request,
            "sessions": sessions
        }
    )


# 세션 상세
@router.get("/session/{sid}", response_class=HTMLResponse)
async def session_detail(
    request: Request,
    sid: str,
    _: HTTPBasicCredentials = Depends(require_admin),
    pool: asyncpg.Pool = Depends(get_pool)
):

    async with pool.acquire() as conn:

        session = await conn.fetchrow("""
        SELECT * FROM user_sessions
        WHERE sid = $1
        """, sid)

        report = await conn.fetchrow("""
        SELECT * FROM reports
        WHERE sid = $1
        """, sid)

    if not session:
        raise HTTPException(404)

    return templates.TemplateResponse(
        "session_detail.html",
        {
            "request": request,
            "session": dict(session),
            "report": dict(report) if report else None
        }
    )


# 최근 1시간 세션 삭제
@router.post("/delete_recent_hour")
async def delete_recent_hour(
    _: HTTPBasicCredentials = Depends(require_admin),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        async with conn.transaction():
            # UTC 기준 최근 1시간
            await conn.execute("""
                DELETE FROM reports
                WHERE sid IN (
                    SELECT sid FROM user_sessions
                    WHERE created_at >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '1 hour'
                )
            """)
            await conn.execute("""
                DELETE FROM user_sessions
                WHERE created_at >= (NOW() AT TIME ZONE 'UTC') - INTERVAL '1 hour'
            """)

    return RedirectResponse("/_admin", status_code=303)

#오늘 데이터 삭제
@router.post("/delete_today")
async def delete_today(
    _: HTTPBasicCredentials = Depends(require_admin),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        async with conn.transaction():
            # UTC 기준 오늘 00:00 ~ 내일 00:00
            await conn.execute("""
                DELETE FROM reports
                WHERE sid IN (
                    SELECT sid FROM user_sessions
                    WHERE created_at >= DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC')
                      AND created_at <  DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC') + INTERVAL '1 day'
                )
            """)
            await conn.execute("""
                DELETE FROM user_sessions
                WHERE created_at >= DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC')
                  AND created_at <  DATE_TRUNC('day', NOW() AT TIME ZONE 'UTC') + INTERVAL '1 day'
            """)

    return RedirectResponse("/_admin", status_code=303)

#전체삭제
@router.post("/delete_all")
async def delete_all(
    _: HTTPBasicCredentials = Depends(require_admin),
    pool: asyncpg.Pool = Depends(get_pool),
):
    async with pool.acquire() as conn:
        async with conn.transaction():
            # 존재하는 테이블만 삭제(테이블명이 다를 수 있어서 방어적으로 처리)
            # to_regclass는 테이블 없으면 NULL 반환
            async def del_if_exists(table: str):
                exists = await conn.fetchval("SELECT to_regclass($1)", f"public.{table}")
                if exists:
                    await conn.execute(f"DELETE FROM {table}")

            # FK 자식 테이블부터
            await del_if_exists("message_schedules")
            await del_if_exists("paid_surveys")
            await del_if_exists("orders")

            # 그 다음 핵심 테이블
            await del_if_exists("reports")
            await del_if_exists("user_sessions")

    return RedirectResponse("/_admin", status_code=303)