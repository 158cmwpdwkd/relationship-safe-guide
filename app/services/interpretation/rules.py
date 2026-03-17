# app/services/interpretation/rules.py

from __future__ import annotations

from typing import Any, Dict, List

from .schemas import RuleApplication


# --------------------------------------------------
# Axis definitions
# --------------------------------------------------

AXES = {
    "immediate_risk",
    "emotional_fusion",
    "relationship_foundation",
    "closure_strength",
    "partner_openness",
    "contact_pressure",
    "stabilization_priority",
}


# --------------------------------------------------
# Question metadata
# --------------------------------------------------

QUESTION_META: Dict[str, Dict[str, Any]] = {
    "PAID_Q1_duration": {"type": "single", "label": "관계 기간"},
    "PAID_Q2_relationship_weight": {"type": "single", "label": "관계 무게감"},
    "PAID_Q3_reunion_history": {"type": "single", "label": "반복 이력"},
    "PAID_Q4_breakup_timing": {"type": "single", "label": "이별 시점"},
    "PAID_Q5_last_contact_timing": {"type": "single", "label": "마지막 연락"},
    "PAID_Q6_breakup_initiator": {"type": "single", "label": "이별 주도권"},
    "PAID_Q7_breakup_reason": {"type": "single", "label": "이별 원인"},
    "PAID_Q8_issue_severity": {"type": "single", "label": "문제 심각도"},
    "PAID_Q9_last_conversation_mood": {"type": "single", "label": "마지막 대화 분위기"},
    "PAID_Q10_conflict_pattern": {"type": "single", "label": "갈등 패턴"},
    "PAID_Q11_partner_conflict_response": {"type": "single", "label": "상대 갈등 반응"},
    "PAID_Q12_my_problem_behavior": {"type": "single", "label": "내 문제 행동"},
    "PAID_Q13_channel_state": {"type": "single", "label": "현재 연락 채널 상태"},
    "PAID_Q14_recent_signal": {"type": "single", "label": "최근 상대 신호"},
    "PAID_Q15_contact_after_reject": {"type": "single", "label": "거절 후 재접촉"},
    "PAID_Q16_response_after_contact": {"type": "single", "label": "재접촉 후 반응"},
    "PAID_Q17_regret_freq": {"type": "single", "label": "후회/미련 빈도"},
    "PAID_Q18_impulse_action": {"type": "multi", "label": "충동 행동"},
    "PAID_Q19_changes_2w": {"type": "multi", "label": "최근 2주 변화"},
    "PAID_Q20_goal": {"type": "single", "label": "현재 목표"},
}


# --------------------------------------------------
# Single-choice rules
# --------------------------------------------------

