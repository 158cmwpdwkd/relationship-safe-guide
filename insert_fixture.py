import json
from datetime import datetime, UTC

from app.db import SessionLocal
from app.models import UserSession, Report, Order, PaidSurvey

SID = "S_FIXTURE_PREMIUM_20260321_01"
ORDER_ID = "RCL_FIXTURE_PREMIUM_20260321_01"
REPORT_TOKEN = "t_fixture_premium_20260321_01"


def main():
    db = SessionLocal()
    try:
        now = datetime.now(UTC)

        sess = db.query(UserSession).filter(UserSession.sid == SID).first()
        if not sess:
            sess = UserSession(
                sid=SID,
                created_at=now,
                free_answers_json=json.dumps({}, ensure_ascii=False),
                impulse_index=0,
                risk_level="LOW",
                fear_type="test",
                red_flags_json="[]",
                phone="01000000000",
                email="fixture@example.com",
                consent_collection_use=True,
                consent_cross_border=False,
                consent_version="v1",
                consent_at=now,
                consent_ip="127.0.0.1",
                consent_ua="fixture-script",
            )
            db.add(sess)

        rep = db.query(Report).filter(Report.report_token == REPORT_TOKEN).first()
        if not rep:
            rep = Report(
                sid=SID,
                status="READY",
                markdown="",
                html="",
                report_token=REPORT_TOKEN,
                generated_at=now,
                expires_at=now,
            )
            db.add(rep)

        order = db.query(Order).filter(Order.order_id == ORDER_ID).first()
        if not order:
            order = Order(
                order_id=ORDER_ID,
                sid=SID,
                status="PAID",
                amount=29000,
                paid_at=now,
                pg_payload_json="{}",
            )
            db.add(order)

        paid = db.query(PaidSurvey).filter(PaidSurvey.sid == SID).first()
        if not paid:
            paid = PaidSurvey(
                sid=SID,
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
                        "notes": "fixture insert",
                    },
                    ensure_ascii=False,
                ),
                submitted_at=now,
            )
            db.add(paid)

        db.commit()
        print("fixture inserted/verified")
        print("sid =", SID)
        print("order_id =", ORDER_ID)
        print("report_token =", REPORT_TOKEN)

    finally:
        db.close()


if __name__ == "__main__":
    main()