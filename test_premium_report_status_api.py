import json
import uuid
from datetime import datetime, UTC

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import Order, Report, UserSession
from app.routes_premium import router, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_premium_report_status.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


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


def seed_status_data(status="READY", with_html=True):
    db = TestingSessionLocal()
    try:
        uid = uuid.uuid4().hex[:8]
        sid = f"S_status_{uid}"
        token = f"t_status_{uid}"
        order_id = f"RCL_status_{uid}"
        now = datetime.now(UTC)

        sess = UserSession(
            sid=sid,
            created_at=now,
            free_answers_json=json.dumps({}, ensure_ascii=False),
            impulse_index=10,
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
        db.add(sess)

        rep = Report(
            sid=sid,
            status=status,
            markdown="## md" if with_html else "",
            html="<html><body>ok</body></html>" if with_html else "",
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

        db.commit()
        return sid, token, order_id
    finally:
        db.close()


def test_premium_report_status_ready():
    sid, token, order_id = seed_status_data(status="READY", with_html=True)

    res = client.get(
        "/api/premium/report/status",
        params={
            "sid": sid,
            "order_id": order_id,
            "report_token": token,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()

    assert body["ok"] is True
    assert body["status"] == "READY"
    assert body["has_html"] is True
    assert body["has_markdown"] is True
    assert body["report_url"] == f"/r/{token}"


def test_premium_report_status_generating():
    sid, token, order_id = seed_status_data(status="GENERATING", with_html=False)

    res = client.get(
        "/api/premium/report/status",
        params={
            "sid": sid,
            "order_id": order_id,
            "report_token": token,
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()

    assert body["ok"] is True
    assert body["status"] == "GENERATING"
    assert body["has_html"] is False
    assert body["has_markdown"] is False