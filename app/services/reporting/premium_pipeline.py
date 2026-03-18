# app/services/reporting/premium_pipeline.py

from __future__ import annotations

from typing import Any, Dict, Mapping

from app.services.interpretation.engine import run_interpretation_engine
from app.services.interpretation.premium_report import build_premium_report_prompt


def _as_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    raise TypeError("Expected mapping-like or object with __dict__")


def prepare_premium_report_payload(engine_input: Any) -> Dict[str, Any]:
    """
    EngineInput(또는 engine이 받을 수 있는 입력 객체)를 받아
    1) 해석 엔진 실행
    2) 프롬프트 생성
    3) 이후 GPT 호출용 payload 반환

    주의:
    - 이 함수는 raw paid answers를 EngineInput으로 바꾸지 않는다.
    - 변환 책임은 라우트/상위 서비스에서 맡는다.
    """
    interpretation_result = run_interpretation_engine(engine_input)
    prompt = build_premium_report_prompt(interpretation_result)

    return {
        "interpretation_result": _as_dict(interpretation_result),
        "prompt": prompt,
        "meta": {
            "report_type": "premium",
            "prompt_version": "v1",
        },
    }