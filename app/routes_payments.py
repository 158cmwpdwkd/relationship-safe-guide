# app/routes_payments.py
import os
import json
import time
import uuid
import hashlib
from datetime import datetime
from urllib.parse import urlparse
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Form
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from .db import SessionLocal
from .models import Report, Order

router = APIRouter(tags=["payments"])

INICIS_MID = (os.getenv("INICIS_MID") or "").strip()
INICIS_SIGN_KEY = (os.getenv("INICIS_SIGN_KEY") or "").strip()
SERVICE_BASE_URL = (os.getenv("SERVICE_BASE_URL") or "https://reconnectlab.co.kr").strip().rstrip("/")
API_BASE_URL = (os.getenv("API_BASE_URL") or "https://relationship-safe-guide-api.onrender.com").strip().rstrip("/")

PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE") or "29000")
PREMIUM_GOODNAME = (os.getenv("PREMIUM_GOODNAME") or "리커넥트랩 프리미엄 AI 리포트").strip()


class PreparePaymentIn(BaseModel):
    reportToken: str
    buyerName: Optional[str] = "고객"
    buyerEmail: Optional[str] = "help@reconnectlab.co.kr"
    buyerTel: Optional[str] = "010-0000-0000"


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def make_order_id() -> str:
    return f"RCL_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"


def make_signature(oid: str, price: int, timestamp: str) -> str:
    return sha256_hex(f"oid={oid}&price={price}&timestamp={timestamp}")


def make_verification(oid: str, price: int, sign_key: str, timestamp: str) -> str:
    return sha256_hex(f"oid={oid}&price={price}&signKey={sign_key}&timestamp={timestamp}")


def make_mkey(sign_key: str) -> str:
    return sha256_hex(sign_key)


def make_auth_signature(auth_token: str, timestamp: str) -> str:
    return sha256_hex(f"authToken={auth_token}&timestamp={timestamp}")


def make_auth_verification(auth_token: str, sign_key: str, timestamp: str) -> str:
    return sha256_hex(f"authToken={auth_token}&signKey={sign_key}&timestamp={timestamp}")


