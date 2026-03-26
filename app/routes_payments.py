# app/routes_payments.py
import os
import json
import time
import uuid
import hashlib
import traceback
from datetime import datetime
from urllib.parse import urlparse, quote
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Form, Query, Request
from fastapi.responses import RedirectResponse, HTMLResponse, PlainTextResponse
from pydantic import BaseModel

from .db import SessionLocal
from .models import Report, Order

router = APIRouter(tags=["payments"])

INICIS_MID = (os.getenv("INICIS_MID") or "").strip()
INICIS_SIGN_KEY = (os.getenv("INICIS_SIGN_KEY") or "").strip()
SERVICE_BASE_URL = (os.getenv("SERVICE_BASE_URL") or "https://reconnectlab.co.kr").strip().rstrip("/")
API_BASE_URL = (os.getenv("API_BASE_URL") or "https://relationship-safe-guide-api.onrender.com").strip().rstrip("/")
PAYMENT_BASE_URL = (os.getenv("PAYMENT_BASE_URL") or API_BASE_URL).rstrip("/")
PAYMENT_FAIL_URL = f"{SERVICE_BASE_URL}/payment-fail"

PREMIUM_PRICE = int(os.getenv("PREMIUM_PRICE") or "29000")
PREMIUM_GOODNAME = (os.getenv("PREMIUM_GOODNAME") or "리커넥트랩 프리미엄 AI 리포트").strip()


class PreparePaymentIn(BaseModel):
    reportToken: str
    buyerName: Optional[str] = "고객"
    buyerEmail: Optional[str] = "help@reconnectlab.co.kr"
    buyerTel: Optional[str] = "010-0000-0000"
    freeReturnUrl: Optional[str] = None
    freeToken: Optional[str] = None


def build_payment_fail_query(*, free_return_url: str = "", free_token: str = "", code: str = "", msg: str = "", mode: str = "") -> str:
    parts = []
    if mode:
        parts.append(f"mode={quote(mode)}")
    if code:
        parts.append(f"code={quote(code)}")
    if msg:
        parts.append(f"msg={quote(msg)}")
    if (free_return_url or "").strip():
        parts.append(f"free_return_url={quote((free_return_url or '').strip(), safe='')}")
    if (free_token or "").strip():
        parts.append(f"free_token={quote((free_token or '').strip(), safe='')}")
    return "&".join(parts)


def build_payment_fail_target(*, free_return_url: str = "", free_token: str = "", code: str = "", msg: str = "", mode: str = "") -> str:
    query = build_payment_fail_query(
        free_return_url=free_return_url,
        free_token=free_token,
        code=code,
        msg=msg,
        mode=mode,
    )
    return f"{PAYMENT_FAIL_URL}?{query}" if query else PAYMENT_FAIL_URL


def log_payment_return(event: str, **payload) -> None:
    try:
        print(f"{event} {json.dumps(payload, ensure_ascii=False, default=str)}")
    except Exception:
        print(f"{event} {payload}")


def build_payment_success_target(*, order_id: str) -> str:
    return f"{SERVICE_BASE_URL}/premium-survey?orderId={quote((order_id or '').strip())}"


def build_payment_home_target(*, reason: str) -> str:
    return f"{SERVICE_BASE_URL}/?payment_reason={quote((reason or '').strip())}"


def _render_client_return_page(*, mode: str, code: str = "", msg: str = "", free_return_url: str = "", free_token: str = "") -> RedirectResponse:
    target_url = build_payment_fail_target(
        free_return_url=free_return_url,
        free_token=free_token,
        code=code,
        msg=msg,
        mode=(mode or "cancel").strip().lower(),
    )
    return RedirectResponse(url=target_url, status_code=303)


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


def get_report_token_from_order(order: Order) -> str:
    if getattr(order, "free_report_token", None):
        return str(order.free_report_token).strip()

    try:
        payload = json.loads(order.pg_payload_json or "{}")
    except Exception:
        payload = {}

    if isinstance(payload, dict):
        # prepare 단계에서 넣어둔 값 우선
        if payload.get("prepared_payload", {}).get("report_token"):
            return str(payload["prepared_payload"]["report_token"]).strip()
        if payload.get("report_token"):
            return str(payload["report_token"]).strip()

    return ""


