from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes_survey import router as survey_router
from .routes_report import router as report_router

from .db import engine, Base
from .models import UserSession, Order, PaidSurvey, Report, MessageSchedule  # 👈 중요 (등록용 import)

app = FastAPI()

# 개발 중 임시: 전부 허용 (런칭 전에는 아임웹 도메인만 허용으로 변경)
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
def on_startup():
    Base.metadata.create_all(bind=engine)
    
app.include_router(survey_router)
app.include_router(report_router)