def is_valid_inicis_auth_url(auth_url: str, idc_name: Optional[str]) -> bool:
    """
    authUrl이 이니시스 승인 URL인지 최소 검증.
    idc_name(fc/ks/stg)와 host prefix도 대조.
    """
    try:
        parsed = urlparse(auth_url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme != "https":
            return False

        allowed_hosts = {
            "fcstdpay.inicis.com",
            "ksstdpay.inicis.com",
            "stgstdpay.inicis.com",
        }
        if host not in allowed_hosts:
            return False

        if idc_name:
            idc = idc_name.lower().strip()
            if idc == "fc" and host != "fcstdpay.inicis.com":
                return False
            if idc == "ks" and host != "ksstdpay.inicis.com":
                return False
            if idc == "stg" and host != "stgstdpay.inicis.com":
                return False

        return True
    except Exception:
        return False


def find_report_and_sid_by_token(report_token: str):
    db = SessionLocal()
    try:
        rep = db.query(Report).filter(Report.report_token == report_token).first()
        if not rep:
            return None, None
        return rep, rep.sid
    finally:
        db.close()


@router.post("/api/payments/inicis/prepare")
async def inicis_prepare(payload: PreparePaymentIn):
    if not payload.reportToken.strip():
        raise HTTPException(status_code=400, detail="reportToken is required")

    if not INICIS_MID or not INICIS_SIGN_KEY:
        raise HTTPException(status_code=500, detail="INICIS_MID / INICIS_SIGN_KEY가 설정되지 않았습니다.")

    rep, sid = find_report_and_sid_by_token(payload.reportToken.strip())
    if not rep or not sid:
        raise HTTPException(status_code=404, detail="유효한 report token을 찾을 수 없습니다.")

    oid = make_order_id()
    timestamp = str(int(time.time() * 1000))

    signature = make_signature(oid, PREMIUM_PRICE, timestamp)
    verification = make_verification(oid, PREMIUM_PRICE, INICIS_SIGN_KEY, timestamp)
    mkey = make_mkey(INICIS_SIGN_KEY)

    db = SessionLocal()
    try:
        order = Order(
            order_id=oid,
            sid=sid,
            status="PENDING",
            amount=PREMIUM_PRICE,
            pg_payload_json=json.dumps(
                {
                    "stage": "prepare",
                    "report_token": payload.reportToken.strip(),
                    "buyerName": payload.buyerName or "고객",
                    "buyerEmail": payload.buyerEmail or "help@reconnectlab.co.kr",
                    "buyerTel": payload.buyerTel or "010-0000-0000",
                    "created_at": datetime.utcnow().isoformat(),
                },
                ensure_ascii=False,
            ),
        )
        db.add(order)
        db.commit()
    finally:
        db.close()

    form = {
        "version": "1.0",
        "mid": INICIS_MID,
        "oid": oid,
        "price": str(PREMIUM_PRICE),
        "timestamp": timestamp,
        "use_chkfake": "Y",
        "signature": signature,
        "verification": verification,
        "mKey": mkey,
        "currency": "WON",
        "goodname": PREMIUM_GOODNAME,
        "buyername": payload.buyerName or "고객",
        "buyeremail": payload.buyerEmail or "help@reconnectlab.co.kr",
        "buyertel": payload.buyerTel or "010-0000-0000",
        "returnUrl": f"{API_BASE_URL}/api/payments/inicis/return",
        "closeUrl": f"{SERVICE_BASE_URL}/payment-close",
        "charset": "UTF-8",
        "format": "JSON",
        "payViewType": "overlay",
        "merchantData": payload.reportToken.strip(),
        # 디지털콘텐츠 당일 제공 기준 예시
        "offerPeriod": datetime.utcnow().strftime("%Y%m%d-%Y%m%d"),
    }

    return {
        "ok": True,
        "form": form,
    }


@router.post("/api/payments/inicis/return")
async def inicis_return(
    resultCode: Optional[str] = Form(None),
    resultMsg: Optional[str] = Form(None),
    mid: Optional[str] = Form(None),
    orderNumber: Optional[str] = Form(None),
    authToken: Optional[str] = Form(None),
    authUrl: Optional[str] = Form(None),
    netCancelUrl: Optional[str] = Form(None),
    charset: Optional[str] = Form("UTF-8"),
    merchantData: Optional[str] = Form(None),
    idc_name: Optional[str] = Form(None),
):
    # 1) 인증단계 실패
    if resultCode != "0000":
        return RedirectResponse(
            url=f"{SERVICE_BASE_URL}/payment-fail?code={resultCode or 'AUTH_FAIL'}&msg={resultMsg or ''}",
            status_code=303,
        )

    if not all([mid, orderNumber, authToken, authUrl]):
        return RedirectResponse(
            url=f"{SERVICE_BASE_URL}/payment-fail?code=INVALID_AUTH_RESULT",
            status_code=303,
        )

    if not is_valid_inicis_auth_url(authUrl, idc_name):
        return RedirectResponse(
            url=f"{SERVICE_BASE_URL}/payment-fail?code=INVALID_AUTH_URL",
            status_code=303,
        )

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == orderNumber).first()
        if not order:
            return RedirectResponse(
                url=f"{SERVICE_BASE_URL}/payment-fail?code=ORDER_NOT_FOUND",
                status_code=303,
            )

        timestamp = str(int(time.time() * 1000))
        signature = make_auth_signature(authToken, timestamp)
        verification = make_auth_verification(authToken, INICIS_SIGN_KEY, timestamp)

        approve_payload = {
            "mid": mid,
            "authToken": authToken,
            "timestamp": timestamp,
            "signature": signature,
            "verification": verification,
            "charset": charset or "UTF-8",
            "format": "JSON",
        }

        approve_data = None

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    authUrl,
                    data=approve_payload,
                    headers={"Content-Type": "application/x-www-form-urlencoded"},
                )
                resp.raise_for_status()
                approve_data = resp.json()
        except Exception as e:
            order.status = "FAILED"
            order.pg_payload_json = json.dumps(
                {
                    "stage": "approve_http_error",
                    "error": str(e),
                    "auth_result": {
                        "resultCode": resultCode,
                        "resultMsg": resultMsg,
                        "mid": mid,
                        "orderNumber": orderNumber,
                        "authUrl": authUrl,
                        "netCancelUrl": netCancelUrl,
                        "merchantData": merchantData,
                        "idc_name": idc_name,
                    },
                },
                ensure_ascii=False,
            )
            db.commit()

            # 망취소 시도
            if netCancelUrl:
                try:
                    async with httpx.AsyncClient(timeout=15.0) as client:
                        await client.post(
                            netCancelUrl,
                            data=approve_payload,
                            headers={"Content-Type": "application/x-www-form-urlencoded"},
                        )
                except Exception:
                    pass

            return RedirectResponse(
                url=f"{SERVICE_BASE_URL}/payment-fail?code=APPROVE_HTTP_ERROR",
                status_code=303,
            )

        if not approve_data or approve_data.get("resultCode") != "0000":
            order.status = "FAILED"
            order.pg_payload_json = json.dumps(
                {
                    "stage": "approve_failed",
                    "auth_result": {
                        "resultCode": resultCode,
                        "resultMsg": resultMsg,
                        "mid": mid,
                        "orderNumber": orderNumber,
                        "authUrl": authUrl,
                        "netCancelUrl": netCancelUrl,
                        "merchantData": merchantData,
                        "idc_name": idc_name,
                    },
                    "approve_result": approve_data,
                },
                ensure_ascii=False,
            )
            db.commit()

            return RedirectResponse(
                url=f"{SERVICE_BASE_URL}/payment-fail?code={(approve_data or {}).get('resultCode', 'APPROVE_FAIL')}",
                status_code=303,
            )

        # 승인 성공
        order.status = "PAID"
        order.amount = int(approve_data.get("TotPrice") or order.amount or PREMIUM_PRICE)
        order.paid_at = datetime.utcnow()
        order.pg_payload_json = json.dumps(
            {
                "stage": "paid",
                "auth_result": {
                    "resultCode": resultCode,
                    "resultMsg": resultMsg,
                    "mid": mid,
                    "orderNumber": orderNumber,
                    "authUrl": authUrl,
                    "netCancelUrl": netCancelUrl,
                    "merchantData": merchantData,
                    "idc_name": idc_name,
                },
                "approve_result": approve_data,
            },
            ensure_ascii=False,
        )
        db.commit()

        report_token = merchantData or ""
        if not report_token:
            # 혹시 merchantData가 비어 있으면 기존 payload에서 복구
            try:
                prepared = json.loads(order.pg_payload_json)
                report_token = prepared.get("report_token", "")
            except Exception:
                report_token = ""

        if not report_token:
            return RedirectResponse(
                url=f"{SERVICE_BASE_URL}/payment-fail?code=MISSING_REPORT_TOKEN",
                status_code=303,
            )

        return RedirectResponse(
            url=f"{SERVICE_BASE_URL}/premium-survey?token={report_token}&orderId={order.order_id}",
            status_code=303,
        )

    finally:
        db.close()