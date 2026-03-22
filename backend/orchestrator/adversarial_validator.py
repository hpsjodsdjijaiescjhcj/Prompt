from __future__ import annotations

import re


def run_adversarial_residual_validation(
    spec: dict,
    output: str,
    phase: str = "post_execution",
    plan_graph: dict | None = None,
) -> dict:
    task_type = spec.get("task_type", "generic")
    plan_outline = _build_plan_outline(spec, plan_graph)
    precondition_issues = _check_preconditions(spec)
    attack_findings = _run_attack_checks(spec, output, phase, plan_graph)
    residual_targets = _collect_residual_targets(plan_outline, precondition_issues, attack_findings)
    pass_check = not precondition_issues and not attack_findings

    return {
        "pass": pass_check,
        "phase": phase,
        "risk_level": _risk_level(precondition_issues, attack_findings),
        "plan_outline": plan_outline,
        "precondition_issues": precondition_issues,
        "attack_findings": attack_findings,
        "residual_targets": residual_targets,
        "repair_prompt": _build_repair_prompt(task_type, spec, precondition_issues, attack_findings),
    }


def _build_plan_outline(spec: dict, plan_graph: dict | None = None) -> list[dict]:
    if plan_graph:
        return [
            {
                "id": node["id"],
                "name": node.get("kind", ""),
                "description": node.get("label", ""),
                "depends_on": node.get("depends_on", []),
            }
            for node in plan_graph.get("nodes", [])
        ]

    task_type = spec.get("task_type", "generic")
    if task_type == "email":
        steps = [
            ("s1", "establish_context", "Explain the context and why the email is being sent now."),
            ("s2", "state_request", "State the exact request/action the recipient should take."),
            ("s3", "commitment_boundary", "Include deadlines, next steps, or bullet items when required."),
            ("s4", "close_loop", "Close politely with a clear response expectation."),
        ]
    elif task_type == "writing":
        steps = [
            ("s1", "frame_goal", "Anchor the piece to the platform, audience, and content goal."),
            ("s2", "deliver_core_points", "Deliver the main selling points or core narrative clearly."),
            ("s3", "fit_style", "Match style modifiers, tone, and format constraints."),
            ("s4", "call_to_action", "End with a usable conclusion or CTA when applicable."),
        ]
    elif task_type == "code":
        steps = [
            ("s1", "understand_change", "State the change goal, files, and constraints."),
            ("s2", "implement_change", "Describe the concrete code or patch strategy."),
            ("s3", "verify_execution", "Explain how tests/lint/rollback safety are covered."),
            ("s4", "report_delta", "Return patch-level or file-level implementation details."),
        ]
    else:
        steps = [
            ("s1", "restate_objective", "Restate the objective in an executable way."),
            ("s2", "cover_required_context", "Use background, audience, and constraints instead of answering generically."),
            ("s3", "produce_usable_result", "Return a directly usable result in the expected format."),
            ("s4", "respect_acceptance", "Ensure the output satisfies acceptance criteria and edge conditions."),
        ]

    return [
        {"id": step_id, "name": name, "description": description}
        for step_id, name, description in steps
    ]


def _check_preconditions(spec: dict) -> list[dict]:
    issues = []
    objective = (spec.get("objective") or "").strip()
    if len(objective) < 4:
        issues.append(_issue("missing_objective", "Task objective is too weak to execute reliably.", "s1"))

    acceptance = spec.get("acceptance_criteria") or []
    if not acceptance:
        issues.append(_issue("missing_acceptance", "Acceptance criteria are missing, so validation has no target.", "s4"))

    task_type = spec.get("task_type", "generic")
    audience = spec.get("audience") or {}
    context = spec.get("context") or {}

    if task_type == "email":
        if not (audience.get("recipient_type") or audience.get("recipient_label")):
            issues.append(_issue("missing_recipient", "Email task is missing a concrete recipient identity or type.", "s1"))
        if not (context.get("background") or "").strip():
            issues.append(_issue("missing_background", "Email task has no background context, which weakens the ask.", "s1"))
    elif task_type == "writing":
        if not (audience.get("target") or "").strip():
            issues.append(_issue("missing_audience", "Writing task is missing a target audience.", "s1"))
        if not (context.get("background") or "").strip():
            issues.append(_issue("missing_material", "Writing task is missing source material or key context.", "s2"))
    elif task_type == "code":
        constraints = spec.get("constraints") or {}
        if not (constraints.get("change_type") or spec.get("change_type")):
            issues.append(_issue("missing_change_type", "Code task is missing a change type such as feature, bugfix, or refactor.", "s1"))
    else:
        if not ((context.get("background") or "").strip() or (spec.get("original_request") or "").strip()):
            issues.append(_issue("missing_context", "Generic task lacks enough context for reliable execution.", "s2"))

    weather = context.get("weather") or {}
    if weather:
        if not weather.get("location"):
            issues.append(_issue("missing_weather_location", "Weather query is missing a location.", "s2"))
        if not weather.get("time_range"):
            issues.append(_issue("missing_weather_time", "Weather query is missing a time range.", "s2"))

    return issues


