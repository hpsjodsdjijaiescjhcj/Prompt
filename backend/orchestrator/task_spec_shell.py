from __future__ import annotations


def build_task_spec_shell(
    session_id: str,
    raw_request: str,
    task_type: str,
    state: str,
    spec: dict | None = None,
    inferred_answers: dict | None = None,
) -> dict:
    inferred_answers = inferred_answers or {}
    spec = spec or {}
    context = spec.get("context") or {}
    constraints = spec.get("constraints") or {}
    audience = spec.get("audience") or {}
    output_format = spec.get("output_format") or {}
    weather = context.get("weather") or {}

    normalized_goal = (
        spec.get("objective")
        or inferred_answers.get("clarified_request")
        or raw_request
    )

    inputs = {
        "primary_target": _first_nonempty(
            inferred_answers.get("primary_target"),
            ((context.get("intent_frame") or {}).get("primary_target")),
            audience.get("recipient_type"),
            audience.get("target"),
            weather.get("location"),
        ),
        "audience": audience,
        "background": context.get("background", ""),
        "weather": weather,
        "source_fields": {
            "clarified_request": inferred_answers.get("clarified_request", ""),
            "motivation": inferred_answers.get("motivation", ""),
            "stakeholders": inferred_answers.get("stakeholders", ""),
            "style_modifiers": inferred_answers.get("style_modifiers", ""),
        },
    }

    shell = {
        "id": session_id,
        "raw_request": raw_request,
        "normalized_goal": normalized_goal,
        "task_type": task_type,
        "inputs": inputs,
        "constraints": _normalize_constraints(constraints, inferred_answers),
        "missing_fields": [],
        "assumptions": _derive_assumptions(spec, inferred_answers),
        "success_criteria": list(spec.get("acceptance_criteria") or []),
        "expected_artifacts": _expected_artifacts(task_type, spec),
        "tool_plan": _tool_plan(task_type, state, output_format),
        "risk_level": "low",
        "requires_confirmation": False,
        "validation_checks": _validation_checks(task_type, spec),
        "status": state,
    }
    return shell


def apply_shell_annotations(
    shell: dict,
    gap_analysis: dict | None = None,
    risk_assessment: dict | None = None,
) -> dict:
    result = dict(shell or {})
    gap_analysis = gap_analysis or {}
    risk_assessment = risk_assessment or {}
    result["missing_fields"] = list(gap_analysis.get("missing_fields") or [])
    result["risk_level"] = risk_assessment.get("risk_level", result.get("risk_level", "low"))
    result["requires_confirmation"] = bool(
        risk_assessment.get("requires_confirmation", result.get("requires_confirmation", False))
    )
    return result


def _normalize_constraints(constraints: dict, inferred_answers: dict) -> dict:
    result = dict(constraints or {})
    for key in ("hard_constraints", "output_preference", "word_limit", "must_include_deadline", "must_include_bullets"):
        value = inferred_answers.get(key)
        if value not in (None, "", []):
            result.setdefault(key, value)
    return result


def _derive_assumptions(spec: dict, inferred_answers: dict) -> list[str]:
    assumptions = []
    weather = (spec.get("context") or {}).get("weather") or {}
    if weather and not weather.get("unit"):
        assumptions.append("Weather output can default to celsius when the unit is not specified.")
    if inferred_answers.get("language") and not spec.get("language"):
        assumptions.append(f"Use {inferred_answers.get('language')} unless the user overrides it later.")
    if not (spec.get("context") or {}).get("background"):
        assumptions.append("Background context is limited, so later validation should be conservative.")
    return assumptions


def _expected_artifacts(task_type: str, spec: dict) -> list[str]:
    output_format = spec.get("output_format") or {}
    if task_type == "email":
        return ["email_draft", "model_adapted_prompt"]
    if task_type == "writing":
        return ["content_draft", "model_adapted_prompt"]
    if task_type == "code":
        return ["patch_or_change_plan", "model_adapted_prompt"]
    if task_type == "generic":
        artifact = output_format.get("type") or "structured_answer"
        return [artifact, "model_adapted_prompt"]
    return ["model_adapted_prompt"]


def _tool_plan(task_type: str, state: str, output_format: dict) -> list[str]:
    plan = ["clarify", "align"]
    if state in {"spec_ready", "executing", "validating", "done"}:
        plan.append("prompt_generation")
    if task_type == "generic" and (output_format.get("type") or "") == "structured":
        plan.append("structured_delivery")
    plan.append("validate")
    return plan


def _validation_checks(task_type: str, spec: dict) -> list[str]:
    checks = ["schema_validation", "constraint_validation", "goal_validation"]
    constraints = spec.get("constraints") or {}
    if task_type == "email":
        if constraints.get("must_include_deadline"):
            checks.append("deadline_check")
        if constraints.get("must_include_bullets"):
            checks.append("bullet_check")
    if task_type == "generic" and ((spec.get("context") or {}).get("weather") or {}):
        checks.append("weather_parameter_check")
    return checks


def _first_nonempty(*values):
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
        if value not in (None, "", [], {}):
            return value
    return ""
