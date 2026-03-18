# app/services/reporting/llm_client.py

from __future__ import annotations

import os
from typing import Any, Dict, List

import httpx


class PremiumLLMError(RuntimeError):
    pass


def _require_env(name: str) -> str:
    value = (os.getenv(name) or "").strip()
    if not value:
        raise PremiumLLMError(f"missing env: {name}")
    return value


def _extract_message_content(data: Dict[str, Any]) -> str:
    choices = data.get("choices") or []
    if not choices:
        raise PremiumLLMError("no choices returned from OpenAI")

    message = choices[0].get("message") or {}
    content = message.get("content")

    if isinstance(content, str):
        return content.strip()

    if isinstance(content, list):
        texts: List[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                txt = (item.get("text") or "").strip()
                if txt:
                    texts.append(txt)
        merged = "\n".join(texts).strip()
        if merged:
            return merged

    raise PremiumLLMError("empty message content returned from OpenAI")


def generate_premium_markdown(prompt: str) -> str:
    api_key = _require_env("OPENAI_API_KEY")
    model = (os.getenv("OPENAI_PREMIUM_MODEL") or "gpt-4.1-mini").strip()
    timeout_seconds = float((os.getenv("OPENAI_TIMEOUT_SECONDS") or "60").strip())

    system_prompt = """
당신은 리커넥트랩 프리미엄 리포트 작성 모델이다.

절대 규칙:
1. 재회 성공 확률/가능성/퍼센트 금지
2. 상대 심리 단정 금지
3. 메시지 예문 생성 금지
4. 차단/거부/공포 신호를 무시하는 행동 유도 금지
5. 여성 안전 우선
6. 한국어 마크다운으로만 출력
7. 섹션 제목은 사용자가 준 구조를 유지
""".strip()

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        with httpx.Client(timeout=timeout_seconds) as client:
            resp = client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPStatusError as e:
        detail = ""
        try:
            detail = e.response.text[:1000]
        except Exception:
            pass
        raise PremiumLLMError(
            f"openai http error: status={e.response.status_code}, body={detail}"
        ) from e
    except Exception as e:
        raise PremiumLLMError(f"openai request failed: {e}") from e

    content = _extract_message_content(data)

    if not content:
        raise PremiumLLMError("openai returned empty markdown")

    return content