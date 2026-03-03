import os
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import MessageSchedule

def run_once():
    now = datetime.utcnow()
    with SessionLocal() as db:  # type: Session
        q = select(MessageSchedule).where(
            MessageSchedule.status == "PENDING",
            MessageSchedule.send_at <= now
        )
        rows = db.execute(q).scalars().all()

        for msg in rows:
            try:
                # TODO: 여기서 알림톡 API 호출로 교체
                print(f"[SEND] {msg.type} sid={msg.sid} at={now.isoformat()}")

                msg.status = "SENT"
                msg.attempts += 1
                db.add(msg)
                db.commit()
            except Exception as e:
                msg.status = "FAILED"
                msg.attempts += 1
                msg.last_error = str(e)
                db.add(msg)
                db.commit()

if __name__ == "__main__":
    run_once()