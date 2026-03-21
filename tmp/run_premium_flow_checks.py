import json
import os
import sys
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text


DB_PATH = os.path.join("tmp", "premium_flow_checks.db")
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
os.environ["DATABASE_URL"] = f"sqlite:///./{DB_PATH}"

from app.db import Base, SessionLocal, engine  # noqa: E402
from app.routes_premium import router as premium_router  # noqa: E402
from app.routes_report import router as report_router  # noqa: E402
import app.routes_premium as routes_premium  # noqa: E402


def now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def valid_paid_answers(notes: str) -> dict:
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


def rebuild_db() -> None:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def seed_case(*, sid: str, token: str, order_id: str, order_status: str, note: str) -> None:
    free_answers = json.dumps(
        {
            "FREE_Q1_stop_work_7d": "0",
            "FREE_Q2_sns_check_yesterday": "2",
            "FREE_Q3_impulse_control_rate": "3",
            "FREE_Q4_main_fear": "abandonment",
            "FREE_Q5_red_flags": [],
        },
        ensure_ascii=False,
    )
    paid_answers = json.dumps(valid_paid_answers(note), ensure_ascii=False)
    ts = now_iso()

    with engine.begin() as conn:
        conn.execute(
            text(
                """
                INSERT INTO user_sessions (
                    sid, created_at, free_answers_json, impulse_index, risk_level, fear_type,
                    red_flags_json, phone, email, consent_collection_use, consent_cross_border,
                    consent_version, consent_at, consent_ip, consent_ua
                ) VALUES (
                    :sid, :created_at, :free_answers_json, :impulse_index, :risk_level, :fear_type,
                    :red_flags_json, :phone, :email, :consent_collection_use, :consent_cross_border,
                    :consent_version, :consent_at, :consent_ip, :consent_ua
                )
                """
            ),
            {
                "sid": sid,
                "created_at": ts,
                "free_answers_json": free_answers,
                "impulse_index": 22,
                "risk_level": "LOW",
                "fear_type": "abandonment",
                "red_flags_json": "[]",
                "phone": "01012341234",
                "email": f"{sid.lower()}@example.com",
                "consent_collection_use": 1,
                "consent_cross_border": 0,
                "consent_version": "v1",
                "consent_at": ts,
                "consent_ip": "127.0.0.1",
                "consent_ua": "premium-flow-check",
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO reports (
                    sid, status, markdown, html, report_token, generated_at, expires_at
                ) VALUES (
                    :sid, :status, :markdown, :html, :report_token, :generated_at, :expires_at
                )
                """
            ),
            {
                "sid": sid,
                "status": "READY",
                "markdown": "",
                "html": "",
                "report_token": token,
                "generated_at": ts,
                "expires_at": ts,
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO orders (
                    order_id, sid, status, amount, paid_at, pg_payload_json
                ) VALUES (
                    :order_id, :sid, :status, :amount, :paid_at, :pg_payload_json
                )
                """
            ),
            {
                "order_id": order_id,
                "sid": sid,
                "status": order_status,
                "amount": 29000,
                "paid_at": ts if order_status == "PAID" else None,
                "pg_payload_json": "{}",
            },
        )
        conn.execute(
            text(
                """
                INSERT INTO paid_surveys (
                    sid, answers_json, submitted_at
                ) VALUES (
                    :sid, :answers_json, :submitted_at
                )
                """
            ),
            {
                "sid": sid,
                "answers_json": paid_answers,
                "submitted_at": ts,
            },
        )


def fetch_state(token: str, order_id: str) -> dict:
    with engine.begin() as conn:
        report = conn.execute(
            text(
                """
                SELECT sid, report_token, status, generated_at,
                       length(coalesce(markdown, '')) AS markdown_len,
                       length(coalesce(html, '')) AS html_len
                FROM reports
                WHERE report_token = :token
                """
            ),
            {"token": token},
        ).mappings().first()
        order = conn.execute(
            text(
                """
                SELECT order_id, sid, status, paid_at
                FROM orders
                WHERE order_id = :order_id
                """
            ),
            {"order_id": order_id},
        ).mappings().first()
    return {
        "report": dict(report) if report else None,
        "order": dict(order) if order else None,
    }


