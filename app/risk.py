from typing import List, Tuple

def compute_risk(q1: int, q2: int, q3: int, red_flags: List[str]) -> Tuple[int, int, bool, str]:
    impulse = q1 + q2 + q3  # 3~15
    # "해당 없음" 제외
    picked = [x for x in red_flags if x and x != "해당 없음"]
    red_count = len(picked)
    has_threat = any("위협" in x for x in picked)

    if has_threat or red_count >= 3:
        level = "HARD_BLOCK"
    elif red_count >= 1:
        level = "SOFT_GATE"
    elif impulse >= 11:
        level = "HIGH"
    elif impulse >= 7:
        level = "MEDIUM"
    else:
        level = "LOW"

    return impulse, red_count, has_threat, level