from __future__ import annotations


HIGH_STAKES_KEYWORDS = {
    "medical",
    "surgery",
    "diagnosis",
    "法律",
    "legal",
    "诉讼",
    "financial",
    "investment",
    "trading",
    "股票",
    "处方",
}


def assess_risk(
    task_shell: dict,
    gap_analysis: dict | None = None,
    executor: str | None = None,
) -> dict:
    gap_analysis = gap_analysis or {}
    task_type = task_shell.get("task_type", "generic")
    raw_request = (task_shell.get("raw_request") or "").lower()

    risk_level = "low"
    reasons = []
    decision = "auto_execute"
    requires_confirmation = False
    can_auto_execute = True

    if gap_analysis.get("need_user_input"):
        risk_level = "medium"
        decision = "needs_clarification"
        can_auto_execute = False
        reasons.append("Critical fields are still missing.")

    if task_type == "email":
        risk_level = _max_risk(risk_level, "medium")
        requires_confirmation = True
        reasons.append("Email tasks affect outbound communication quality.")

    if task_type == "code":
        risk_level = _max_risk(risk_level, "medium")
        reasons.append("Code tasks can introduce implementation regressions.")

    if executor and executor != "prompt_only" and task_type in {"email", "code"}:
        risk_level = _max_risk(risk_level, "high")
        requires_confirmation = True
        can_auto_execute = False
        decision = "needs_confirmation"
        reasons.append("Runnable execution for external-facing or code tasks should be explicitly confirmed.")

    if any(keyword in raw_request for keyword in HIGH_STAKES_KEYWORDS):
        risk_level = "high"
        requires_confirmation = True
        can_auto_execute = False
        decision = "needs_confirmation" if decision != "needs_clarification" else decision
        reasons.append("The request appears to be high-stakes.")

    if gap_analysis.get("need_user_input"):
        decision = "needs_clarification"
    elif risk_level == "high":
        decision = "needs_confirmation"

    return {
        "risk_level": risk_level,
        "decision": decision,
        "requires_confirmation": requires_confirmation,
        "can_auto_execute": can_auto_execute and decision == "auto_execute",
        "reasons": reasons,
    }


def _max_risk(left: str, right: str) -> str:
    order = {"low": 0, "medium": 1, "high": 2}
    return left if order[left] >= order[right] else right
