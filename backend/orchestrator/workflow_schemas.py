from __future__ import annotations

from typing import Any


def start_response(session: dict) -> dict:
    return {
        "session_id": session.get("session_id"),
        "state": session.get("state"),
        "task_type": session.get("task_type"),
        "clarify_form_schema": session.get("clarify_form_schema"),
        "missing_slots": session.get("missing_slots") or [],
        "missing_slot_hints": session.get("missing_slot_hints") or {},
        "task_spec_shell": session.get("task_spec_shell"),
        "spec_gap": session.get("spec_gap") or {},
        "risk_assessment": session.get("risk_assessment") or {},
        "skill_selection": session.get("skill_selection"),
        "skill_suggestions": session.get("skill_suggestions") or [],
        "project_memory": session.get("project_memory") or {},
        "run_memory": session.get("run_memory") or {},
        "hook_trace": session.get("hook_trace") or [],
        "spec_draft": session.get("spec_draft"),
    }


def clarify_response(session: dict) -> dict:
    return {
        "session_id": session.get("session_id"),
        "state": session.get("state"),
        "task_spec_shell": session.get("task_spec_shell"),
        "spec_gap": session.get("spec_gap") or {},
        "risk_assessment": session.get("risk_assessment") or {},
        "skill_selection": session.get("skill_selection"),
        "skill_suggestions": session.get("skill_suggestions") or [],
        "run_memory": session.get("run_memory") or {},
        "hook_trace": session.get("hook_trace") or [],
        "spec_draft": session.get("spec_draft"),
    }


def confirm_response(session: dict) -> dict:
    return {
        "session_id": session.get("session_id"),
        "state": session.get("state"),
        "route": session.get("route") or {},
        "generated_prompts": session.get("generated_prompts") or [],
        "task_spec_shell": session.get("task_spec_shell"),
        "spec_gap": session.get("spec_gap") or {},
        "risk_assessment": session.get("risk_assessment") or {},
        "skill_selection": session.get("skill_selection"),
        "skill_suggestions": session.get("skill_suggestions") or [],
        "run_memory": session.get("run_memory") or {},
        "hook_trace": session.get("hook_trace") or [],
        "lightweight_spec_validation": session.get("lightweight_spec_validation") or {},
        "plan_graph": session.get("plan_graph"),
        "preflight_validation": session.get("preflight_validation") or {},
        "execution": session.get("execution"),
    }


def execute_response(session: dict) -> dict:
    return {
        "session_id": session.get("session_id"),
        "state": session.get("state"),
        "plan_graph": session.get("plan_graph"),
        "preflight_validation": session.get("preflight_validation") or {},
        "skill_selection": session.get("skill_selection"),
        "skill_suggestions": session.get("skill_suggestions") or [],
        "run_memory": session.get("run_memory") or {},
        "hook_trace": session.get("hook_trace") or [],
        "execution": session.get("execution"),
    }


def validate_response(session: dict) -> dict:
    return {
        "session_id": session.get("session_id"),
        "state": session.get("state"),
        "lightweight_output_validation": session.get("lightweight_output_validation") or {},
        "repair_result": session.get("repair_result") or {},
        "skill_selection": session.get("skill_selection"),
        "skill_suggestions": session.get("skill_suggestions") or [],
        "run_memory": session.get("run_memory") or {},
        "hook_trace": session.get("hook_trace") or [],
        "validation": session.get("validation") or {},
        "final_output": session.get("final_output", ""),
    }


def assert_response_shape(stage: str, payload: dict[str, Any]) -> None:
    required = {
        "start": {"session_id", "state", "task_type", "spec_draft"},
        "clarify": {"session_id", "state", "spec_draft"},
        "confirm": {"session_id", "state", "route", "generated_prompts"},
        "execute": {"session_id", "state", "execution"},
        "validate": {"session_id", "state", "validation", "final_output"},
    }.get(stage, set())

    missing = [k for k in required if k not in payload]
    if missing:
        raise ValueError(f"Workflow response schema violation ({stage}): missing keys {missing}")