SINGLE_RULES: Dict[str, Dict[str, Dict[str, Any]]] = {
    # Q1
    "PAID_Q1_duration": {
        "short": {
            "score_effects": {"relationship_foundation": 10},
            "tags": ["short_relationship"],
            "overrides": {},
            "safety_flags": [],
        },
        "early": {
            "score_effects": {"relationship_foundation": 20},
            "tags": ["early_relationship"],
            "overrides": {},
            "safety_flags": [],
        },
        "stable": {
            "score_effects": {"relationship_foundation": 40},
            "tags": ["stable_relationship"],
            "overrides": {},
            "safety_flags": [],
        },
        "deep": {
            "score_effects": {"relationship_foundation": 65},
            "tags": ["deep_relationship"],
            "overrides": {},
            "safety_flags": [],
        },
        "family": {
            "score_effects": {"relationship_foundation": 80},
            "tags": ["family_level_relationship_duration"],
            "overrides": {},
            "safety_flags": [],
        },
    },

    # Q2
    "PAID_Q2_relationship_weight": {
        "some": {
            "score_effects": {"relationship_foundation": 8},
            "tags": ["ambiguous_relationship"],
            "overrides": {},
            "safety_flags": [],
        },
        "dating_light": {
            "score_effects": {"relationship_foundation": 22},
            "tags": ["light_dating_relationship"],
            "overrides": {},
            "safety_flags": [],
        },
        "dating_clear": {
            "score_effects": {"relationship_foundation": 48},
            "tags": ["clear_relationship"],
            "overrides": {},
            "safety_flags": [],
        },
        "serious": {
            "score_effects": {"relationship_foundation": 70},
            "tags": ["serious_relationship_future_talk"],
            "overrides": {},
            "safety_flags": [],
        },
        "family_level": {
            "score_effects": {"relationship_foundation": 86},
            "tags": ["cohabitation_or_marriage_level_relationship"],
            "overrides": {},
            "safety_flags": [],
        },
    },

    # Q3
    "PAID_Q3_reunion_history": {
        "never": {
            "score_effects": {"partner_openness": 5, "closure_strength": 22},
            "tags": ["no_reunion_history"],
            "overrides": {},
            "safety_flags": [],
        },
        "once": {
            "score_effects": {"partner_openness": 28, "relationship_foundation": 10},
            "tags": ["one_reunion_history"],
            "overrides": {},
            "safety_flags": [],
        },
        "multi": {
            "score_effects": {
                "partner_openness": 40,
                "relationship_foundation": 14,
                "emotional_fusion": 12,
            },
            "tags": ["multiple_reunion_history", "on_off_cycle_possible"],
            "overrides": {},
            "safety_flags": ["cyclical_relationship_pattern"],
        },
        "unclear": {
            "score_effects": {},
            "tags": ["reunion_history_unclear"],
            "overrides": {"confidence_penalty": 5},
            "safety_flags": [],
        },
    },

    # Q4
    "PAID_Q4_breakup_timing": {
        "d3": {
            "score_effects": {"immediate_risk": 72, "closure_strength": 8},
            "tags": ["fresh_breakup_3d"],
            "overrides": {},
            "safety_flags": ["fresh_breakup"],
        },
        "w1": {
            "score_effects": {"immediate_risk": 60, "closure_strength": 18},
            "tags": ["fresh_breakup_1w"],
            "overrides": {},
            "safety_flags": ["fresh_breakup"],
        },
        "w2_4": {
            "score_effects": {"immediate_risk": 45, "closure_strength": 35},
            "tags": ["breakup_2_to_4_weeks"],
            "overrides": {},
            "safety_flags": [],
        },
        "m1_3": {
            "score_effects": {"immediate_risk": 25, "closure_strength": 55},
            "tags": ["breakup_1_to_3_months"],
            "overrides": {},
            "safety_flags": [],
        },
        "m3_plus": {
            "score_effects": {"immediate_risk": 10, "closure_strength": 72},
            "tags": ["breakup_over_3_months"],
            "overrides": {},
            "safety_flags": [],
        },
    },

    # Q5
    "PAID_Q5_last_contact_timing": {
        "today_3d": {
            "score_effects": {"partner_openness": 45, "closure_strength": 10},
            "tags": ["very_recent_contact"],
            "overrides": {},
            "safety_flags": [],
        },
        "w1": {
            "score_effects": {"partner_openness": 35, "closure_strength": 20},
            "tags": ["recent_contact_within_1_week"],
            "overrides": {},
            "safety_flags": [],
        },
        "w2_4": {
            "score_effects": {"partner_openness": 20, "closure_strength": 40},
            "tags": ["contact_2_to_4_weeks_ago"],
            "overrides": {},
            "safety_flags": [],
        },
        "m1_3": {
            "score_effects": {"partner_openness": 10, "closure_strength": 60},
            "tags": ["contact_1_to_3_months_ago"],
            "overrides": {},
            "safety_flags": [],
        },
        "m3_plus": {
            "score_effects": {"partner_openness": 0, "closure_strength": 75},
            "tags": ["no_contact_over_3_months"],
            "overrides": {},
            "safety_flags": [],
        },
        "unknown": {
            "score_effects": {},
            "tags": ["last_contact_timing_unknown"],
            "overrides": {"confidence_penalty": 5},
            "safety_flags": [],
        },
    },

    # Q6
    "PAID_Q6_breakup_initiator": {
        "me": {
            "score_effects": {"closure_strength": 24, "partner_openness": 20},
            "tags": ["user_initiated_breakup"],
            "overrides": {},
            "safety_flags": [],
        },
        "other": {
            "score_effects": {"closure_strength": 48, "partner_openness": 5},
            "tags": ["partner_initiated_breakup"],
            "overrides": {},
            "safety_flags": [],
        },
        "mutual": {
            "score_effects": {"closure_strength": 32, "partner_openness": 16},
            "tags": ["mutual_breakup"],
            "overrides": {},
            "safety_flags": [],
        },
        "unclear": {
            "score_effects": {"closure_strength": 20},
            "tags": ["ambiguous_breakup_initiation"],
            "overrides": {"confidence_penalty": 5},
            "safety_flags": [],
        },
    },

   # Q7
    "PAID_Q7_breakup_reason": {
        "personality_values": {
            "score_effects": {"closure_strength": 38},
            "tags": ["breakup_due_to_personality_or_values"],
            "overrides": {},
            "safety_flags": [],
        },
        "trust": {
            "score_effects": {"closure_strength": 60, "partner_openness": 0},
            "tags": ["trust_damage_breakup"],
            "overrides": {},
            "safety_flags": ["trust_break"],
        },
        "distance_env": {
            "score_effects": {"closure_strength": 24, "partner_openness": 25},
            "tags": ["distance_or_environment_issue"],
            "overrides": {},
            "safety_flags": [],
        },
        "family": {
            "score_effects": {"closure_strength": 48, "partner_openness": 10},
            "tags": ["family_or_social_opposition_issue"],
            "overrides": {},
            "safety_flags": [],
        },
        "fight": {
            "score_effects": {"closure_strength": 42},
            "tags": ["repeated_conflict_breakup"],
            "overrides": {},
            "safety_flags": [],
        },
        "one_sided": {
            "score_effects": {"closure_strength": 58, "partner_openness": 5},
            "tags": ["one_sided_feeling_loss"],
            "overrides": {},
            "safety_flags": [],
        },
        "life_stage": {
            "score_effects": {"closure_strength": 28, "partner_openness": 20},
            "tags": ["life_stage_change_issue"],
            "overrides": {},
            "safety_flags": [],
        },
        "other": {
            "score_effects": {"closure_strength": 28},
            "tags": ["other_breakup_reason"],
            "overrides": {"needs_text_context": True, "confidence_penalty": 5},
            "safety_flags": [],
        },
    },

    # Q8
    "PAID_Q8_issue_severity": {
        "light": {
            "score_effects": {"closure_strength": 10, "partner_openness": 30},
            "tags": ["issue_severity_light"],
            "overrides": {},
            "safety_flags": [],
        },
        "mid": {
            "score_effects": {"closure_strength": 28, "partner_openness": 20},
            "tags": ["issue_severity_mid"],
            "overrides": {},
            "safety_flags": [],
        },
        "high": {
            "score_effects": {"closure_strength": 45, "partner_openness": 10},
            "tags": ["issue_severity_high"],
            "overrides": {},
            "safety_flags": [],
        },
        "very_high": {
            "score_effects": {"closure_strength": 65, "partner_openness": 0},
            "tags": ["issue_severity_very_high"],
            "overrides": {},
            "safety_flags": ["high_damage_breakup"],
        },
        "unknown": {
            "score_effects": {},
            "tags": ["issue_severity_unknown"],
            "overrides": {"confidence_penalty": 5},
            "safety_flags": [],
        },
    },

    # Q9
    "PAID_Q9_last_conversation_mood": {
        "emotional": {
            "score_effects": {"immediate_risk": 15, "closure_strength": 35},
            "tags": ["last_conversation_highly_emotional"],
            "overrides": {},
            "safety_flags": ["emotionally_heated_recent_context"],
        },
        "cold_clear": {
            "score_effects": {"closure_strength": 62, "partner_openness": 4},
            "tags": ["last_conversation_cold_but_clear"],
            "overrides": {},
            "safety_flags": ["clear_ending_signal"],
        },
        "mixed": {
            "score_effects": {"closure_strength": 24, "partner_openness": 18},
            "tags": ["last_conversation_mixed_closure_and_attachment"],
            "overrides": {"confidence_penalty": 6},
            "safety_flags": [],
        },
        "soft_unclear": {
            "score_effects": {"closure_strength": 18, "partner_openness": 25},
            "tags": ["last_conversation_soft_but_unclear"],
            "overrides": {},
            "safety_flags": [],
        },
        "sudden_cut": {
            "score_effects": {"closure_strength": 58, "partner_openness": 2, "immediate_risk": 10},
            "tags": ["last_conversation_sudden_cutoff"],
            "overrides": {},
            "safety_flags": ["abrupt_disconnection"],
        },
        "unknown": {
            "score_effects": {},
            "tags": ["last_conversation_mood_unknown"],
            "overrides": {"confidence_penalty": 5},
            "safety_flags": [],
        },
    },

    # Q10
    "PAID_Q10_conflict_pattern": {
        "pursue_avoid": {
            "score_effects": {"emotional_fusion": 20, "contact_pressure": 18, "closure_strength": 22},
            "tags": ["pursue_avoid_cycle"],
            "overrides": {},
            "safety_flags": ["pressure_cycle_risk"],
        },
        "mutual_explosion": {
            "score_effects": {"immediate_risk": 12, "closure_strength": 42},
            "tags": ["mutual_emotional_escalation_pattern"],
            "overrides": {},
            "safety_flags": ["volatile_pattern"],
        },
        "silent_cutoff": {
            "score_effects": {"closure_strength": 45, "partner_openness": 5},
            "tags": ["silent_cutoff_pattern"],
            "overrides": {},
            "safety_flags": ["avoidant_disconnection_pattern"],
        },
        "one_sided_endure": {
            "score_effects": {"closure_strength": 35, "relationship_foundation": 5},
            "tags": ["one_sided_endure_then_burst_pattern"],
            "overrides": {},
            "safety_flags": [],
        },
        "repeat_same": {
            "score_effects": {"closure_strength": 38},
            "tags": ["repeated_same_conflict_pattern"],
            "overrides": {},
            "safety_flags": [],
        },
        "unknown": {
            "score_effects": {},
            "tags": ["conflict_pattern_unknown"],
            "overrides": {"confidence_penalty": 5},
            "safety_flags": [],
        },
    },

    # Q11
    "PAID_Q11_partner_conflict_response": {
        "talk_now": {
            "score_effects": {"partner_openness": 42},
            "tags": ["partner_tends_to_talk_immediately"],
            "overrides": {},
            "safety_flags": [],
        },
        "need_time": {
            "score_effects": {"partner_openness": 28},
            "tags": ["partner_needs_time_before_talking"],
            "overrides": {},
            "safety_flags": [],
        },
        "avoid": {
            "score_effects": {"partner_openness": 10, "closure_strength": 10},
            "tags": ["partner_avoids_conflict_dialogue"],
            "overrides": {},
            "safety_flags": [],
        },
        "silent": {
            "score_effects": {"partner_openness": 0, "closure_strength": 55},
            "tags": ["partner_silent_or_cutoff_response"],
            "overrides": {"force_constraint": "respect_silence_boundary"},
            "safety_flags": ["partner_hard_boundary"],
        },
        "burst": {
            "score_effects": {"immediate_risk": 10, "closure_strength": 30},
            "tags": ["partner_bursts_emotionally_in_conflict"],
            "overrides": {},
            "safety_flags": ["volatile_pattern"],
        },
        "unknown": {
            "score_effects": {},
            "tags": ["partner_conflict_response_unknown"],
            "overrides": {"confidence_penalty": 5},
            "safety_flags": [],
        },
    },

    # Q12
    "PAID_Q12_my_problem_behavior": {
        "press": {
            "score_effects": {"contact_pressure": 35, "closure_strength": 8},
            "tags": ["self_report_pressure_behavior"],
            "overrides": {},
            "safety_flags": ["pressure_behavior"],
        },
        "avoid": {
            "score_effects": {"closure_strength": 12},
            "tags": ["self_report_avoidance"],
            "overrides": {},
            "safety_flags": [],
        },
        "explode": {
            "score_effects": {"immediate_risk": 10, "emotional_fusion": 20, "closure_strength": 15},
            "tags": ["self_report_emotional_explosion"],
            "overrides": {},
            "safety_flags": ["emotional_reactivity"],
        },
        "test": {
            "score_effects": {"emotional_fusion": 20, "contact_pressure": 15},
            "tags": ["self_report_testing_reactions"],
            "overrides": {},
            "safety_flags": ["testing_behavior"],
        },
        "lie_hide": {
            "score_effects": {"closure_strength": 25, "partner_openness": 0},
            "tags": ["self_report_hiding_or_lying"],
            "overrides": {},
            "safety_flags": ["trust_break"],
        },
        "jealous": {
            "score_effects": {"contact_pressure": 38, "closure_strength": 15},
            "tags": ["self_report_jealousy_or_control"],
            "overrides": {},
            "safety_flags": ["control_risk"],
        },
        "neglect": {
            "score_effects": {"closure_strength": 18},
            "tags": ["self_report_neglect_or_distance"],
            "overrides": {},
            "safety_flags": [],
        },
        "none_clear": {
            "score_effects": {},
            "tags": ["no_clear_self_problem_behavior_reported"],
            "overrides": {},
            "safety_flags": [],
        },
    },

    # Q13
    "PAID_Q13_channel_state": {
        "all_blocked": {
            "score_effects": {"partner_openness": 0, "closure_strength": 70},
            "tags": ["all_channels_blocked"],
            "overrides": {"force_constraint": "respect_block"},
            "safety_flags": ["hard_boundary", "blocked_state"],
        },
        "no_reply": {
            "score_effects": {"partner_openness": 5, "closure_strength": 48},
            "tags": ["message_delivered_but_no_reply"],
            "overrides": {},
            "safety_flags": ["distance_signal"],
        },
        "partial_open": {
            "score_effects": {"partner_openness": 18, "closure_strength": 25},
            "tags": ["partially_open_channels"],
            "overrides": {},
            "safety_flags": ["boundary_signal"],
        },
        "normal": {
            "score_effects": {"partner_openness": 45, "closure_strength": 8},
            "tags": ["communication_channel_open"],
            "overrides": {},
            "safety_flags": [],
        },
        "unknown": {
            "score_effects": {},
            "tags": ["channel_state_unknown"],
            "overrides": {"confidence_penalty": 5},
            "safety_flags": [],
        },
    },

        # Q14
    "PAID_Q14_recent_signal": {
        "none": {
            "score_effects": {"partner_openness": 0, "closure_strength": 38},
            "tags": ["no_recent_signal"],
            "overrides": {},
            "safety_flags": [],
        },
        "neutral_open": {
            "score_effects": {"partner_openness": 15},
            "tags": ["neutral_but_not_closed_signal"],
            "overrides": {},
            "safety_flags": [],
        },
        "small_response": {
            "score_effects": {"partner_openness": 35},
            "tags": ["small_response_signal"],
            "overrides": {},
            "safety_flags": [],
        },
        "indirect_signal": {
            "score_effects": {"partner_openness": 20},
            "tags": ["indirect_signal_present"],
            "overrides": {},
            "safety_flags": [],
        },
        "mixed_signal": {
            "score_effects": {"partner_openness": 18},
            "tags": ["mixed_signal_repeated"],
            "overrides": {"confidence_penalty": 8},
            "safety_flags": [],
        },
        "unknown": {
            "score_effects": {},
            "tags": ["recent_signal_unknown"],
            "overrides": {"confidence_penalty": 5},
            "safety_flags": [],
        },
    },

    # Q15
    "PAID_Q15_contact_after_reject": {
        "no": {
            "score_effects": {"contact_pressure": 0},
            "tags": ["no_contact_after_rejection"],
            "overrides": {},
            "safety_flags": [],
        },
        "once_twice": {
            "score_effects": {"contact_pressure": 30},
            "tags": ["limited_contact_after_rejection"],
            "overrides": {},
            "safety_flags": [],
        },
        "repeated": {
            "score_effects": {"contact_pressure": 68, "immediate_risk": 20},
            "tags": ["repeated_contact_after_rejection"],
            "overrides": {},
            "safety_flags": ["repeat_contact_after_reject"],
        },
        "bypass": {
            "score_effects": {"contact_pressure": 92, "immediate_risk": 35},
            "tags": ["bypass_contact_after_rejection"],
            "overrides": {"force_constraint": "no_bypass_contact"},
            "safety_flags": ["bypass_contact", "high_boundary_risk"],
        },
    },

    # Q16
    "PAID_Q16_response_after_contact": {
        "ignored": {
            "score_effects": {"partner_openness": 0, "closure_strength": 55},
            "tags": ["contact_ignored"],
            "overrides": {},
            "safety_flags": ["ignored_after_contact"],
        },
        "cold_reject": {
            "score_effects": {"partner_openness": 0, "closure_strength": 65},
            "tags": ["cold_rejection_after_contact"],
            "overrides": {"force_constraint": "no_direct_contact_push"},
            "safety_flags": ["explicit_rejection_signal"],
        },
        "polite_distance": {
            "score_effects": {"partner_openness": 10, "closure_strength": 45},
            "tags": ["polite_but_distant_response"],
            "overrides": {},
            "safety_flags": ["distance_signal"],
        },
        "mixed": {
            "score_effects": {"partner_openness": 18},
            "tags": ["mixed_response_after_contact"],
            "overrides": {"confidence_penalty": 8},
            "safety_flags": [],
        },
        "soft_open": {
            "score_effects": {"partner_openness": 35},
            "tags": ["soft_open_response"],
            "overrides": {},
            "safety_flags": [],
        },
        "no_contact": {
            "score_effects": {},
            "tags": ["no_recontact_attempt_yet"],
            "overrides": {},
            "safety_flags": [],
        },
    },

    # Q17
    "PAID_Q17_regret_freq": {
        "lt20": {
            "score_effects": {"emotional_fusion": 5, "immediate_risk": 5},
            "tags": ["low_regret_frequency"],
            "overrides": {},
            "safety_flags": [],
        },
        "m20_50": {
            "score_effects": {"emotional_fusion": 20, "immediate_risk": 10},
            "tags": ["moderate_regret_frequency"],
            "overrides": {},
            "safety_flags": [],
        },
        "m50_70": {
            "score_effects": {"emotional_fusion": 45, "immediate_risk": 20},
            "tags": ["high_regret_frequency"],
            "overrides": {},
            "safety_flags": [],
        },
        "m70_90": {
            "score_effects": {"emotional_fusion": 70, "immediate_risk": 30},
            "tags": ["very_high_regret_frequency"],
            "overrides": {},
            "safety_flags": ["high_emotional_preoccupation"],
        },
        "gt90": {
            "score_effects": {"emotional_fusion": 90, "immediate_risk": 45},
            "tags": ["extreme_regret_frequency"],
            "overrides": {},
            "safety_flags": ["extreme_emotional_preoccupation"],
        },
    },

    # Q20
    "PAID_Q20_goal": {
        "reconnect": {
            "score_effects": {"contact_pressure": 15, "emotional_fusion": 10},
            "tags": ["goal_reconnect"],
            "overrides": {},
            "safety_flags": [],
        },
        "reconcile": {
            "score_effects": {"contact_pressure": 25, "emotional_fusion": 20},
            "tags": ["goal_reconcile"],
            "overrides": {},
            "safety_flags": [],
        },
        "closure": {
            "score_effects": {"closure_strength": 10},
            "tags": ["goal_seek_closure"],
            "overrides": {},
            "safety_flags": [],
        },
        "stabilize": {
            "score_effects": {"stabilization_priority": 50},
            "tags": ["goal_self_stabilization"],
            "overrides": {},
            "safety_flags": [],
        },
        "unsure": {
            "score_effects": {"stabilization_priority": 20},
            "tags": ["goal_unclear"],
            "overrides": {"confidence_penalty": 5},
            "safety_flags": [],
        },
    },
}


