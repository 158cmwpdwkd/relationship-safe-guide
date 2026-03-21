# app/services/reporting/premium_pipeline.py

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Dict, Mapping

from app.services.interpretation.engine import run_interpretation_engine
from app.services.interpretation.premium_report import build_premium_report_prompt
from app.services.reporting.llm_client import generate_premium_markdown
from app.services.reporting.premium_metrics import build_premium_metrics
from app.services.reporting.premium_renderer import render_premium_report_html


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
    metrics = build_premium_metrics(interpretation_result)

    return {
        "interpretation_result": _as_dict(interpretation_result),
        "metrics": metrics,
        "prompt": prompt,
        "meta": {
            "report_type": "premium",
            "prompt_version": "v1",
            "metrics_version": metrics["version"],
        },
    }


def generate_premium_report_artifacts(*, prompt: str, metrics: Dict[str, Any]) -> Dict[str, str]:
    markdown_text = generate_premium_markdown(prompt)
    html_text = render_premium_report_html(
        markdown_text,
        metrics=metrics,
    )
    return {
        "markdown": markdown_text,
        "html": html_text,
    }


def finalize_premium_report_record(
    *,
    report: Any,
    markdown_text: str,
    html_text: str,
    db: Any,
    overwrite: bool = True,
):
    existing_html = (report.html or "").strip()
    existing_markdown = (report.markdown or "").strip()

    if (
        not overwrite
        and report.status == "READY"
        and existing_html
        and existing_markdown
    ):
        return report

    report.status = "GENERATING"
    db.commit()

    report.markdown = markdown_text
    report.html = html_text
    report.generated_at = datetime.now(UTC)
    report.status = "READY"

    db.commit()
    db.refresh(report)
    return report
