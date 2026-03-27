import os
import re

import httpx

KAKAO_ALERT_API_URL = (os.getenv("KAKAO_ALERT_API_URL") or "").strip()
KAKAO_ALERT_API_KEY = (os.getenv("KAKAO_ALERT_API_KEY") or "").strip()
KAKAO_ALERT_SENDER_KEY = (os.getenv("KAKAO_ALERT_SENDER_KEY") or "").strip()


def normalize_phone(phone) -> str:
    digits = re.sub(r"\D", "", str(phone or ""))
    if digits.startswith("82") and len(digits) == 12:
        digits = "0" + digits[2:]
    if digits.startswith("10") and len(digits) == 10:
        digits = "0" + digits
    if len(digits) != 11 or not digits.startswith("010"):
        return ""
    return digits


def send_kakao_alert(phone, template_code, variables) -> bool:
    normalized_phone = normalize_phone(phone)
    template = str(template_code or "").strip()
    if not normalized_phone or not template:
        return False
    if not KAKAO_ALERT_API_URL or not KAKAO_ALERT_API_KEY or not KAKAO_ALERT_SENDER_KEY:
        return False

    payload = {
        "senderKey": KAKAO_ALERT_SENDER_KEY,
        "templateCode": template,
        "to": normalized_phone,
        "variables": variables or {},
    }
    headers = {
        "Authorization": f"Bearer {KAKAO_ALERT_API_KEY}",
        "Content-Type": "application/json; charset=utf-8",
    }

    try:
        response = httpx.post(
            KAKAO_ALERT_API_URL,
            json=payload,
            headers=headers,
            timeout=10.0,
        )
        if response.status_code >= 400:
            return False
        if not response.text.strip():
            return True
        try:
            body = response.json()
        except Exception:
            return True
        if isinstance(body, dict) and body.get("success") is False:
            return False
        return True
    except Exception:
        return False