def get_free_return_context(prepared_payload: dict) -> tuple[str, str]:
    if not isinstance(prepared_payload, dict):
        return "", ""
    free_return_url = str(prepared_payload.get("free_return_url") or "").strip()
    free_token = str(prepared_payload.get("free_token") or "").strip()
    return free_return_url, free_token


def get_pay_method(approve_data: dict) -> str:
    return str(
        approve_data.get("payMethod")
        or approve_data.get("gopaymethod")
        or approve_data.get("paymethod")
        or ""
    ).strip().upper()


def is_vbank_pay_method(pay_method: str) -> bool:
    return pay_method in {"VBANK", "VACCT"}


def build_inicis_form(report_token: str, buyer_name: str, buyer_email: str, buyer_tel: str, free_return_url: str = "", free_token: str = ""):
    """
    주문 생성 + 이니시스 요청 form 데이터 생성 공통 함수
    """
    if not report_token.strip():
        raise HTTPException(status_code=400, detail="reportToken is required")

    if not INICIS_MID or not INICIS_SIGN_KEY:
        raise HTTPException(status_code=500, detail="INICIS_MID / INICIS_SIGN_KEY가 설정되지 않았습니다.")

    rep, sid = find_report_and_sid_by_token(report_token.strip())
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
            free_report_token=report_token.strip(),
            status="PENDING",
            payment_method=None,
            amount=PREMIUM_PRICE,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            pg_payload_json=json.dumps(
                {
                    "stage": "prepare",
                    "report_token": report_token.strip(),
                    "buyerName": buyer_name,
                    "buyerEmail": buyer_email,
                    "buyerTel": buyer_tel,
                    "free_return_url": (free_return_url or "").strip(),
                    "free_token": (free_token or "").strip(),
                    "created_at": datetime.utcnow().isoformat(),
                },
                ensure_ascii=False,
            ),
        )
        db.add(order)
        db.commit()
    finally:
        db.close()

    close_query = build_payment_fail_query(
        free_return_url=(free_return_url or "").strip(),
        free_token=(free_token or "").strip(),
    )

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
        "buyername": buyer_name,
        "buyeremail": buyer_email,
        "buyertel": buyer_tel,
        "returnUrl": f"{PAYMENT_BASE_URL}/api/payments/inicis/return",
        "closeUrl": f"{PAYMENT_BASE_URL}/api/payments/inicis/close" + (f"?{close_query}" if close_query else ""),
        "charset": "UTF-8",
        "format": "JSON",
        "payViewType": "overlay",
        "merchantData": oid,
        "offerPeriod": datetime.utcnow().strftime("%Y%m%d-%Y%m%d"),
        "gopaymethod": "",
        "acceptmethod": "centerCd(Y)",
    }
    return form


