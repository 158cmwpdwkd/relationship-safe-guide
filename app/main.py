import os
import asyncpg

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes_survey import router as survey_router
from app.routes_report import router as report_router
from app.routes_admin import router as admin_router
from app.routes_payments import router as payments_router
from app.routes_premium import router as premium_router

from app.db import engine, Base
from app.models import UserSession, Order, PaidSurvey, Report, MessageSchedule

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://reconnectlab.co.kr",
        "https://www.reconnectlab.co.kr",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # 1) SQLAlchemy 테이블 생성
    Base.metadata.create_all(bind=engine)

    # 2) asyncpg pool 생성
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL is not set")

    app.state.db_pool = await asyncpg.create_pool(
        dsn=db_url,
        min_size=1,
        max_size=5,
        ssl="require",
    )

@app.on_event("shutdown")
async def shutdown():
    pool = getattr(app.state, "db_pool", None)
    if pool:
        await pool.close()

app.include_router(survey_router)
app.include_router(report_router)
app.include_router(admin_router)
app.include_router(payments_router)
app.include_router(premium_router)