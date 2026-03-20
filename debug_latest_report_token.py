from app.db import SessionLocal
from app.models import Report

db = SessionLocal()
try:
    rows = (
        db.query(Report)
        .order_by(Report.generated_at.desc(), Report.sid.desc())
        .limit(10)
        .all()
    )

    if not rows:
        print("No reports found")
    else:
        for r in rows:
            print(
                f"sid={r.sid} | token={r.report_token} | status={r.status} | has_html={bool(r.html)}"
            )
finally:
    db.close()