def _run_attack_checks(spec: dict, output: str, phase: str, plan_graph: dict | None = None) -> list[dict]:
    findings = []
    task_type = spec.get("task_type", "generic")
    constraints = spec.get("constraints") or {}
    output_text = output or ""

    if phase == "preflight":
        if task_type == "email":
            if constraints.get("must_include_deadline") and not _spec_has_deadline_commitment(spec):
                findings.append(
                    _issue(
                        "deadline_unplanned",
                        "Preflight check: the spec requires a deadline, but the plan does not encode a concrete deadline commitment.",
                        _resolve_step_id(plan_graph, "commitment", "s3"),
                    )
                )
            if constraints.get("must_include_bullets") and not _spec_has_bullet_focus(spec):
                findings.append(
                    _issue(
                        "bullet_unplanned",
                        "Preflight check: the spec requires action bullets, but the plan does not state what those bullets should enumerate.",
                        _resolve_step_id(plan_graph, "commitment", "s3"),
                    )
                )
        elif task_type == "writing":
            if not _spec_has_core_message(spec):
                findings.append(
                    _issue(
                        "weak_message_frame",
                        "Preflight check: the writing spec does not yet encode enough core message context to survive style generation.",
                        _resolve_step_id(plan_graph, "context", "s2"),
                    )
                )
        elif task_type == "code":
            if not _spec_has_verification_path(spec):
                findings.append(
                    _issue(
                        "verification_unplanned",
                        "Preflight check: the code plan does not describe how success will be verified.",
                        _resolve_step_id(plan_graph, "validation", "s3"),
                    )
                )
        else:
            if not _spec_has_output_shape(spec):
                findings.append(_issue("weak_output_contract", "Preflight check: the generic task lacks a concrete output shape, making downstream execution unstable.", _resolve_step_id(plan_graph, "output", "s3")))
        return findings

    if not output_text.strip():
        findings.append(_issue("empty_delivery", "No output exists, so the plan cannot survive execution.", "s3"))
        return findings

    if task_type == "email":
        if constraints.get("must_include_deadline") and not _contains_deadline(output_text):
            findings.append(_issue("deadline_break", "Adversarial check: if the recipient delays, the plan has no enforceable deadline.", _resolve_step_id(plan_graph, "commitment", "s3")))
        if constraints.get("must_include_bullets") and not _contains_bullet_list(output_text):
            findings.append(_issue("bullet_break", "Adversarial check: required action items are not explicitly enumerable.", _resolve_step_id(plan_graph, "commitment", "s3")))
        if not _contains_response_request(output_text):
            findings.append(_issue("loop_not_closed", "Adversarial check: the email does not force a concrete reply path.", _resolve_step_id(plan_graph, "closure", "s4")))
    elif task_type == "writing":
        if spec.get("must_include") and not _covers_list(output_text, spec.get("must_include") or []):
            findings.append(_issue("content_drop", "Adversarial check: at least one required content point disappeared in the final text.", "s2"))
        if not _style_modifiers_reflected(spec, output_text):
            findings.append(_issue("style_miss", "Adversarial check: style modifiers are present in spec but weak in the output.", "s3"))
    elif task_type == "code":
        if not _looks_like_code_delta(output_text):
            findings.append(_issue("non_executable_change", "Adversarial check: output does not look like a patch, diff, or explicit code change plan.", "s4"))
        if "test" in " ".join((spec.get("acceptance_criteria") or [])).lower() and "test" not in output_text.lower():
            findings.append(_issue("test_gap", "Adversarial check: the plan requires verification, but no test or validation path is described.", "s3"))
    else:
        if not _covers_acceptance(output_text, spec.get("acceptance_criteria") or []):
            findings.append(_issue("acceptance_gap", "Adversarial check: the response does not visibly cover the acceptance criteria.", "s4"))
        if _looks_overly_generic(output_text):
            findings.append(_issue("generic_answer", "Adversarial check: the response is too generic to survive a hostile edge-case review.", "s2"))

    return findings


def _resolve_step_id(plan_graph: dict | None, kind: str, fallback: str) -> str:
    if not plan_graph:
        return fallback
    for node in plan_graph.get("nodes", []):
        if node.get("kind") == kind:
            return node["id"]
    return fallback


def _collect_residual_targets(plan_outline: list[dict], preconditions: list[dict], attacks: list[dict]) -> list[dict]:
    by_step: dict[str, dict] = {}
    for issue in preconditions + attacks:
        step_id = issue.get("step_id") or "s1"
        if step_id not in by_step:
            step_name = next((row["name"] for row in plan_outline if row["id"] == step_id), step_id)
            by_step[step_id] = {
                "step_id": step_id,
                "step_name": step_name,
                "issue_types": [],
                "messages": [],
            }
        by_step[step_id]["issue_types"].append(issue["type"])
        by_step[step_id]["messages"].append(issue["message"])
    return list(by_step.values())