# --------------------------------------------------
# Multi-choice rules
# --------------------------------------------------

MULTI_RULES: Dict[str, Dict[str, Dict[str, Any]]] = {
    "PAID_Q18_impulse_action": {
        "sns_stalk": {
            "score_effects": {"emotional_fusion": 10, "contact_pressure": 5},
            "tags": ["impulse_sns_stalking"],
            "overrides": {},
            "safety_flags": [],
        },
        "contact": {
            "score_effects": {"contact_pressure": 20, "immediate_risk": 10},
            "tags": ["impulse_contact_attempt"],
            "overrides": {},
            "safety_flags": ["impulse_contact"],
        },
        "write_delete": {
            "score_effects": {"emotional_fusion": 15},
            "tags": ["impulse_write_delete_messages"],
            "overrides": {},
            "safety_flags": [],
        },
        "call_repeat": {
            "score_effects": {"contact_pressure": 30, "immediate_risk": 15},
            "tags": ["impulse_repeat_calls"],
            "overrides": {},
            "safety_flags": ["repeat_call_risk"],
        },
        "check_last_seen": {
            "score_effects": {"emotional_fusion": 15},
            "tags": ["impulse_check_last_seen"],
            "overrides": {},
            "safety_flags": [],
        },
        "photo_review": {
            "score_effects": {"emotional_fusion": 12},
            "tags": ["impulse_review_photos_or_chats"],
            "overrides": {},
            "safety_flags": [],
        },
        "none": {
            "score_effects": {},
            "tags": ["no_impulse_action_selected"],
            "overrides": {},
            "safety_flags": [],
        },
    },

    "PAID_Q19_changes_2w": {
        "sleep_appetite": {
            "score_effects": {"immediate_risk": 15, "stabilization_priority": 10},
            "tags": ["recent_sleep_or_appetite_change"],
            "overrides": {},
            "safety_flags": ["functional_change"],
        },
        "focus_down": {
            "score_effects": {"immediate_risk": 12, "stabilization_priority": 10},
            "tags": ["recent_focus_drop"],
            "overrides": {},
            "safety_flags": ["functional_change"],
        },
        "work_drop": {
            "score_effects": {"immediate_risk": 20, "stabilization_priority": 15},
            "tags": ["recent_daily_function_drop"],
            "overrides": {},
            "safety_flags": ["significant_functional_drop"],
        },
        "mood_swing": {
            "score_effects": {
                "immediate_risk": 18,
                "emotional_fusion": 10,
                "stabilization_priority": 10,
            },
            "tags": ["recent_mood_instability"],
            "overrides": {},
            "safety_flags": ["mood_instability"],
        },
        "social_cut": {
            "score_effects": {"immediate_risk": 10, "stabilization_priority": 10},
            "tags": ["recent_social_withdrawal"],
            "overrides": {},
            "safety_flags": ["social_withdrawal"],
        },
        "none": {
            "score_effects": {},
            "tags": ["no_recent_change_selected"],
            "overrides": {},
            "safety_flags": [],
        },
    },
}


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def _sanitize_score_effects(score_effects: Dict[str, int]) -> Dict[str, int]:
    clean: Dict[str, int] = {}
    for axis, value in score_effects.items():
        if axis not in AXES:
            raise ValueError(f"Unknown axis in score_effects: {axis}")
        clean[axis] = int(value)
    return clean


