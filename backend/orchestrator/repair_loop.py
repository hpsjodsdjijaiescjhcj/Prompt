from __future__ import annotations

from .executor import run_executor


def build_repair_plan(report: dict, lightweight_validation: dict, logic_validation: dict) -> dict:
    issues = list(report.get("issues") or [])
    lightweight_repairs = list(lightweight_validation.get("suggested_repairs") or [])
    repair_prompt = (report.get("suggested_fix_prompt") or "").strip()
    should_attempt = bool(issues and repair_prompt)
    return {
        "should_attempt": should_attempt,
        "issue_count": len(issues),
        "lightweight_repairs": lightweight_repairs,
        "repair_prompt": repair_prompt,
        "logic_risk_level": logic_validation.get("risk_level", "low"),
    }


def attempt_repair_once(
    execution: dict,
    repair_plan: dict,
    executor_config: dict,
    session_id: str,
) -> dict:
    executor = execution.get("executor")
    if not repair_plan.get("should_attempt"):
        return {
            "attempted": False,
            "success": False,
            "reason": "repair_plan_not_actionable",
            "revised_execution": execution,
            "revised_output": "",
        }
    if not execution or executor in {None, "prompt_only"}:
        return {
            "attempted": False,
            "success": False,
            "reason": "executor_not_runnable",
            "revised_execution": execution,
            "revised_output": "",
        }

    revised = run_executor(
        executor,
        repair_plan["repair_prompt"],
        executor_config or {},
        {"session_id": session_id, "mode": "auto_repair_loop"},
    )
    ok = not revised.get("error") and bool(revised.get("raw_output"))
    return {
        "attempted": True,
        "success": ok,
        "reason": "" if ok else (revised.get("error") or "empty_repair_output"),
        "revised_execution": revised if ok else execution,
        "revised_output": revised.get("raw_output", "") if ok else "",
    }
