# app/routes_premium.py

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from .db import SessionLocal
from .models import Order, Report

router = APIRouter(prefix="/api/premium", tags=["premium"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/access-check")
def premium_access_check(
    token: str = Query(...),
    orderId: str = Query(...),
    db: Session = Depends(get_db),
):
    """
    유료설문 접근 체크

    검증 순서
    1. report_token 존재 여부
    2. order 존재 여부
    3. order.sid == report.sid
    4. order.status == PAID
    """

    report = db.query(Report).filter(Report.report_token == token).first()

    if not report:
        return {
            "ok": False,
            "reason": "ORDER_NOT_FOUND"
        }

    order = db.query(Order).filter(Order.order_id == orderId).first()

    if not order:
        return {
            "ok": False,
            "reason": "ORDER_NOT_FOUND"
        }

    if order.sid != report.sid:
        return {
            "ok": False,
            "reason": "ORDER_NOT_FOUND"
        }

    if order.status != "PAID":
        return {
            "ok": False,
            "reason": "NOT_PAID"
        }

    return {
        "ok": True
    }