def _build_repair_prompt(task_type: str, spec: dict, preconditions: list[dict], attacks: list[dict]) -> str:
    issues = preconditions + attacks
    if not issues:
        return ""
    issue_lines = "\n".join(f"- {row['type']}: {row['message']}" for row in issues)
    return (
        "Revise only the weak parts of the current task plan/output.\n"
        f"Task type: {task_type}\n"
        f"Objective: {spec.get('objective', '')}\n"
        "Do not rewrite everything from scratch. Repair the residual logic gaps below:\n"
        f"{issue_lines}\n"
        "Return a corrected final output that preserves the original intent while fixing these failures."
    )


def _risk_level(preconditions: list[dict], attacks: list[dict]) -> str:
    total = len(preconditions) + len(attacks)
    if total >= 4:
        return "high"
    if total >= 2:
        return "medium"
    return "low"


def _issue(issue_type: str, message: str, step_id: str) -> dict:
    return {"type": issue_type, "message": message, "step_id": step_id}


def _contains_deadline(text: str) -> bool:
    patterns = [
        r"deadline",
        r"due",
        r"before\s+\w+",
        r"截至",
        r"截止",
        r"最?晚",
        r"\d{1,2}月\d{1,2}日",
        r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?",
    ]
    return any(re.search(p, text, flags=re.IGNORECASE) for p in patterns)


def _contains_bullet_list(text: str) -> bool:
    for line in text.splitlines():
        s = line.strip()
        if re.match(r"^(?:-|\*|•)\s+", s):
            return True
        if re.match(r"^\d+[\.)]\s+", s):
            return True
    return False


def _contains_response_request(text: str) -> bool:
    markers = ["reply", "respond", "confirm", "let me know", "回复", "确认", "请告知", "请回复"]
    lower = text.lower()
    return any(m in lower for m in markers)


def _covers_list(output: str, items: list[str]) -> bool:
    if not items:
        return True
    lower = output.lower()
    matched = 0
    for item in items:
        if item and item.lower() in lower:
            matched += 1
    return matched >= max(1, len(items) - 1)


def _style_modifiers_reflected(spec: dict, output: str) -> bool:
    modifiers = (((spec.get("context") or {}).get("intent_frame") or {}).get("style_modifiers") or [])
    if not modifiers:
        return True
    text = output.lower()
    for modifier in modifiers:
        token = str(modifier).strip().lower()
        if token and token in text:
            return True
    tone = str(spec.get("tone", "")).lower()
    if tone and tone in text:
        return True
    return False


def _looks_like_code_delta(text: str) -> bool:
    hints = ["diff --git", "+++", "---", "@@", "patch", "changed files", "file:", "```"]
    lower = text.lower()
    return any(h in lower for h in hints)


def _covers_acceptance(output: str, criteria: list[str]) -> bool:
    if not criteria:
        return True
    output_lower = output.lower()
    score = 0
    for criterion in criteria:
        parts = [p for p in re.split(r"[，,。.;:\s]+", criterion.lower()) if len(p) >= 2]
        if any(part in output_lower for part in parts[:3]):
            score += 1
    return score >= max(1, len(criteria) // 2)


def _looks_overly_generic(output: str) -> bool:
    weak_markers = [
        "it depends",
        "根据情况",
        "视情况而定",
        "可以从以下几个方面",
        "as follows",
    ]
    lower = output.lower()
    return len(output.strip()) < 80 or any(marker in lower for marker in weak_markers)


def _spec_has_deadline_commitment(spec: dict) -> bool:
    text_sources = [
        spec.get("objective", ""),
        (spec.get("context") or {}).get("background", ""),
        "\n".join(spec.get("must_include") or []),
        "\n".join((spec.get("acceptance_criteria") or [])),
    ]
    merged = "\n".join(text_sources)
    return _contains_deadline(merged)


def _spec_has_bullet_focus(spec: dict) -> bool:
    must_include = spec.get("must_include") or []
    output_format = spec.get("output_format") or {}
    sections = output_format.get("sections") or []
    return bool(must_include or sections)


def _spec_has_core_message(spec: dict) -> bool:
    context = spec.get("context") or {}
    background = (context.get("background") or "").strip()
    must_include = spec.get("must_include") or []
    return len(background) >= 12 or len(must_include) >= 1


def _spec_has_verification_path(spec: dict) -> bool:
    acceptance = " ".join(spec.get("acceptance_criteria") or []).lower()
    constraints = " ".join((spec.get("constraints") or {}).get("hard_constraints") or []).lower()
    return "test" in acceptance or "lint" in acceptance or "test" in constraints or "lint" in constraints


def _spec_has_output_shape(spec: dict) -> bool:
    output_format = spec.get("output_format") or {}
    output_type = str(output_format.get("type", "")).strip()
    sections = output_format.get("sections") or []
    return bool(output_type or sections)