def _build_rule_application(
    question_id: str,
    answer_value: str,
    raw_rule: Dict[str, Any],
) -> RuleApplication:
    return RuleApplication(
        question_id=question_id,
        answer_value=answer_value,
        score_effects=_sanitize_score_effects(raw_rule.get("score_effects", {})),
        semantic_tags=list(raw_rule.get("tags", [])),
        overrides=dict(raw_rule.get("overrides", {})),
        safety_flags=list(raw_rule.get("safety_flags", [])),
    )


# --------------------------------------------------
# Public API
# --------------------------------------------------

def get_question_meta(question_id: str) -> Dict[str, Any]:
    if question_id not in QUESTION_META:
        raise KeyError(f"Unknown question_id: {question_id}")
    return QUESTION_META[question_id]


def get_single_rule(question_id: str, answer_value: str) -> RuleApplication:
    if question_id not in SINGLE_RULES:
        raise KeyError(f"Unknown single-choice question_id: {question_id}")

    question_rules = SINGLE_RULES[question_id]
    if answer_value not in question_rules:
        raise KeyError(f"Unknown answer '{answer_value}' for question '{question_id}'")

    return _build_rule_application(question_id, answer_value, question_rules[answer_value])


def get_multi_rules(question_id: str, answer_values: List[str]) -> List[RuleApplication]:
    if question_id not in MULTI_RULES:
        raise KeyError(f"Unknown multi-choice question_id: {question_id}")

    question_rules = MULTI_RULES[question_id]
    results: List[RuleApplication] = []

    for answer_value in answer_values:
        if answer_value not in question_rules:
            raise KeyError(f"Unknown answer '{answer_value}' for question '{question_id}'")
        results.append(_build_rule_application(question_id, answer_value, question_rules[answer_value]))

    return results


