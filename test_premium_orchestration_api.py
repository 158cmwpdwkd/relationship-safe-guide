import json
import uuid
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import Order, PaidSurvey, Report, UserSession
from app.routes_premium import get_db as premium_get_db, router as premium_router
from app.routes_report import router as report_router
import app.routes_report as routes_report_module


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_premium_orchestration_api.db"

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
app.include_router(premium_router)
app.include_router(report_router)
app.dependency_overrides[premium_get_db] = override_get_db
routes_report_module.SessionLocal = TestingSessionLocal
client = TestClient(app)


def setup_module(module):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def teardown_module(module):
    Base.metadata.drop_all(bind=engine)


def seed_case(
    *,
    order_status: str | None,
    with_paid_survey: bool,
    with_premium_html: bool,
):
    db = TestingSessionLocal()
    try:
        uid = uuid.uuid4().hex[:8]
        sid = f"S_orch_{uid}"
        token = f"t_orch_{uid}"
        order_id = f"RCL_orch_{uid}"
        now = datetime.now(UTC)

        session = UserSession(
            sid=sid,
            created_at=now,
            free_answers_json=json.dumps({}, ensure_ascii=False),
            impulse_index=12,
            risk_level="LOW",
            fear_type="abandonment",
            red_flags_json="[]",
            phone="01000000000",
            email=f"{uid}@example.com",
            consent_collection_use=True,
            consent_cross_border=False,
            consent_version="v1",
            consent_at=now,
            consent_ip="127.0.0.1",
            consent_ua="pytest",
        )
        db.add(session)

        report = Report(
            sid=sid,
            status="READY" if with_premium_html else "GENERATING",
            markdown="## premium" if with_premium_html else "",
            html="<html><body>premium</body></html>" if with_premium_html else "",
            report_token=token,
            generated_at=now,
            expires_at=now,
        )
        db.add(report)

        if order_status is not None:
            order = Order(
                order_id=order_id,
                sid=sid,
                status=order_status,
                amount=29000,
                paid_at=now if order_status == "PAID" else None,
                pg_payload_json="{}",
            )
            db.add(order)

        if with_paid_survey:
            paid = PaidSurvey(
                sid=sid,
                answers_json=json.dumps(
                    {
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
                        "notes": "orchestration test",
                    },
                    ensure_ascii=False,
                ),
                submitted_at=now,
            )
            db.add(paid)

        db.commit()
        return sid, token, order_id
    finally:
        db.close()


def test_entry_not_paid():
    sid, token, order_id = seed_case(
        order_status="PENDING",
        with_paid_survey=False,
        with_premium_html=False,
    )

    res = client.get("/api/premium/entry", params={"token": token, "order_id": order_id})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["state"] == "NOT_PAID"
    assert body["next_action"] == "GO_PAYMENT"


def test_entry_need_survey():
    sid, token, order_id = seed_case(
        order_status="PAID",
        with_paid_survey=False,
        with_premium_html=False,
    )

    res = client.get("/api/premium/entry", params={"token": token, "order_id": order_id})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["state"] == "NEED_SURVEY"
    assert body["next_action"] == "GO_SURVEY"
    assert f"orderId={order_id}" in body["next_url"]


def test_entry_ready():
    sid, token, order_id = seed_case(
        order_status="PAID",
        with_paid_survey=True,
        with_premium_html=True,
    )

    res = client.get("/api/premium/entry", params={"token": token})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["state"] == "READY"
    assert body["next_action"] == "OPEN_REPORT"
    assert body["next_url"] == f"/r/{token}"


def test_report_route_blocks_not_paid():
    sid, token, order_id = seed_case(
        order_status="PENDING",
        with_paid_survey=False,
        with_premium_html=False,
    )

    res = client.get(f"/r/{token}", follow_redirects=False)
    assert res.status_code == 403, res.text
    assert "NOT_PAID" in res.text


def test_report_route_redirects_need_survey():
    sid, token, order_id = seed_case(
        order_status="PAID",
        with_paid_survey=False,
        with_premium_html=False,
    )

    res = client.get(f"/r/{token}", follow_redirects=False)
    assert res.status_code == 409, res.text
    assert "NEED_SURVEY" in res.text
