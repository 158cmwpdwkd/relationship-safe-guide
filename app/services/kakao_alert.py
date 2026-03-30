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


def _preview_text(value: str, *, limit: int = 500) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    if len(raw) > limit:
        return raw[: limit - 3] + "..."
    return raw


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


def _extract_json_keys(body) -> list[str]:
    if isinstance(body, dict):
        return sorted(str(key) for key in body.keys())
    return []


def _first_present(body: dict, *keys):
    for key in keys:
        value = body.get(key)
        if value not in (None, ""):
            return value
    return None


def _extract_response_fields(body) -> dict:
    if not isinstance(body, dict):
        return {
            "parsed_json_keys": [],
            "parsed_error_code": None,
            "parsed_error_message": None,
            "parsed_status_code": None,
            "parsed_status_message": None,
            "parsed_success": None,
            "parsed_status": None,
            "parsed_code": None,
            "parsed_message": None,
        }
    return {
        "parsed_json_keys": _extract_json_keys(body),
        "parsed_error_code": _first_present(body, "errorCode"),
        "parsed_error_message": _first_present(body, "errorMessage"),
        "parsed_status_code": _first_present(body, "statusCode"),
        "parsed_status_message": _first_present(body, "statusMessage"),
        "parsed_success": body.get("success"),
        "parsed_status": body.get("status"),
        "parsed_code": _first_present(body, "code"),
        "parsed_message": _first_present(body, "message"),
    }


def _body_shape_summary(payload: dict) -> dict:
    messages = payload.get("messages")
    message = messages[0] if isinstance(messages, list) and messages else {}
    kakao_options = message.get("kakaoOptions") if isinstance(message, dict) else {}
    variables = kakao_options.get("variables") if isinstance(kakao_options, dict) else {}
    return {
        "messages_count": len(messages) if isinstance(messages, list) else 0,
        "has_to": bool(message.get("to")) if isinstance(message, dict) else False,
        "has_kakaoOptions": isinstance(kakao_options, dict),
        "has_pfId": bool(kakao_options.get("pfId")) if isinstance(kakao_options, dict) else False,
        "has_templateId": bool(kakao_options.get("templateId")) if isinstance(kakao_options, dict) else False,
        "variables_keys": sorted(str(key) for key in variables.keys()) if isinstance(variables, dict) else [],
    }


def _status_code_is_failure(status_code) -> bool:
    if status_code in (None, ""):
        return False
    text = str(status_code).strip()
    if not text:
        return False
    if text.isdigit():
        code_number = int(text)
        if 200 <= code_number < 300:
            return False
        if text.endswith("000"):
            return False
        return True
    upper_text = text.upper()
    success_tokens = {"SUCCESS", "SENDING", "SENT", "PENDING", "ACCEPTED", "OK"}
    if upper_text in success_tokens:
        return False
    if "FAIL" in upper_text or "ERROR" in upper_text:
        return True
    return True


def _message_text_is_failure(message) -> bool:
    if message in (None, ""):
        return False
    upper_text = str(message).strip().upper()
    if not upper_text:
        return False
    failure_tokens = ("FAIL", "FAILED", "ERROR", "INVALID", "DENIED", "UNAUTHORIZED")
    return any(token in upper_text for token in failure_tokens)


def _evaluate_solapi_failure(*, http_status: int, body) -> tuple[bool, str]:
    if http_status >= 400:
        return True, "HTTP_ERROR"
    if not isinstance(body, dict):
        return False, ""
    if body.get("success") is False:
        return True, "SOLAPI_RESPONSE_FAILURE"
    if str(body.get("status") or "").strip().upper() == "FAILED":
        return True, "SOLAPI_STATUS_FAILED"
    if _first_present(body, "errorCode") not in (None, ""):
        return True, "SOLAPI_ERROR_CODE"
    if _first_present(body, "errorMessage") not in (None, ""):
        return True, "SOLAPI_ERROR_MESSAGE"
    status_code = _first_present(body, "statusCode")
    if _status_code_is_failure(status_code):
        return True, "SOLAPI_STATUS_CODE"
    status_message = _first_present(body, "statusMessage")
    if _message_text_is_failure(status_message):
        return True, "SOLAPI_STATUS_MESSAGE"
    code_value = _first_present(body, "code")
    if _status_code_is_failure(code_value):
        return True, "SOLAPI_CODE"
    message_value = _first_present(body, "message")
    if _message_text_is_failure(message_value):
        return True, "SOLAPI_MESSAGE"
    return False, ""


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