def render_inicis_html(form: dict, *, free_return_url: str = "", free_token: str = "") -> HTMLResponse:
    inputs = []
    for key, value in form.items():
        if value is None:
            continue
        safe_key = str(key).replace('"', "&quot;")
        safe_val = str(value).replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")
        inputs.append(f'<input type="hidden" name="{safe_key}" value="{safe_val}" />')

    html = f"""
    <!doctype html>
    <html lang="ko">
    <head>
      <meta charset="utf-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <title>리커넥트랩 결제 진행</title>
      <script src="https://stdpay.inicis.com/stdjs/INIStdPay.js" charset="UTF-8"></script>
      <style>
        body {{
          font-family: Arial, sans-serif;
          background: #0F1626;
          color: #F0ECE8;
          display: flex;
          align-items: center;
          justify-content: center;
          min-height: 100vh;
          margin: 0;
          padding: 24px;
        }}
        .box {{
          width: 100%;
          max-width: 420px;
          background: #1A2540;
          border: 1px solid rgba(212,145,108,.2);
          border-radius: 16px;
          padding: 28px 24px;
          text-align: center;
        }}
        .spinner {{
          width: 36px;
          height: 36px;
          border: 3px solid rgba(255,255,255,.15);
          border-top-color: #D4916C;
          border-radius: 50%;
          margin: 0 auto 16px;
          animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
          to {{ transform: rotate(360deg); }}
        }}
        .title {{
          font-size: 18px;
          font-weight: 700;
          margin-bottom: 8px;
        }}
        .desc {{
          font-size: 14px;
          color: #9AAABB;
          line-height: 1.6;
        }}
      </style>
    </head>
    <body>
      <div class="box">
        <div class="spinner"></div>
        <div class="title">결제창을 준비하고 있어요</div>
        <div class="desc">잠시만 기다리면 KG이니시스 결제창이 열립니다.</div>
      </div>

      <form id="inicisPayForm" method="POST" accept-charset="UTF-8" style="display:none;">
        {''.join(inputs)}
      </form>

      <script>
        window.addEventListener("load", function () {{
          console.debug("[RCL payment]", "payment.page.version", "2026-03-22-context-isolation-v1");
          console.debug("[RCL payment]", "payment.context", {{
            is_top_window: window.self === window.top,
            current_url: window.location.href
          }});

var paymentFailUrl = "{build_payment_fail_target(mode='cancel', free_return_url=free_return_url, free_token=free_token)}";
          var closeUrl = "{f'{PAYMENT_BASE_URL}/api/payments/inicis/close' + (f'?{build_payment_fail_query(free_return_url=(free_return_url or '').strip(), free_token=(free_token or '').strip())}' if build_payment_fail_query(free_return_url=(free_return_url or '').strip(), free_token=(free_token or '').strip()) else '')}";
          var payStarted = false;
          var redirecting = false;
          var sawBlur = false;

          function redirectPaymentFail(reason) {{
            if (redirecting) return;
            redirecting = true;
            console.debug("[RCL payment]", "pay.close.redirect_target", paymentFailUrl);
            console.debug("[RCL payment]", "pay.start.redirect_payment_fail", {{ reason: reason }});
            console.debug("[RCL payment]", "pay.start.redirect_target", paymentFailUrl);
            window.location.replace(paymentFailUrl);
          }}

          var removed = [];
          ["rcl-nav", "rcl-main", "rcl-footer", "rcl-state", "rcl-report-outer"].forEach(function (id) {{
            var node = document.getElementById(id);
            if (node && node.parentNode) {{
              removed.push(id);
              node.parentNode.removeChild(node);
            }}
          }});
          console.debug("[RCL payment]", "payment.free_dom.cleanup", {{ removed: removed }});
          console.debug("[RCL payment]", "pay.start.boot", {{ current_url: window.location.href, close_url: closeUrl }});
          console.debug("[RCL payment]", "pay.start.request_origin", window.location.origin);
          console.debug("[RCL payment]", "pay.start.close_url_built", closeUrl);
          try {{
            console.debug("[RCL payment]", "pay.start.close_url_origin", new URL(closeUrl, window.location.href).origin);
          }} catch (e) {{
            console.debug("[RCL payment]", "pay.start.close_url_origin", "INVALID");
          }}

          if (window.self !== window.top) {{
            console.debug("[RCL payment]", "payment.fail.redirect.mode", "embedded_context_escape");
            console.debug("[RCL payment]", "payment.fail.redirect.target", window.location.href);
            console.debug("[RCL payment]", "payment.fail.redirect.top", true);
            try {{
              window.top.location.replace(window.location.href);
              return;
            }} catch (e) {{}}
          }}

if (!window.INIStdPay || typeof window.INIStdPay.pay !== "function") {{
            console.debug("[RCL payment]", "payment.fail.redirect.mode", "script_load_fail");
            console.debug("[RCL payment]", "payment.fail.redirect.target", "{build_payment_fail_target(mode='fail', code='INICIS_SCRIPT_LOAD_FAIL', free_return_url=free_return_url, free_token=free_token)}");
            console.debug("[RCL payment]", "payment.fail.redirect.top", true);
            alert("결제 모듈을 불러오지 못했습니다.");
            try {{
              window.top.location.replace("{build_payment_fail_target(mode='fail', code='INICIS_SCRIPT_LOAD_FAIL', free_return_url=free_return_url, free_token=free_token)}");
            }} catch (e) {{
              window.location.replace("{build_payment_fail_target(mode='fail', code='INICIS_SCRIPT_LOAD_FAIL', free_return_url=free_return_url, free_token=free_token)}");
            }}
            return;
          }}
          window.addEventListener("blur", function () {{
            if (!payStarted) return;
            sawBlur = true;
            console.debug("[RCL payment]", "pay.start.close_detected", {{ event: "blur" }});
          }});
          window.addEventListener("focus", function () {{
            if (!payStarted || !sawBlur || redirecting) return;
            console.debug("[RCL payment]", "pay.start.cancel_detected", {{ event: "focus_after_blur" }});
            redirectPaymentFail("focus_after_blur");
          }});
          document.addEventListener("visibilitychange", function () {{
            if (!payStarted || redirecting) return;
            if (document.visibilityState === "hidden") {{
              sawBlur = true;
              console.debug("[RCL payment]", "pay.start.close_detected", {{ event: "visibility_hidden" }});
            }} else if (document.visibilityState === "visible" && sawBlur) {{
              console.debug("[RCL payment]", "pay.start.cancel_detected", {{ event: "visibility_visible_after_hidden" }});
              redirectPaymentFail("visibility_visible_after_hidden");
            }}
          }});
          payStarted = true;
          console.debug("[RCL payment]", "pay.start.open_inicis", {{ current_url: window.location.href }});
          INIStdPay.pay("inicisPayForm");
        }});
      </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/pay/start", response_class=HTMLResponse)
async def pay_start_page(
    report_token: str = Query(...),
    buyer_name: str = Query("고객"),
    buyer_email: str = Query("help@reconnectlab.co.kr"),
    buyer_tel: str = Query("010-0000-0000"),
    free_return_url: str = Query(""),
    free_token: str = Query(""),
):
    form = build_inicis_form(
        report_token=report_token,
        buyer_name=buyer_name or "고객",
        buyer_email=buyer_email or "help@reconnectlab.co.kr",
        buyer_tel=buyer_tel or "010-0000-0000",
        free_return_url=free_return_url or "",
        free_token=free_token or "",
    )
    return render_inicis_html(
        form,
        free_return_url=free_return_url or "",
        free_token=free_token or "",
    )


@router.post("/api/payments/inicis/prepare")
async def inicis_prepare(payload: PreparePaymentIn):
    form = build_inicis_form(
        report_token=payload.reportToken.strip(),
        buyer_name=payload.buyerName or "고객",
        buyer_email=payload.buyerEmail or "help@reconnectlab.co.kr",
        buyer_tel=payload.buyerTel or "010-0000-0000",
        free_return_url=payload.freeReturnUrl or "",
        free_token=payload.freeToken or "",
    )

    return {
        "ok": True,
        "form": form,
    }


@router.api_route("/api/payments/inicis/close", methods=["GET", "POST"], response_class=HTMLResponse)
async def inicis_close(
    free_return_url: str = Query(""),
    free_token: str = Query(""),
):
    return _render_client_return_page(
        mode="cancel",
        free_return_url=free_return_url or "",
        free_token=free_token or "",
    )
    return HTMLResponse(
        content=f"""
        <!doctype html>
        <html lang="ko">
        <head>
          <meta charset="utf-8" />
          <title>결제 취소</title>
        </head>
        <body>
          <script>
            if (window.opener && !window.opener.closed) {{
              window.close();
            }} else {{
              if (window.history.length > 1) {{
                window.history.back();
              }} else {{
                window.location.replace("{SERVICE_BASE_URL}/");
              }}
            }}
          </script>
        </body>
        </html>
        """
    )


@router.get("/api/payments/inicis/exit", response_class=HTMLResponse)
async def inicis_exit(
    mode: str = Query("cancel"),
    code: str = Query(""),
    msg: str = Query(""),
    free_return_url: str = Query(""),
    free_token: str = Query(""),
):
    return _render_client_return_page(
        mode=mode,
        code=code,
        msg=msg,
        free_return_url=free_return_url or "",
        free_token=free_token or "",
    )


@router.post("/api/payments/inicis/return")
async def inicis_return(
    request: Request,
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
    log_payment_return(
        "payment.return.enter",
        current_url=str(request.url),
        resultCode=resultCode,
        resultMsg=resultMsg,
        orderNumber=orderNumber,
        authUrl=authUrl,
        merchantData=merchantData,
        idc_name=idc_name,
    )

    if resultCode != "0000":
        log_payment_return(
            "payment.return.fallback_home",
            reason=(resultCode or "AUTH_FAIL").strip() or "AUTH_FAIL",
            orderNumber=orderNumber,
        )
        return RedirectResponse(
            url=f"{PAYMENT_BASE_URL}/api/payments/inicis/exit?mode=fail&code={quote(resultCode or 'AUTH_FAIL')}&msg={quote(resultMsg or '')}",
            status_code=303,
        )

    if not all([mid, orderNumber, authToken, authUrl]):
        log_payment_return(
            "payment.return.fallback_home",
            reason="ORDER_ID_MISSING" if not orderNumber else "INVALID_AUTH_RESULT",
            orderNumber=orderNumber,
        )
        return RedirectResponse(
            url=f"{PAYMENT_BASE_URL}/api/payments/inicis/exit?mode=fail&code=INVALID_AUTH_RESULT",
            status_code=303,
        )

    if not is_valid_inicis_auth_url(authUrl, idc_name):
        log_payment_return(
            "payment.return.fallback_home",
            reason="INVALID_AUTH_URL",
            orderNumber=orderNumber,
            authUrl=authUrl,
            idc_name=idc_name,
        )
        return RedirectResponse(
            url=f"{PAYMENT_BASE_URL}/api/payments/inicis/exit?mode=fail&code=INVALID_AUTH_URL",
            status_code=303,
        )

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == orderNumber).first()
        log_payment_return(
            "payment.return.order_lookup",
            resolved_order_id=(orderNumber or "").strip(),
            found=bool(order),
        )
        if not order:
            reason = "ORDER_NOT_FOUND"
            log_payment_return(
                "payment.return.fallback_home",
                reason=reason,
                resolved_order_id=(orderNumber or "").strip(),
            )
            return RedirectResponse(
                url=build_payment_home_target(reason=reason),
                status_code=303,
            )

        # 기존 prepare 데이터 미리 백업
        prepared_payload = {}
        try:
            prepared_payload = json.loads(order.pg_payload_json or "{}")
        except Exception:
            prepared_payload = {}
        free_return_url, free_token = get_free_return_context(prepared_payload)

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
                    "prepared_payload": prepared_payload,
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
                url=f"{PAYMENT_BASE_URL}/api/payments/inicis/exit?{build_payment_fail_query(mode='fail', code='APPROVE_HTTP_ERROR', free_return_url=free_return_url, free_token=free_token)}",
                status_code=303,
            )

        if not approve_data or approve_data.get("resultCode") != "0000":
            order.status = "FAILED"
            order.pg_payload_json = json.dumps(
                {
                    "stage": "approve_failed",
                    "prepared_payload": prepared_payload,
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
                url=f"{PAYMENT_BASE_URL}/api/payments/inicis/exit?{build_payment_fail_query(mode='fail', code=(approve_data or {}).get('resultCode', 'APPROVE_FAIL'), free_return_url=free_return_url, free_token=free_token)}",
                status_code=303,
            )

        pay_method = get_pay_method(approve_data)

        # 가상계좌는 "승인성공"이 아니라 "채번성공"일 수 있음
        if is_vbank_pay_method(pay_method):
            order.status = "VBANK_ISSUED"
            order.payment_method = pay_method
            order.amount = int(approve_data.get("TotPrice") or order.amount or PREMIUM_PRICE)
            order.updated_at = datetime.utcnow()
            order.pg_payload_json = json.dumps(
                {
                    "stage": "vbank_issued",
                    "prepared_payload": prepared_payload,
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

            redirect_target = f"{SERVICE_BASE_URL}/payment-pending?orderId={quote(order.order_id)}"
            log_payment_return(
                "payment.return.redirect_target",
                final_redirect_url=redirect_target,
                reason="PAYMENT_PENDING",
                order_id=order.order_id,
            )
            return RedirectResponse(
                url=redirect_target,
                status_code=303,
            )

        # 카드/즉시결제류만 여기서 PAID 처리
        order.status = "PAID"
        order.payment_method = pay_method
        order.amount = int(approve_data.get("TotPrice") or order.amount or PREMIUM_PRICE)
        order.paid_at = datetime.utcnow()
        order.updated_at = datetime.utcnow()
        order.pg_payload_json = json.dumps(
            {
                "stage": "paid",
                "prepared_payload": prepared_payload,
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

        redirect_target = build_payment_success_target(order_id=order.order_id)
        log_payment_return(
            "payment.return.redirect_target",
            final_redirect_url=redirect_target,
            reason="PAYMENT_CONFIRMED",
            order_id=order.order_id,
        )
        return RedirectResponse(
            url=redirect_target,
            status_code=303,
        )

    except Exception as exc:
        log_payment_return(
            "payment.return.fallback_home",
            reason=f"EXCEPTION_{exc.__class__.__name__[:40].upper()}",
            orderNumber=orderNumber,
            trace=traceback.format_exc(limit=3),
        )
        raise
    finally:
        db.close()


@router.post("/api/payments/inicis/vbank-notify")
async def inicis_vbank_notify(request: Request):
    """
    가상계좌 입금통보 노티
    - KG이니시스 관리자에서 '입금통보수신URL' 로 이 주소를 등록해야 함
    - 성공 처리 시 반드시 본문 "OK" 를 반환해야 함
    """
    form = await request.form()

    p_oid = (form.get("P_OID") or "").strip()
    p_status = (form.get("P_STATUS") or "").strip()
    p_amt = (form.get("P_AMT") or "").strip()
    p_tid = (form.get("P_TID") or "").strip()
    p_type = (form.get("P_TYPE") or "").strip()
    p_auth_dt = (form.get("P_AUTH_DT") or "").strip()
    p_rmesg1 = (form.get("P_RMESG1") or "").strip()
    p_rmesg2 = (form.get("P_RMESG2") or "").strip()
    p_noti = (form.get("P_NOTI") or "").strip()
    p_uname = (form.get("P_UNAME") or "").strip()
    p_fn_nm = (form.get("P_FN_NM") or "").strip()

    if not p_oid:
        return PlainTextResponse("NOT_FOUND", status_code=404)

    db = SessionLocal()
    try:
        order = db.query(Order).filter(Order.order_id == p_oid).first()
        if not order:
            return PlainTextResponse("NOT_FOUND", status_code=404)

        # 기존 payload 보존
        try:
            existing_payload = json.loads(order.pg_payload_json or "{}")
        except Exception:
            existing_payload = {}

        notify_data = {
            "P_OID": p_oid,
            "P_STATUS": p_status,
            "P_AMT": p_amt,
            "P_TID": p_tid,
            "P_TYPE": p_type,
            "P_AUTH_DT": p_auth_dt,
            "P_RMESG1": p_rmesg1,
            "P_RMESG2": p_rmesg2,
            "P_NOTI": p_noti,
            "P_UNAME": p_uname,
            "P_FN_NM": p_fn_nm,
            "received_at": datetime.utcnow().isoformat(),
        }

        # 00 = 채번, 02 = 입금통보
        if p_status == "02":
            order.status = "PAID"
            order.payment_method = (p_type or order.payment_method or "").strip().upper() or order.payment_method
            if p_amt:
                try:
                    order.amount = int(p_amt)
                except Exception:
                    pass
            order.paid_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()
            order.pg_payload_json = json.dumps(
                {
                    "stage": "vbank_paid",
                    "previous_payload": existing_payload,
                    "notify_result": notify_data,
                },
                ensure_ascii=False,
            )
            db.commit()
            return PlainTextResponse("OK", status_code=200)

        # 채번/기타 상태도 로그는 남김
        order.pg_payload_json = json.dumps(
            {
                "stage": "vbank_notify_received",
                "previous_payload": existing_payload,
                "notify_result": notify_data,
            },
            ensure_ascii=False,
        )
        order.updated_at = datetime.utcnow()
        db.commit()
        return PlainTextResponse("OK", status_code=200)

    except Exception:
        db.rollback()
        return PlainTextResponse("FAIL", status_code=500)
    finally:
        db.close()
