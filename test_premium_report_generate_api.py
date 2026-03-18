import json
import uuid
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import Order, PaidSurvey, Report, UserSession
from app.routes_premium import get_db, router


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_premium_report_generate_api.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def _valid_paid_answers(notes: str = "pytest memo"):
    return {
        "q1": "short",
        "q2": "dating_light",
        "q3": "never",
        "q4": "d3",
        "q5": "today_3d",
        "q6": "me",
        "q7": "fight",
        "q8": "mid",
        "q9": "cold_clear",
        "q10": "repeat_same",
        "q11": "avoid",
        "q12": "press",
        "q13": "normal",
        "q14": "none",
        "q15": "no",
        "q16": "no_contact",
        "q17": "m50_70",
        "q18": ["sns_stalk"],
        "q19": ["focus_down"],
        "q20": "reconnect",
        "q7_text": None,
        "q12_text": None,
        "q20_text": None,
        "notes": notes,
    }


def seed_ready_data(with_paid_survey: bool = True):
    db = TestingSessionLocal()
    try:
        uid = uuid.uuid4().hex[:8]
        sid = f"S_generate_{uid}"
        token = f"t_generate_{uid}"
        order_id = f"RCL_generate_{uid}"
        now = datetime.now(UTC)

        sess = UserSession(
            sid=sid,
            created_at=now,
            free_answers_json=json.dumps(
                {
                    "FREE_Q1_stop_work_7d": "0",
                    "FREE_Q2_sns_check_yesterday": "2",
                    "FREE_Q3_impulse_control_rate": "3",
                    "FREE_Q4_main_fear": "abandonment",
                    "FREE_Q5_red_flags": [],
                },
                ensure_ascii=False,
            ),
            impulse_index=22,
            risk_level="LOW",
            fear_type="abandonment",
            red_flags_json="[]",
            phone="01012341234",
            email=f"{uid}@example.com",
            consent_collection_use=True,
            consent_cross_border=False,
            consent_version="v1",
            consent_at=now,
            consent_ip="127.0.0.1",
            consent_ua="pytest",
        )
        db.add(sess)

        rep = Report(
            sid=sid,
            status="READY",
            markdown="",
            html="",
            report_token=token,
            generated_at=now,
            expires_at=now,
        )
        db.add(rep)

        order = Order(
            order_id=order_id,
            sid=sid,
            status="PAID",
            amount=29000,
            paid_at=now,
            pg_payload_json="{}",
        )
        db.add(order)

        if with_paid_survey:
            paid = PaidSurvey(
                sid=sid,
                answers_json=json.dumps(_valid_paid_answers("generate test"), ensure_ascii=False),
                submitted_at=now,
            )
            db.add(paid)

        db.commit()
        return sid, token, order_id
    finally:
        db.close()


def test_generate_premium_report_payload_success():
    sid, token, order_id = seed_ready_data(with_paid_survey=True)

    payload = {
        "order_id": order_id,
        "report_token": token,
    }

    res = client.post("/api/premium/report/generate", json=payload)
    assert res.status_code == 200, res.text

    body = res.json()
    assert body["ok"] is True
    assert body["sid"] == sid
    assert body["prompt"]
    assert isinstance(body["interpretation_result"], dict)
    assert isinstance(body["meta"], dict)


def test_generate_premium_report_payload_without_paid_survey():
    sid, token, order_id = seed_ready_data(with_paid_survey=False)

    payload = {
        "order_id": order_id,
        "report_token": token,
    }

    res = client.post("/api/premium/report/generate", json=payload)
    assert res.status_code == 404, res.text

    body = res.json()
    assert body["detail"] == "PAID_SURVEY_NOT_FOUND"

def test_print_seed_values_for_manual_api_call():
    sid, token, order_id = seed_ready_data(with_paid_survey=True)

    print("\n===== MANUAL API TEST VALUES =====")
    print("sid =", sid)
    print("report_token =", token)
    print("order_id =", order_id)

    assert sid
    assert token
    assert order_id