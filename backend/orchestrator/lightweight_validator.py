from __future__ import annotations

import re


def validate_task_spec_lightweight(task_shell: dict, spec: dict, gap_analysis: dict | None = None) -> dict:
    gap_analysis = gap_analysis or {}
    schema_issues = []
    constraint_issues = []
    goal_issues = []

    if not (task_shell.get("normalized_goal") or "").strip():
        schema_issues.append(_issue("missing_goal", "Normalized goal is empty."))
    if not (task_shell.get("success_criteria") or []):
        schema_issues.append(_issue("missing_success_criteria", "Success criteria are missing."))

    if gap_analysis.get("missing_fields"):
        constraint_issues.append(
            _issue(
                "missing_fields",
                f"Spec still has missing fields: {', '.join(gap_analysis.get('missing_fields') or [])}.",
            )
        )

    task_type = spec.get("task_type", "generic")
    constraints = spec.get("constraints") or {}
    context = spec.get("context") or {}
    if task_type == "email" and constraints.get("must_include_deadline") and not _spec_has_concrete_deadline(spec):
        constraint_issues.append(_issue("missing_deadline_plan", "Email spec requires a deadline but none is defined in the spec context."))
    if task_type == "generic":
        weather = context.get("weather") or {}
        if weather and (not weather.get("location") or not weather.get("time_range")):
            constraint_issues.append(_issue("weather_parameters_incomplete", "Weather task requires both location and time range."))
        if not ((spec.get("output_format") or {}).get("type") or (spec.get("output_format") or {}).get("sections")):
            constraint_issues.append(_issue("missing_output_contract", "Generic task is missing an explicit output contract."))

    objective = (spec.get("objective") or "").strip()
    if len(objective) < 8:
        goal_issues.append(_issue("weak_objective", "Objective is too short to reliably guide execution."))

    issues = schema_issues + constraint_issues + goal_issues
    return {
        "passed": not issues,
        "issues": issues,
        "suggested_repairs": _suggest_repairs(issues),
        "checks": {
            "schema_validation": {"passed": not schema_issues, "issues": schema_issues},
            "constraint_validation": {"passed": not constraint_issues, "issues": constraint_issues},
            "goal_validation": {"passed": not goal_issues, "issues": goal_issues},
        },
    }


def validate_output_lightweight(task_shell: dict, spec: dict, output: str) -> dict:
    schema_issues = []
    constraint_issues = []
    goal_issues = []

    if not (output or "").strip():
        schema_issues.append(_issue("empty_output", "Executor returned no content."))

    must_include = spec.get("must_include") or []
    must_avoid = spec.get("must_avoid") or []
    constraints = spec.get("constraints") or {}
    output_lower = (output or "").lower()

    for item in must_include:
        token = str(item).strip().lower()
        if token and token not in output_lower:
            constraint_issues.append(_issue("must_include_missing", f"Required item missing from output: {item}"))

    for item in must_avoid:
        token = str(item).strip().lower()
        if token and token in output_lower:
            constraint_issues.append(_issue("must_avoid_violation", f"Forbidden item appears in output: {item}"))

    if constraints.get("word_limit"):
        word_limit = int(constraints.get("word_limit") or 0)
        token_count = len(re.findall(r"[A-Za-z0-9_]+|[\u4e00-\u9fff]", output or ""))
        if token_count > word_limit:
            constraint_issues.append(_issue("word_limit_exceeded", f"Output length {token_count} exceeds limit {word_limit}."))

    goal_keywords = _goal_keywords(task_shell.get("normalized_goal") or "")
    if goal_keywords and not any(keyword in output_lower for keyword in goal_keywords):
        goal_issues.append(_issue("weak_goal_coverage", "Output has weak overlap with the normalized goal."))

    issues = schema_issues + constraint_issues + goal_issues
    return {
        "passed": not issues,
        "issues": issues,
        "suggested_repairs": _suggest_repairs(issues),
        "checks": {
            "schema_validation": {"passed": not schema_issues, "issues": schema_issues},
            "constraint_validation": {"passed": not constraint_issues, "issues": constraint_issues},
            "goal_validation": {"passed": not goal_issues, "issues": goal_issues},
        },
    }


def _suggest_repairs(issues: list[dict]) -> list[str]:
    suggestions = []
    for issue in issues:
        if issue["type"] == "missing_fields":
            suggestions.append("补齐缺失字段后再继续执行。")
        elif issue["type"] == "missing_output_contract":
            suggestions.append("明确输出形式，例如 structured / checklist / comparison。")
        elif issue["type"] == "weak_goal_coverage":
            suggestions.append("让输出更直接回应规范化目标中的核心对象和动作。")
        elif issue["type"] == "must_include_missing":
            suggestions.append("把所有 must_include 条目显式写入输出。")
    return suggestions


def _goal_keywords(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-z]{3,}|[\u4e00-\u9fff]{2,}", text.lower())
    stop = {"help", "write", "draft", "生成", "帮我", "给我", "please", "分析", "介绍"}
    deduped = []
    for token in raw:
        if token in stop:
            continue
        if token not in deduped:
            deduped.append(token)
    return deduped[:6]


def _issue(issue_type: str, message: str) -> dict:
    return {"type": issue_type, "message": message}


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
