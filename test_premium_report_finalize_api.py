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


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_premium_report_finalize.db"

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


def seed_ready_data():
    db = TestingSessionLocal()
    try:
        uid = uuid.uuid4().hex[:8]
        sid = f"S_finalize_{uid}"
        token = f"t_finalize_{uid}"
        order_id = f"RCL_finalize_{uid}"
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

        paid = PaidSurvey(
            sid=sid,
            answers_json=json.dumps(_valid_paid_answers("finalize test"), ensure_ascii=False),
            submitted_at=now,
        )
        db.add(paid)

        db.commit()
        return sid, token, order_id
    finally:
        db.close()


def test_finalize_premium_report_success(monkeypatch):
    sid, token, order_id = seed_ready_data()
    monkeypatch.setattr(
        "app.services.reporting.premium_pipeline.generate_premium_markdown",
        lambda prompt: "# 1. Current state\n\nTest markdown body",
    )

    payload = {
        "order_id": order_id,
        "report_token": token,
        "overwrite": True,
    }

    res = client.post("/api/premium/report/finalize", json=payload)
    assert res.status_code == 200, res.text

    body = res.json()
    assert body["ok"] is True
    assert body["sid"] == sid
    assert body["saved"] is True
    assert body["status"] == "READY"
    assert "Current state" in body["markdown"]
    assert isinstance(body["metrics"], dict)
    assert len(body["metrics"]["cards"]) == 6
    assert "<html" in body["html"].lower()
    assert "metrics-grid" in body["html"]
    assert 'data-metric-id="relationship_distance"' in body["html"]

    db = TestingSessionLocal()
    try:
        rep = db.query(Report).filter(Report.sid == sid).first()
        assert rep is not None
        assert rep.status == "READY"
        assert "Current state" in rep.markdown
        assert "<html" in rep.html.lower()
        assert rep.generated_at is not None
    finally:
        db.close()


def test_finalize_premium_report_llm_fail_keeps_old_html(monkeypatch):
    sid, token, order_id = seed_ready_data()

    db = TestingSessionLocal()
    try:
        rep = db.query(Report).filter(Report.sid == sid).first()
        rep.markdown = "OLD_MD"
        rep.html = "<html><body>OLD_HTML</body></html>"
        rep.status = "READY"
        db.commit()
    finally:
        db.close()

    def boom(prompt):
        raise RuntimeError("mock llm failure")

    monkeypatch.setattr("app.services.reporting.premium_pipeline.generate_premium_markdown", boom)

    payload = {
        "order_id": order_id,
        "report_token": token,
        "overwrite": True,
    }

    res = client.post("/api/premium/report/finalize", json=payload)
    assert res.status_code == 500, res.text

    body = res.json()
    assert "PREMIUM_REPORT_FINALIZE_FAILED" in body["detail"]

    db = TestingSessionLocal()
    try:
        rep = db.query(Report).filter(Report.sid == sid).first()
        assert rep is not None
        assert rep.status == "FAILED"
        assert rep.markdown == "OLD_MD"
        assert rep.html == "<html><body>OLD_HTML</body></html>"
    finally:
        db.close()


def test_finalize_premium_report_no_overwrite(monkeypatch):
    sid, token, order_id = seed_ready_data()

    db = TestingSessionLocal()
    try:
        rep = db.query(Report).filter(Report.sid == sid).first()
        rep.markdown = "EXISTING_MD"
        rep.html = "<html><body>EXISTING_HTML</body></html>"
        rep.status = "READY"
        db.commit()
    finally:
        db.close()

    called = {"count": 0}

    def fake_llm(prompt):
        called["count"] += 1
        return "NEW"

    monkeypatch.setattr("app.services.reporting.premium_pipeline.generate_premium_markdown", fake_llm)

    payload = {
        "order_id": order_id,
        "report_token": token,
        "overwrite": False,
    }

    res = client.post("/api/premium/report/finalize", json=payload)
    assert res.status_code == 200, res.text

    body = res.json()
    assert body["ok"] is True
    assert body["saved"] is False
    assert body["status"] == "READY"
    assert isinstance(body["metrics"], dict)
    assert len(body["metrics"]["cards"]) == 6
    assert body["markdown"] == "EXISTING_MD"
    assert body["html"] == "<html><body>EXISTING_HTML</body></html>"
    assert body["meta"]["reused_existing"] is True
    assert called["count"] == 0


def test_finalize_premium_report_without_sid_success(monkeypatch):
    sid, token, order_id = seed_ready_data()

    monkeypatch.setattr(
        "app.services.reporting.premium_pipeline.generate_premium_markdown",
        lambda prompt: "# 1. Current state\n\nTest markdown body",
    )

    payload = {
        "order_id": order_id,
        "report_token": token,
        "overwrite": True,
    }

    res = client.post("/api/premium/report/finalize", json=payload)
    assert res.status_code == 200, res.text

    body = res.json()
    assert body["ok"] is True
    assert body["sid"] == sid
    assert body["report_token"] == token


def test_finalize_report_order_mismatch_fail():
    sid1, token1, order_id1 = seed_ready_data()
    sid2, token2, order_id2 = seed_ready_data()

    payload = {
        "order_id": order_id2,
        "report_token": token1,
        "overwrite": True,
    }

    res = client.post("/api/premium/report/finalize", json=payload)
    assert res.status_code == 400, res.text

    body = res.json()
    assert body["detail"] == "REPORT_ORDER_MISMATCH"
