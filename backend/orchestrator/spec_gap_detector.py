from __future__ import annotations

import re


def detect_spec_gaps(
    task_type: str,
    raw_request: str,
    schema: dict | None = None,
    inferred_answers: dict | None = None,
    spec: dict | None = None,
    known_missing_fields: list[str] | None = None,
) -> dict:
    inferred_answers = inferred_answers or {}
    spec = spec or {}
    missing_fields = list(known_missing_fields or [])
    field_map = {field.get("key"): field for field in (schema or {}).get("fields", []) if field.get("key")}

    if spec:
        missing_fields = _detect_missing_from_spec(task_type, spec)
    elif schema:
        for key, field in field_map.items():
            required = bool(field.get("required"))
            value = inferred_answers.get(key, field.get("default"))
            if required and _is_empty(value):
                if key not in missing_fields:
                    missing_fields.append(key)

    defaultable_fields = _detect_defaultable_fields(task_type, inferred_answers, spec)
    risks = _derive_gap_risks(task_type, missing_fields, raw_request, spec)
    clarification_questions = _clarification_questions(missing_fields, field_map)
    constraints = _collect_constraints(spec, inferred_answers)

    return {
        "missing_fields": missing_fields,
        "defaultable_fields": defaultable_fields,
        "risks": risks,
        "constraints": constraints,
        "need_user_input": bool(missing_fields),
        "clarification_questions": clarification_questions,
    }


def _detect_missing_from_spec(task_type: str, spec: dict) -> list[str]:
    context = spec.get("context") or {}
    audience = spec.get("audience") or {}
    constraints = spec.get("constraints") or {}
    missing = []

    if not (spec.get("objective") or "").strip():
        missing.append("clarified_request")
    if not (spec.get("acceptance_criteria") or []):
        missing.append("success_criteria")

    if task_type == "email":
        if not (audience.get("recipient_type") or audience.get("recipient_label")):
            missing.append("recipient_type")
        if not (context.get("background") or "").strip():
            missing.append("background")
        if constraints.get("must_include_deadline") and not _spec_has_concrete_deadline(spec):
            missing.append("deadline_text")
    elif task_type == "writing":
        if not (audience.get("target") or "").strip():
            missing.append("audience")
        if not (context.get("background") or "").strip():
            missing.append("background")
    elif task_type == "generic":
        weather = context.get("weather") or {}
        if weather:
            if not weather.get("location"):
                missing.append("location")
            if not weather.get("time_range"):
                missing.append("time_range")
        else:
            if not ((context.get("intent_frame") or {}).get("primary_target") or (spec.get("original_request") or "").strip()):
                missing.append("primary_target")
        if not ((spec.get("output_format") or {}).get("type") or (spec.get("output_format") or {}).get("sections")):
            missing.append("expected_output_type")
    elif task_type == "code":
        if not (spec.get("change_type") or (constraints.get("change_type"))):
            missing.append("change_type")

    return missing


def _detect_defaultable_fields(task_type: str, inferred_answers: dict, spec: dict) -> list[str]:
    defaults = []
    if inferred_answers.get("language"):
        defaults.append("language")
    if inferred_answers.get("tone"):
        defaults.append("tone")
    if task_type == "generic":
        weather = (spec.get("context") or {}).get("weather") or {}
        if weather.get("unit"):
            defaults.append("unit")
    if inferred_answers.get("output_preference"):
        defaults.append("output_preference")
    return defaults


def _derive_gap_risks(task_type: str, missing_fields: list[str], raw_request: str, spec: dict) -> list[dict]:
    risks = []
    if missing_fields:
        risks.append(
            {
                "type": "missing_critical_fields",
                "message": f"Missing fields can make downstream execution unstable: {', '.join(missing_fields)}.",
            }
        )
    if task_type == "email" and "发送" in raw_request:
        risks.append(
            {
                "type": "external_communication",
                "message": "Email tasks can affect external communication quality and usually deserve explicit confirmation.",
            }
        )
    if task_type == "generic" and ((spec.get("context") or {}).get("weather") or {}):
        risks.append(
            {
                "type": "parameter_sensitive",
                "message": "Weather-style tasks are parameter sensitive; location and time range must be grounded before execution.",
            }
        )
    return risks


def _clarification_questions(missing_fields: list[str], field_map: dict[str, dict]) -> list[dict]:
    rows = []
    for key in missing_fields:
        field = field_map.get(key) or {}
        rows.append(
            {
                "field": key,
                "label": field.get("label") or key,
                "question": field.get("help_text") or field.get("placeholder") or f"Please provide {key}.",
            }
        )
    return rows


def _collect_constraints(spec: dict, inferred_answers: dict) -> list[str]:
    constraints = list((spec.get("constraints") or {}).get("hard_constraints") or [])
    raw_constraints = inferred_answers.get("hard_constraints")
    if isinstance(raw_constraints, str) and raw_constraints.strip():
        constraints.extend([line.strip() for line in raw_constraints.splitlines() if line.strip()])
    deduped = []
    for item in constraints:
        if item not in deduped:
            deduped.append(item)
    return deduped


def _is_empty(value) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        return not value.strip()
    if isinstance(value, list):
        return len(value) == 0
    return False


def _spec_has_concrete_deadline(spec: dict) -> bool:
    context = spec.get("context") or {}
    candidates = [
        context.get("deadline_text", ""),
        spec.get("objective", ""),
        context.get("background", ""),
        "\n".join(spec.get("must_include") or []),
    ]
    return any(_contains_deadline_marker(text) for text in candidates if text)


def _contains_deadline_marker(text: str) -> bool:
    patterns = [
        r"\d{1,2}月\d{1,2}日",
        r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?",
        r"\b(?:by|before)\s+(?:\d{1,2}(?:st|nd|rd|th)?|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?|today|tomorrow|eod|monday|tuesday|wednesday|thursday|friday|saturday|sunday|next\s+\w+)\b",
        r"\bdeadline[:：]?\s*(?:\d|today|tomorrow|eod|next)\b",
        r"截至",
        r"截止",
        r"最?晚",
    ]
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)
