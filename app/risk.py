# app/risk.py
from typing import List

def compute_risk(answers: dict) -> dict:
    q1 = int(answers["FREE_Q1_stop_work_7d"])
    q2 = int(answers["FREE_Q2_sns_check_yesterday"])
    q3 = int(answers["FREE_Q3_impulse_control_rate"])
    q3_map = {
        10: 5,
        30: 4,
        50: 3,
        70: 2,
        90: 1
    }
    
    q3_scores = q3_map.get(q3, 3)

    red_flags: List[str] = answers.get("FREE_Q5_red_flags", [])
    if "rf_none" in red_flags and len(red_flags) > 1:
        red_flags = ["rf_none"]  # 서버에서도 방어

    impulse_index = q1 + q2 + q3_scores
    red_flag_count = len([x for x in red_flags if x != "rf_none"])
    has_threat = "rf_threat_msg" in red_flags

    if has_threat or red_flag_count >= 3:
        risk_level = "HARD_BLOCK"
    elif red_flag_count >= 1:
        risk_level = "SOFT_GATE"
    elif impulse_index >= 11:
        risk_level = "HIGH"
    elif impulse_index >= 7:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "impulse_index": impulse_index,
        "red_flag_count": red_flag_count,
        "has_threat": has_threat,
        "risk_level": risk_level,
    }