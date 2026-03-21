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


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_paid_survey_api.db"

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


def _seed_paid_accessible_row(order_status: str = "PAID"):
    db = TestingSessionLocal()
    try:
        uid = uuid.uuid4().hex[:8]
        sid = f"S_paid_{uid}"
        token = f"t_paid_{uid}"
        order_id = f"RCL_paid_{uid}"
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

        report = Report(
            sid=sid,
            status="READY",
            markdown="",
            html="",
            report_token=token,
            generated_at=now,
            expires_at=now,
        )
        db.add(report)

        order = Order(
            order_id=order_id,
            sid=sid,
            status=order_status,
            amount=29000,
            paid_at=now if order_status == "PAID" else None,
            pg_payload_json="{}",
        )
        db.add(order)

        db.commit()
        return sid, token, order_id
    finally:
        db.close()


def seed_paid_accessable_row():
    return _seed_paid_accessible_row(order_status="PAID")


def seed_ready_data():
    return _seed_paid_accessible_row(order_status="PAID")


def seed_not_paid_row():
    return _seed_paid_accessible_row(order_status="PENDING")


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


def test_submit_paid_survey_success(monkeypatch):
    sid, token, order_id = seed_paid_accessable_row()
    monkeypatch.setattr(
        "app.services.reporting.premium_pipeline.generate_premium_markdown",
        lambda prompt: "# 1. Current state\n\nAuto premium report",
    )

    payload = {
        "report_token": token,
        "order_id": order_id,
        "answers": _valid_paid_answers("pytest memo"),
        "submitted_at": None,
    }

    res = client.post("/api/premium/survey/paid", json=payload)
    assert res.status_code == 200, res.text

    body = res.json()
    assert body["ok"] is True
    assert body["sid"] == sid
    assert body["saved"] is True
    assert body["order_id"] == order_id
    assert body["report_token"] == token
    assert body["state"] == "READY"
    assert body["next"] == "OPEN_REPORT"
    assert body["next_url"] == f"/r/{token}"

    db = TestingSessionLocal()
    try:
        paid = db.query(PaidSurvey).filter(PaidSurvey.sid == sid).first()
        assert paid is not None
        report = db.query(Report).filter(Report.sid == sid).first()
        assert report is not None
        assert report.status == "READY"
        assert "Auto premium report" in report.markdown
        assert "<html" in report.html.lower()

        saved_answers = json.loads(paid.answers_json)
        assert saved_answers["q1"] == "short"
        assert saved_answers["q18"] == ["sns_stalk"]
        assert saved_answers["q19"] == ["focus_down"]
        assert saved_answers["notes"] == "pytest memo"
    finally:
        db.close()


def test_submit_paid_survey_not_paid():
    sid, token, order_id = seed_not_paid_row()

    payload = {
        "report_token": token,
        "order_id": order_id,
        "answers": _valid_paid_answers("not paid case"),
        "submitted_at": None,
    }

    res = client.post("/api/premium/survey/paid", json=payload)
    assert res.status_code == 403, res.text

    body = res.json()
    assert body["detail"] == "NOT_PAID"

    db = TestingSessionLocal()
    try:
        paid = db.query(PaidSurvey).filter(PaidSurvey.sid == sid).first()
        assert paid is None
    finally:
        db.close()


def test_paid_survey_save_without_sid_success(monkeypatch):
    sid, token, order_id = seed_ready_data()
    monkeypatch.setattr(
        "app.services.reporting.premium_pipeline.generate_premium_markdown",
        lambda prompt: "# 1. Current state\n\nAuto premium report",
    )

    payload = {
        "report_token": token,
        "order_id": order_id,
        "answers": _valid_paid_answers("first save"),
    }

    res = client.post("/api/premium/survey/paid", json=payload)
    assert res.status_code == 200, res.text

    body = res.json()
    assert body["ok"] is True
    assert body["sid"] == sid
    assert body["saved"] is True
    assert body["state"] == "READY"

    payload2 = {
        "report_token": token,
        "order_id": order_id,
        "answers": _valid_paid_answers("updated save"),
    }

    res2 = client.post("/api/premium/survey/paid", json=payload2)
    assert res2.status_code == 200, res2.text

    body2 = res2.json()
    assert body2["ok"] is True
    assert body2["sid"] == sid
    assert body2["saved"] is True
    assert body2["state"] == "READY"

    db = TestingSessionLocal()
    try:
        paid_rows = db.query(PaidSurvey).filter(PaidSurvey.sid == sid).all()
        assert len(paid_rows) == 1

        saved_answers = json.loads(paid_rows[0].answers_json)
        assert saved_answers["notes"] == "updated save"
        assert saved_answers["q18"] == ["sns_stalk"]
        assert saved_answers["q19"] == ["focus_down"]
    finally:
        db.close()
