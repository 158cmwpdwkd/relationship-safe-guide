import hashlib
import hmac
import json
import os
import re
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

import httpx

DEFAULT_SOLAPI_API_URL = "https://api.solapi.com/messages/v4/send"
SOLAPI_API_URL = (
    os.getenv("SOLAPI_API_URL")
    or os.getenv("KAKAO_ALERT_API_URL")
    or DEFAULT_SOLAPI_API_URL
).strip()
SOLAPI_API_KEY = (
    os.getenv("SOLAPI_API_KEY")
    or os.getenv("KAKAO_ALERT_API_KEY")
    or ""
).strip()
SOLAPI_API_SECRET = (
    os.getenv("SOLAPI_API_SECRET")
    or os.getenv("KAKAO_ALERT_API_SECRET")
    or ""
).strip()
SOLAPI_PFID = (
    os.getenv("SOLAPI_PFID")
    or os.getenv("KAKAO_ALERT_SENDER_KEY")
    or ""
).strip()


def _log_solapi_alert(event: str, **payload) -> None:
    try:
        print(f"{event} {json.dumps(payload, ensure_ascii=False, default=str)}")
    except Exception:
        print(f"{event} {payload}")


def _mask_phone(phone: str) -> str:
    if len(phone or "") < 7:
        return "***"
    return f"{phone[:5]}***{phone[-3:]}"


def _mask_value(value: str, *, head: int = 4, tail: int = 3) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if len(raw) <= head + tail:
        return raw[:head] + "***"
    return f"{raw[:head]}***{raw[-tail:]}"


def _preview_url(url: str) -> str:
    raw = str(url or "").strip()
    if not raw:
        return ""
    try:
        parsed = urlsplit(raw)
        path = parsed.path or "/"
        query = f"?{parsed.query}" if parsed.query else ""
        preview = f"{parsed.scheme}://{parsed.netloc}{path}{query}"
    except Exception:
        preview = raw
    if len(preview) > 80:
        return preview[:77] + "..."
    return preview


def _response_body_summary(response: httpx.Response) -> str:
    text = (response.text or "").strip()
    if not text:
        return ""
    if len(text) > 300:
        return text[:297] + "..."
    return text


def normalize_phone(phone) -> str:
    digits = re.sub(r"\D", "", str(phone or ""))
    if digits.startswith("82") and len(digits) == 12:
        digits = "0" + digits[2:]
    if digits.startswith("10") and len(digits) == 10:
        digits = "0" + digits
    if len(digits) != 11 or not digits.startswith("010"):
        return ""
    return digits


def _build_solapi_auth_header(*, api_key: str, api_secret: str) -> str:
    date_value = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    if date_value.endswith("+00:00"):
        date_value = date_value[:-6] + "Z"
    salt = uuid.uuid4().hex
    signature = hmac.new(
        api_secret.encode("utf-8"),
        f"{date_value}{salt}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return (
        "HMAC-SHA256 "
        f"apiKey={api_key}, date={date_value}, salt={salt}, signature={signature}"
    )


def _build_solapi_payload(*, phone: str, template_id: str, url_value: str) -> dict:
    return {
        "messages": [
            {
                "to": phone,
                "kakaoOptions": {
                    "pfId": SOLAPI_PFID,
                    "templateId": template_id,
                    "disableSms": True,
                    "variables": {
                        "#{url}": url_value,
                    },
                },
            }
        ]
    }


def send_kakao_alert(phone, template_id, url_value, alert_type=None) -> bool:
    normalized_phone = normalize_phone(phone)
    template = str(template_id or "").strip()
    url_text = str(url_value or "").strip()
    alert_type_value = str(alert_type or "").strip() or "unknown"

    if not normalized_phone:
        _log_solapi_alert(
            "solapi.alert.skip.phone_missing",
            type=alert_type_value,
        )
        return False

    if not template or not url_text:
        _log_solapi_alert(
            "solapi.alert.fail",
            type=alert_type_value,
            reason="INVALID_MESSAGE_INPUT",
            template_id=template,
            url_preview=_preview_url(url_text),
        )
        return False

    if not SOLAPI_API_KEY or not SOLAPI_API_SECRET or not SOLAPI_PFID:
        _log_solapi_alert(
            "solapi.alert.fail",
            type=alert_type_value,
            reason="SOLAPI_ENV_MISSING",
            template_id=template,
            pfid_preview=_mask_value(SOLAPI_PFID),
        )
        return False

    payload = _build_solapi_payload(
        phone=normalized_phone,
        template_id=template,
        url_value=url_text,
    )
    headers = {
        "Authorization": _build_solapi_auth_header(
            api_key=SOLAPI_API_KEY,
            api_secret=SOLAPI_API_SECRET,
        ),
        "Content-Type": "application/json; charset=utf-8",
    }

    _log_solapi_alert(
        "solapi.alert.request",
        type=alert_type_value,
        to_preview=_mask_phone(normalized_phone),
        template_id=template,
        pfid_preview=_mask_value(SOLAPI_PFID),
        url_preview=_preview_url(url_text),
    )

    try:
        response = httpx.post(
            SOLAPI_API_URL,
            json=payload,
            headers=headers,
            timeout=10.0,
        )
        body_summary = _response_body_summary(response)
        _log_solapi_alert(
            "solapi.alert.response",
            http_status=response.status_code,
            response_body_summary=body_summary,
        )
        if response.status_code >= 400:
            _log_solapi_alert(
                "solapi.alert.fail",
                type=alert_type_value,
                reason="HTTP_ERROR",
                http_status=response.status_code,
                response_body_summary=body_summary,
            )
            return False

        if not body_summary:
            return True

        try:
            body = response.json()
        except Exception:
            return True

        if isinstance(body, dict):
            if body.get("success") is False:
                _log_solapi_alert(
                    "solapi.alert.fail",
                    type=alert_type_value,
                    reason="SOLAPI_RESPONSE_FAILURE",
                    response_body_summary=body_summary,
                )
                return False
            if body.get("status") == "FAILED":
                _log_solapi_alert(
                    "solapi.alert.fail",
                    type=alert_type_value,
                    reason="SOLAPI_STATUS_FAILED",
                    response_body_summary=body_summary,
                )
                return False
        return True
    except Exception as exc:
        _log_solapi_alert(
            "solapi.alert.fail",
            type=alert_type_value,
            reason=exc.__class__.__name__,
        )
        return False