def send_kakao_alert(phone, template_id, url_value, alert_type=None, template_source=None) -> bool:
    normalized_phone = normalize_phone(phone)
    template = str(template_id or "").strip()
    url_text = str(url_value or "").strip()
    alert_type_value = str(alert_type or "").strip() or "unknown"
    template_source_value = str(template_source or "").strip() or "unknown"

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
            failure_stage="validation_input",
            template_id=template,
            template_source=template_source_value,
            url_preview=_preview_url(url_text),
        )
        return False

    if not SOLAPI_API_KEY or not SOLAPI_API_SECRET or not SOLAPI_PFID:
        _log_solapi_alert(
            "solapi.alert.fail",
            type=alert_type_value,
            reason="SOLAPI_ENV_MISSING",
            failure_stage="validation_env",
            template_id=template,
            template_source=template_source_value,
            pfid_preview=_mask_value(SOLAPI_PFID),
        )
        return False

    payload = _build_solapi_payload(
        phone=normalized_phone,
        template_id=template,
        url_value=url_text,
    )
    body_shape_summary = _body_shape_summary(payload)
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
        api_url=SOLAPI_API_URL,
        to_preview=_mask_phone(normalized_phone),
        template_id=template,
        template_source=template_source_value,
        pfid_preview=_mask_value(SOLAPI_PFID),
        variables_keys=body_shape_summary["variables_keys"],
        body_shape_summary=body_shape_summary,
        url_preview=_preview_url(url_text),
    )

    try:
        response = httpx.post(
            SOLAPI_API_URL,
            json=payload,
            headers=headers,
            timeout=10.0,
        )
        raw_response_text = _preview_text(response.text, limit=1000)
        parsed_body = None
        response_fields = _extract_response_fields(parsed_body)
        try:
            parsed_body = response.json()
        except Exception:
            parsed_body = None
        response_fields = _extract_response_fields(parsed_body)
        _log_solapi_alert(
            "solapi.alert.response",
            http_status=response.status_code,
            raw_response_text=raw_response_text,
            parsed_json_keys=response_fields["parsed_json_keys"],
            parsed_error_code=response_fields["parsed_error_code"],
            parsed_error_message=response_fields["parsed_error_message"],
            parsed_status_code=response_fields["parsed_status_code"],
            parsed_status_message=response_fields["parsed_status_message"],
            parsed_code=response_fields["parsed_code"],
            parsed_message=response_fields["parsed_message"],
        )
        is_failure, failure_reason = _evaluate_solapi_failure(
            http_status=response.status_code,
            body=parsed_body,
        )
        if is_failure:
            _log_solapi_alert(
                "solapi.alert.fail",
                type=alert_type_value,
                reason=failure_reason,
                failure_stage="response_validation",
                http_status=response.status_code,
                template_id=template,
                template_source=template_source_value,
                raw_response_text=raw_response_text,
                parsed_error_code=response_fields["parsed_error_code"],
                parsed_error_message=response_fields["parsed_error_message"],
                parsed_status_code=response_fields["parsed_status_code"],
                parsed_status_message=response_fields["parsed_status_message"],
                parsed_code=response_fields["parsed_code"],
                parsed_message=response_fields["parsed_message"],
            )
            return False
        return True
    except Exception as exc:
        _log_solapi_alert(
            "solapi.alert.fail",
            type=alert_type_value,
            reason=exc.__class__.__name__,
            failure_stage="request_exception",
            template_id=template,
            template_source=template_source_value,
        )
        return False