def extract_rule_applications(paid_answers: Dict[str, Any]) -> List[RuleApplication]:
    """
    프론트에서 넘어온 answers dict를 받아 RuleApplication 리스트로 변환한다.
    단일선택은 1개, 다중선택은 선택 개수만큼 생성된다.
    """
    results: List[RuleApplication] = []

    for question_id, meta in QUESTION_META.items():
        if question_id not in paid_answers:
            continue

        answer_value = paid_answers[question_id]
        q_type = meta["type"]

        if q_type == "single":
            if answer_value in (None, ""):
                continue
            results.append(get_single_rule(question_id, str(answer_value)))

        elif q_type == "multi":
            if not answer_value:
                continue
            if not isinstance(answer_value, list):
                raise TypeError(f"{question_id} must be a list for multi-choice questions")
            results.extend(get_multi_rules(question_id, [str(v) for v in answer_values_normalized(answer_value)]))

        else:
            raise ValueError(f"Unsupported question type: {q_type}")

    # Q7 기타 텍스트 처리
    q7_value = paid_answers.get("PAID_Q7_breakup_reason")
    q7_other = (paid_answers.get("PAID_Q7_breakup_reason_other_text") or "").strip()

    if q7_value == "other" and q7_other:
        results.append(
            RuleApplication(
                question_id="PAID_Q7_breakup_reason_other_text",
                answer_value=q7_other,
                score_effects={},
                semantic_tags=["breakup_reason_other_text_present"],
                overrides={"text_context": q7_other},
                safety_flags=[],
            )
        )

    return results


def answer_values_normalized(values: List[Any]) -> List[str]:
    """
    multi choice 정규화:
    - 문자열화
    - 중복 제거
    - 순서 유지
    """
    seen = set()
    normalized: List[str] = []

    for value in values:
        s = str(value)
        if s in seen:
            continue
        seen.add(s)
        normalized.append(s)

    return normalized