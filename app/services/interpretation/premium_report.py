# app/services/interpretation/premium_report.py

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping


def _get(obj: Any, key: str, default: Any = None) -> Any:
    """
    dict-like / attribute-like 둘 다 안전하게 지원
    """
    if obj is None:
        return default

    if isinstance(obj, Mapping):
        return obj.get(key, default)

    return getattr(obj, key, default)


def _as_dict(value: Any) -> Dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    if hasattr(value, "__dict__"):
        return dict(vars(value))
    return {}


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple) or isinstance(value, set):
        return list(value)
    return [value]


def _join_list(values: Iterable[Any], default: str = "-") -> str:
    cleaned = [str(v).strip() for v in values if str(v).strip()]
    return ", ".join(cleaned) if cleaned else default


def _format_key_value_block(data: Mapping[str, Any], *, sort_keys: bool = True) -> str:
    if not data:
        return "- 없음"

    items = data.items()
    if sort_keys:
        items = sorted(items, key=lambda x: str(x[0]))

    lines: List[str] = []
    for k, v in items:
        if isinstance(v, float):
            val = f"{v:.2f}"
        else:
            val = str(v)
        lines.append(f"- {k}: {val}")
    return "\n".join(lines)


def _format_list_block(values: Iterable[Any], *, empty_text: str = "- 없음") -> str:
    cleaned = [str(v).strip() for v in values if str(v).strip()]
    if not cleaned:
        return empty_text
    return "\n".join(f"- {v}" for v in cleaned)


def _map_safety_level_kor(level: str) -> str:
    mapping = {
        "LOW": "낮은 위험 상태",
        "ELEVATED": "주의가 필요한 상태",
        "HIGH_RISK": "위험도가 높은 상태",
        "HARD_BLOCK": "접촉 및 행동 제한이 필요한 상태",
    }
    return mapping.get((level or "").upper().strip(), level or "-")


def _map_contact_mode_kor(mode: str) -> str:
    mapping = {
        "NO_CONTACT_STRATEGY": "비접촉 유지가 필요한 상태",
        "CONTACT_RESTRICTED": "접촉이 제한된 상태",
        "CAUTIOUS_DELAY": "신중한 지연이 필요한 상태",
        "STABILIZE_FIRST": "감정 안정이 우선인 상태",
    }
    return mapping.get((mode or "").upper().strip(), mode or "-")


def _build_behavior_policy(
    safety_level: str,
    contact_guidance_mode: str,
) -> str:
    safety_level = (safety_level or "").upper().strip()
    contact_guidance_mode = (contact_guidance_mode or "").upper().strip()

    safety_rules = {
        "HARD_BLOCK": [
            "행동 제안은 최소화하고 안정화 중심으로 작성한다.",
            "직접 연락, 우회 연락, 확인 행동, 감시 행동을 권하지 않는다.",
            "재접촉 관련 내용은 사실상 NO CONTACT 원칙 안에서만 다룬다.",
            "상대의 명시적 거부·차단·공포 신호를 절대 무시하지 않는다.",
            "안전 메시지는 강하게, 희망 메시지는 약하게 쓴다.",
        ],
        "HIGH_RISK": [
            "접촉 제안은 매우 제한적으로 다룬다.",
            "행동 가이드는 감정 진정, 충동 통제, 루틴 회복 중심으로 작성한다.",
            "상대 반응 해석보다 사용자 자신의 행동 제한 규칙을 우선한다.",
            "행동 제한 원칙을 분명한 문장으로 제시한다.",
        ],
        "ELEVATED": [
            "신중 접근 원칙을 유지한다.",
            "즉각 행동보다 지연, 정리, 점검을 우선한다.",
            "접촉 관련 내용은 조건부·제한적으로만 다룬다.",
            "불필요한 낙관 표현을 피한다.",
        ],
        "LOW": [
            "제한적 행동 가능 범위 안에서 현실적 가이드를 작성한다.",
            "다만 감정 과열 상태를 부추기는 표현은 금지한다.",
            "안전 기준을 먼저 제시하고 그 다음 행동을 말한다.",
        ],
    }

    contact_rules = {
        "NO_CONTACT_STRATEGY": [
            "재접촉 전략이 아니라 비접촉 안정화 전략으로 안내한다.",
            "연락을 참는 방법과 충동이 올라올 때의 대체 행동을 구체적으로 제시한다.",
            "접촉 허용 뉘앙스보다 접촉 유보 이유를 더 분명히 쓴다.",
        ],
        "CONTACT_RESTRICTED": [
            "연락은 기본 제한 상태로 본다.",
            "연락을 해도 된다는 식의 메시지를 주지 말고, 왜 제한이 필요한지 설명한다.",
            "사용자가 오해할 수 있는 모호한 문장을 피한다.",
        ],
        "CAUTIOUS_DELAY": [
            "즉시 행동보다 충분한 시간 지연 후 점검을 우선한다.",
            "연락 자체보다 지금 하지 말아야 할 행동을 먼저 정리한다.",
            "행동의 타이밍보다 행동 전 점검 기준을 더 자세히 쓴다.",
        ],
        "STABILIZE_FIRST": [
            "접촉보다 감정 안정화와 일상 기능 회복을 우선한다.",
            "행동 계획은 자기조절 루틴 중심으로 작성한다.",
            "실행 항목은 적더라도 구체적으로 쓴다.",
        ],
    }

    merged: List[str] = []
    merged.extend(safety_rules.get(safety_level, []))
    merged.extend(contact_rules.get(contact_guidance_mode, []))

    if not merged:
        return "- 별도 정책 없음"

    return "\n".join(f"- {x}" for x in merged)


