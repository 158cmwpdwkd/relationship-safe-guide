# debug_seed_render_manual.py
import json
import os
import uuid
from datetime import datetime, UTC

from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import UserSession, Report, Order, PaidSurvey


def valid_paid_answers(notes: str = "manual render seed"):
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


def main():
    db: Session = SessionLocal()
    try:
        uid = uuid.uuid4().hex[:8]
        sid = f"S_manual_{uid}"
        report_token = f"t_manual_{uid}"
        order_id = f"RCL_manual_{uid}"
        now = datetime.now(UTC)

        session = UserSession(
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
            consent_ua="manual-seed",
        )
        db.add(session)

        report = Report(
            sid=sid,
            status="READY",
            markdown="",
            html="",
            report_token=report_token,
            generated_at=now,
            expires_at=now,
        )
        db.add(report)

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
            answers_json=json.dumps(valid_paid_answers(), ensure_ascii=False),
            submitted_at=now,
        )
        db.add(paid)

        db.commit()

        print("\n===== CREATED MANUAL TEST DATA =====")
        print("sid =", sid)
        print("report_token =", report_token)
        print("order_id =", order_id)
        print("generate body =")
        print(
            json.dumps(
                {
                    "order_id": order_id,
                    "report_token": report_token,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        print("finalize body =")
        print(
            json.dumps(
                {
                    "order_id": order_id,
                    "report_token": report_token,
                    "overwrite": True,
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is not set")
    main()