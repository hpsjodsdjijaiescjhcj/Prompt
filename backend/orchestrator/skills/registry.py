from __future__ import annotations

SKILLS = {
    "cold_email": {
        "name": "cold_email",
        "description": "Draft concise outreach/follow-up emails with clear next actions.",
        "task_types": {"email"},
        "expected_input_fields": ["clarified_request", "background", "recipient_type"],
        "recommended_validation_checks": ["tone_check", "deadline_check", "bullet_check"],
    },
    "resume_bullet": {
        "name": "resume_bullet",
        "description": "Convert project details into concise, impact-focused resume bullets.",
        "task_types": {"writing", "generic"},
        "expected_input_fields": ["clarified_request", "background"],
        "recommended_validation_checks": ["goal_validation", "constraint_validation"],
    },
    "sop_paragraph": {
        "name": "sop_paragraph",
        "description": "Generate a focused SOP paragraph aligned to audience and objective.",
        "task_types": {"writing"},
        "expected_input_fields": ["clarified_request", "audience", "background"],
        "recommended_validation_checks": ["goal_validation", "style_validation"],
    },
    "task_breakdown": {
        "name": "task_breakdown",
        "description": "Break vague requests into executable subtasks with dependencies.",
        "task_types": {"generic", "code"},
        "expected_input_fields": ["clarified_request", "primary_target"],
        "recommended_validation_checks": ["schema_validation", "dependency_validation"],
    },
}


def list_skills() -> list[dict]:
    return [dict(v) for v in SKILLS.values()]


def recommend_skills(task_type: str, raw_request: str, top_n: int = 2) -> list[dict]:
    scores = []
    text = (raw_request or "").lower()
    for skill in SKILLS.values():
        if task_type not in skill["task_types"]:
            continue
        score = 0.4
        if skill["name"] == "cold_email" and any(k in text for k in ("邮件", "email", "follow-up", "invoice", "供应商")):
            score += 0.5
        if skill["name"] == "resume_bullet" and any(k in text for k in ("简历", "resume", "bullet")):
            score += 0.5
        if skill["name"] == "sop_paragraph" and any(k in text for k in ("sop", "statement", "申请文书")):
            score += 0.5
        if skill["name"] == "task_breakdown" and any(k in text for k in ("拆解", "breakdown", "步骤", "plan")):
            score += 0.5
        scores.append(
            {
                "name": skill["name"],
                "description": skill["description"],
                "expected_input_fields": list(skill["expected_input_fields"]),
                "recommended_validation_checks": list(skill["recommended_validation_checks"]),
                "score": min(score, 1.0),
            }
        )
    scores.sort(key=lambda x: x["score"], reverse=True)
    return scores[:top_n]


def select_primary_skill(task_type: str, raw_request: str) -> dict | None:
    candidates = recommend_skills(task_type, raw_request, top_n=1)
    return candidates[0] if candidates else None