def _build_inference_notes(axis_scores: Mapping[str, Any]) -> str:
    if not axis_scores:
        return "- 축 점수 없음"

    notes: List[str] = []
    notes.append("축 점수는 숫자를 그대로 나열하기보다 관계 국면의 방향성을 해석하는 보조 근거로만 사용한다.")
    notes.append("특히 종료 강도, 상대 개방성, 감정 동요, 충동성처럼 서로 충돌하는 신호가 있으면 그 충돌 자체를 설명해야 한다.")
    notes.append("축 점수만으로 상대의 마음이나 미래 행동을 단정하지 않는다.")

    return "\n".join(f"- {x}" for x in notes) + "\n" + _format_key_value_block(axis_scores)


def build_premium_report_prompt(result: Any) -> str:
    """
    engine 결과를 기반으로 GPT에 넣을 최종 프롬프트를 생성한다.

    이 함수는 계산을 하지 않으며,
    engine이 이미 계산한 결과를 서술 프롬프트로 구조화하는 역할만 담당한다.
    """
    safety_gate = _as_dict(_get(result, "safety_gate", {}))
    axis_scores = _as_dict(_get(result, "axis_scores", {}))
    semantic_tags = _as_list(_get(result, "semantic_tags", []))
    primary_labels = _as_list(_get(result, "primary_labels", []))
    secondary_labels = _as_list(_get(result, "secondary_labels", []))
    report_constraints = _as_list(_get(result, "report_constraints", []))
    confidence = _as_dict(_get(result, "confidence", {}))
    narrative_context = _as_dict(_get(result, "narrative_context", {}))

    safety_level_raw = str(safety_gate.get("level", "")).upper().strip()
    safety_level_display = _map_safety_level_kor(safety_level_raw)
    safety_reasons = _as_list(safety_gate.get("reasons", []))
    hard_constraints = _as_list(safety_gate.get("hard_constraints", []))

    situation_summary = str(narrative_context.get("situation_summary", "")).strip()
    state_summary = str(narrative_context.get("state_summary", "")).strip()
    risk_summary = str(narrative_context.get("risk_summary", "")).strip()
    contact_guidance_mode_raw = str(narrative_context.get("contact_guidance_mode", "")).upper().strip()
    contact_guidance_mode_display = _map_contact_mode_kor(contact_guidance_mode_raw)

    focus_points = _as_list(narrative_context.get("focus_points", []))
    do_not_do = _as_list(narrative_context.get("do_not_do", []))
    tone_hints = _as_list(narrative_context.get("tone_hints", []))
    model_notes = _as_list(narrative_context.get("model_notes", []))

    behavior_policy = _build_behavior_policy(
        safety_level=safety_level_raw,
        contact_guidance_mode=contact_guidance_mode_raw,
    )
    axis_inference_notes = _build_inference_notes(axis_scores)

    prompt = f"""당신은 리커넥트랩(ReconnectLab)의 프리미엄 리포트 작성 모델이다.

아래의 해석 엔진 결과를 바탕으로, 사용자에게 제공할 한국어 리포트를 작성하라.
이 리포트는 감정 자극용 콘텐츠가 아니라, 행동 리스크를 낮추고 자기조절을 돕는 실용적 분석 문서여야 한다.
핵심 목적은 재회를 밀어붙이는 것이 아니라, 감정적 충동으로 관계가 더 악화되거나 법적·안전상 문제가 생기는 일을 막는 것이다.

[리포트 성격]
- 위로형 에세이가 아니라 관계 분석 + 행동 운영 가이드 문서로 작성한다.
- 공감은 하되 과잉위로, 희망고문, 감정적 미화는 피한다.
- 사용자 입장에서 "내 상황을 제대로 읽은 것 같다"는 느낌이 들 정도로 구체적으로 쓴다.
- 누구에게나 적용되는 일반론보다, 현재 엔진 결과에서 드러난 패턴을 우선 설명한다.
- 한 섹션 안에서도 관찰 → 의미 → 행동 기준의 순서를 유지한다.
- 상대를 평가하는 문서가 아니라, 현재 관계 국면과 사용자의 행동 리스크를 읽는 문서로 작성한다.

[절대 금지 규칙]
- 재회 성공 확률, 가능성 퍼센트, 희망고문성 예측을 절대 쓰지 마라.
- 상대 심리를 단정하지 마라.
- 상대의 속마음, 후회 여부, 미래 행동을 예언하지 마라.
- 보내야 할 메시지 문장, 문자 예시, DM 예시를 생성하지 마라.
- 차단 상태, 거부 신호, 안전 제한을 무시하는 행동을 정당화하지 마라.
- 집착, 감시, 우회접촉, 반복연락, 찾아가기, 선물전달, 지인통한접촉을 부추기지 마라.
- 스토킹처벌법 위반 소지가 있는 행동을 조금이라도 합리화하지 마라.
- "상대방의 개방성이 높다", "재접촉 가능성이 있다" 같은 말만 던지고 근거 없이 기대감을 주지 마라.
- 의미 없는 상담 상투어를 남발하지 마라. 예: "시간이 해결해줄 것입니다", "자신을 사랑하세요", "진심은 통합니다"
- 엔진 내부 enum 값을 그대로 노출하지 마라. 예: LOW, ELEVATED, HIGH_RISK, HARD_BLOCK, NO_CONTACT_STRATEGY

[작성 원칙]
- 문체는 차분하고 단정하게 유지한다.
- 과도한 공감 과잉, 감정 선동, 자극적 표현을 피한다.
- 판단보다 관찰, 추정보다 제한 조건, 낙관보다 안전을 우선한다.
- 사용자가 지금 당장 실천할 수 있는 행동 기준을 제시한다.
- 해석 엔진 결과 바깥의 새로운 추론을 과하게 덧붙이지 마라.
- 특히 안전 관련 제한은 반드시 최우선으로 반영하라.
- 같은 말을 반복하지 말고, 각 섹션이 다른 기능을 담당하게 쓴다.
- "조심하세요", "신중하세요"처럼 추상적 문장만 쓰지 말고, 왜 위험한지와 무엇을 멈춰야 하는지 함께 쓴다.
- 실행 가이드는 적더라도 구체적으로 쓴다.
- 점수나 라벨은 원문을 복붙하듯 노출하지 말고, 관계의 현재 국면을 읽는 재료로만 써라.

[품질 기준]
- 이 리포트는 무료 리포트보다 한 단계 더 깊어야 한다.
- 단순한 위로문이나 범용 상담문처럼 보이면 안 된다.
- 사용자가 읽었을 때 "내 상황의 핵심 모순과 위험 패턴을 짚었다"는 느낌이 들어야 한다.
- 특히 관계에서 동시에 보이는 상반 신호가 있다면, 그 충돌을 분석하는 문장이 반드시 들어가야 한다.
- 예를 들어 종료 강도와 개방성이 동시에 높다면, "가능성"을 말하는 대신 "신호 혼재로 인해 오판하기 쉬운 국면"이라고 설명하는 식으로 쓴다.
- 사용자의 감정 동요와 행동 충동이 관계 리스크로 어떻게 연결되는지 분명히 써라.

[마크다운 출력 규칙]
- 반드시 한국어 마크다운으로만 출력한다.
- 맨 위에 리포트 제목 1개만 `#`로 쓴다.
- 아래 6개 섹션 제목은 반드시 `## 1. ...` 형식으로 정확히 작성한다.
- 각 섹션 안에서는 필요 시 `###` 소제목을 사용할 수 있다.
- 문단만 길게 이어 쓰지 말고, 핵심 기준은 불릿 리스트로 정리한다.
- 표는 사용하지 마라.
- 코드블록은 사용하지 마라.
- 마지막에 짧은 안전 메모 1개를 불릿으로 덧붙여도 된다.

[리포트 출력 형식]
반드시 아래 6개 섹션 제목을 그대로 사용하라.

## 1. 현재 상태 정밀 진단
## 2. 72시간 행동 가이드
## 3. 개인 위험 행동 3가지
## 4. 14일 감정 안정화 플랜
## 5. 재접촉 안전 기준
## 6. 전문가 도움 안내

[섹션별 작성 지침]
1. 현재 상태 정밀 진단
- 현재 관계 국면, 사용자의 정서 상태, 행동 리스크를 정리한다.
- situation_summary, state_summary, risk_summary를 핵심 근거로 사용한다.
- 상대에 대한 단정 대신 "현재 드러난 신호 기준"으로 표현한다.
- 첫 문단에서는 현재 관계를 한 줄로 요약하지 말고, 관계 신호가 왜 단순하지 않은지를 설명하라.
- 엔진 결과에 상반 신호가 있으면 그 충돌을 반드시 분석하라.
- axis_scores, labels, confidence는 보조 근거로만 쓰고, 점수 자체를 나열하지 마라.
- 사용자의 가장 큰 문제는 무엇이고, 지금 왜 보수적 접근이 필요한가를 분명히 드러내라.
- 안전 상태나 접촉 운영 모드를 언급할 때는 반드시 한국어 자연어로 풀어서 쓴다. 예: "{safety_level_display}", "{contact_guidance_mode_display}"

2. 72시간 행동 가이드
- 가장 급한 행동 제한과 감정 안정화 행동을 우선 제시한다.
- contact_guidance_mode와 safety_gate를 최우선 반영한다.
- "오늘 바로 멈출 것 / 3일 안에 회복할 것"처럼 나눠 쓰면 좋다.
- 감정 조절 조언만 쓰지 말고, 확인행동·반복행동·우회행동을 어떻게 제한할지 구체적으로 써라.
- 예: SNS 확인 횟수 제한, 전송 유예 원칙, 연락 충동 기록 후 즉시 전송 금지 같은 식의 운영 원칙
- 단, 메시지 예문이나 접촉 타이밍 팁은 금지다.

3. 개인 위험 행동 3가지
- 지금 사용자에게 특히 위험한 행동 패턴 3가지를 뽑아 설명한다.
- do_not_do, semantic_tags, safety_reasons를 근거로 삼는다.
- 각 항목은 반드시 아래 순서를 따른다.
  1) 위험 행동 이름
  2) 지금 이 사용자에게 왜 특히 위험한지
  3) 관계/법적/정서적 손실이 어떻게 커지는지
  4) 대신 할 행동
- 단순히 "위험하다"로 끝내지 말고, 지금 국면과 연결해 설명하라.

4. 14일 감정 안정화 플랜
- 감정 진정, 생활 루틴 회복, 확인행동 감소, 사고정리 중심으로 작성한다.
- focus_points를 반영한다.
- 비현실적 루틴이나 과장된 자기계발 조언은 피한다.
- 1주차와 2주차로 나눠도 좋고, 핵심 루틴 4~6개로 정리해도 된다.
- 중요한 건 "마음을 다스리세요"가 아니라, 확인행동을 줄이고 충동을 지연시키는 구조를 만드는 것이다.
- 무료 리포트처럼 뻔한 조언이 아니라, 실제로 행동을 바꾸는 설계처럼 보여야 한다.

5. 재접촉 안전 기준
- 접촉을 권유하는 섹션이 아니다.
- 접촉 가능 여부가 아니라 "접촉을 생각하더라도 최소한 어떤 조건을 먼저 점검해야 하는지"를 쓴다.
- NO_CONTACT_STRATEGY 또는 CONTACT_RESTRICTED면 비접촉/제한 원칙을 분명히 적는다.
- 차단, 명시적 거부, 반복충동 상태에서는 접촉 유보 원칙을 분명히 적는다.
- 접촉을 허용하는 뉘앙스보다, 접촉 판단 전에 필요한 안전 조건을 점검표처럼 제시한다.
- "이 조건을 충족하지 못하면 미루는 것이 맞다"는 기준을 분명히 써라.
- 메시지 문구, 타이밍 문구, 성공 팁은 제공하지 마라.

6. 전문가 도움 안내
- 치료를 강요하지 말고, 어떤 상황이면 전문가/상담/주변 도움을 받아야 하는지 안내한다.
- 기능저하, 충동통제 실패, 불면/식사 붕괴, 반복 확인행동, 불안 악화 등을 조건형으로 설명한다.
- "이런 경우에는 혼자 버티지 말고 도움을 받는 편이 안전하다"는 식의 현실적 문장으로 쓴다.
- 위기 징후가 있으면 가장 먼저 안전 확보와 주변 도움 요청을 말한다.

[문장 금지 예시]
아래처럼 쓰지 마라.
- "상대방의 개방성이 비교적 높게 나타납니다."
- "재회 가능성이 아주 없는 것은 아닙니다."
- "심호흡과 산책을 해보세요."
- "스스로를 사랑하세요."
- "시간이 필요합니다."
- "안전 게이트가 ELEVATED 상태입니다."

[문장 선호 예시]
아래처럼 쓰는 쪽이 낫다.
- "현재는 일부 반응 신호가 남아 있어도 관계 종료 강도가 강하게 형성된 국면이므로, 작은 반응을 관계 회복의 근거로 과대해석하기 쉬운 상태입니다."
- "문제는 관계가 완전히 열려 있지 않다는 점보다, 사용자가 혼재된 신호를 희망 근거로 읽을 가능성이 높다는 점입니다."
- "지금 72시간의 핵심은 관계를 진전시키는 행동이 아니라, 확인행동과 충동 반응을 끊어 추가 손실을 막는 것입니다."

[행동 제한 정책]
{behavior_policy}

[축 점수 해석 메모]
{axis_inference_notes}

[엔진 결과 요약 데이터]
- 안전 상태(한글): {safety_level_display or "-"}
- 안전 상태(raw): {safety_level_raw or "-"}
- 안전 사유: {_join_list(safety_reasons)}
- 강한 제한 조건: {_join_list(hard_constraints)}
- 접촉 운영 모드(한글): {contact_guidance_mode_display or "-"}
- 접촉 운영 모드(raw): {contact_guidance_mode_raw or "-"}

[서술용 narrative_context]
- situation_summary: {situation_summary or "-"}
- state_summary: {state_summary or "-"}
- risk_summary: {risk_summary or "-"}

- focus_points:
{_format_list_block(focus_points)}

- do_not_do:
{_format_list_block(do_not_do)}

- tone_hints:
{_format_list_block(tone_hints)}

- model_notes:
{_format_list_block(model_notes)}

[추가 해석 메타 데이터]
- primary_labels:
{_format_list_block(primary_labels)}

- secondary_labels:
{_format_list_block(secondary_labels)}

- semantic_tags:
{_format_list_block(semantic_tags)}

- report_constraints:
{_format_list_block(report_constraints)}

- axis_scores:
{_format_key_value_block(axis_scores)}

- confidence:
{_format_key_value_block(confidence)}

[최종 작성 지시]
위 데이터를 바탕으로, 실제 사용자에게 바로 제공 가능한 한국어 프리미엄 리포트를 작성하라.
리포트는 현실적이고 안전 중심이어야 하며, 각 섹션은 중복 없이 기능이 분명해야 한다.
확률 제시, 상대 심리 단정, 메시지 예문 생성은 절대 금지한다.
핵심은 "재회를 잘하는 법"이 아니라 "더 망치지 않는 법과 자기조절 기준"이다.
범용 상담문처럼 보이지 말고, 현재 국면의 모순·위험패턴·행동기준이 살아 있는 프리미엄 분석 문서처럼 작성하라.
엔진 내부 enum은 그대로 드러내지 말고, 반드시 자연스러운 한국어 상태 설명으로 풀어 써라.
"""

    return prompt