def main() -> None:
    rebuild_db()

    routes_premium.generate_premium_markdown = (
        lambda prompt: "# Premium Report\n\nThis is a stubbed premium report for flow verification."
    )

    app = FastAPI()
    app.include_router(premium_router)
    app.include_router(report_router)
    client = TestClient(app)

    normal = {
        "sid": "S_FLOW_OK_001",
        "token": "t_flow_ok_001",
        "order_id": "RCL_FLOW_OK_001",
    }
    not_paid = {
        "sid": "S_FLOW_NOT_PAID_001",
        "token": "t_flow_not_paid_001",
        "order_id": "RCL_FLOW_NOT_PAID_001",
    }
    mismatch_a = {
        "sid": "S_FLOW_MISMATCH_A",
        "token": "t_flow_mismatch_a",
        "order_id": "RCL_FLOW_MISMATCH_A",
    }
    mismatch_b = {
        "sid": "S_FLOW_MISMATCH_B",
        "token": "t_flow_mismatch_b",
        "order_id": "RCL_FLOW_MISMATCH_B",
    }

    seed_case(**normal, order_status="PAID", note="normal flow")
    seed_case(**not_paid, order_status="PENDING", note="not paid flow")
    seed_case(**mismatch_a, order_status="PAID", note="mismatch token owner")
    seed_case(**mismatch_b, order_status="PAID", note="mismatch order owner")

    print("=== CASE 1: NORMAL ===")
    print(f"sid={normal['sid']}")
    print(f"order_id={normal['order_id']}")
    print(f"report_token={normal['token']}")
    print("fixture_sql=INSERT user_sessions/reports/orders/paid_surveys via SQLAlchemy text()")

    generate_res = client.post(
        "/api/premium/report/generate",
        json={"order_id": normal["order_id"], "report_token": normal["token"]},
    )
    print(f"generate_status_code={generate_res.status_code}")
    print(f"generate_ok={generate_res.json().get('ok')}")

    finalize_res = client.post(
        "/api/premium/report/finalize",
        json={
            "order_id": normal["order_id"],
            "report_token": normal["token"],
            "overwrite": True,
        },
    )
    finalize_body = finalize_res.json()
    print(f"finalize_status_code={finalize_res.status_code}")
    print(f"finalize_saved={finalize_body.get('saved')}")
    print(f"finalize_status={finalize_body.get('status')}")

    status_res = client.get(
        "/api/premium/report/status",
        params={
            "sid": normal["sid"],
            "order_id": normal["order_id"],
            "report_token": normal["token"],
        },
    )
    status_body = status_res.json()
    print(f"status_status_code={status_res.status_code}")
    print(f"status_body={json.dumps(status_body, ensure_ascii=False)}")

    report_res = client.get(f"/r/{normal['token']}")
    print(f"report_view_status_code={report_res.status_code}")
    print(f"report_view_contains_stub={'stubbed premium report' in report_res.text}")
    print(f"db_state={json.dumps(fetch_state(normal['token'], normal['order_id']), ensure_ascii=False)}")

    print("\n=== CASE 2: NOT_PAID ===")
    print(f"sid={not_paid['sid']}")
    print(f"order_id={not_paid['order_id']}")
    print(f"report_token={not_paid['token']}")
    not_paid_res = client.post(
        "/api/premium/report/generate",
        json={"order_id": not_paid["order_id"], "report_token": not_paid["token"]},
    )
    print(f"expected=403 NOT_PAID")
    print(f"actual_status_code={not_paid_res.status_code}")
    print(f"actual_body={json.dumps(not_paid_res.json(), ensure_ascii=False)}")
    print(f"db_state={json.dumps(fetch_state(not_paid['token'], not_paid['order_id']), ensure_ascii=False)}")

    print("\n=== CASE 3: REPORT_ORDER_MISMATCH ===")
    print(f"token_owner_sid={mismatch_a['sid']}")
    print(f"order_owner_sid={mismatch_b['sid']}")
    print(f"order_id={mismatch_b['order_id']}")
    print(f"report_token={mismatch_a['token']}")
    mismatch_res = client.post(
        "/api/premium/report/generate",
        json={"order_id": mismatch_b["order_id"], "report_token": mismatch_a["token"]},
    )
    print(f"expected=400 REPORT_ORDER_MISMATCH")
    print(f"actual_status_code={mismatch_res.status_code}")
    print(f"actual_body={json.dumps(mismatch_res.json(), ensure_ascii=False)}")
    print(f"db_state_report_side={json.dumps(fetch_state(mismatch_a['token'], mismatch_a['order_id']), ensure_ascii=False)}")
    print(f"db_state_order_side={json.dumps(fetch_state(mismatch_b['token'], mismatch_b['order_id']), ensure_ascii=False)}")


if __name__ == "__main__":
    main()
