from __future__ import annotations

import re

from recommender import recommend_models

from .adversarial_validator import run_adversarial_residual_validation
from .executor import run_executor
from .hooks import build_default_hook_manager
from .inference import apply_inferred_defaults, infer_initial_answers
from .lightweight_validator import validate_output_lightweight, validate_task_spec_lightweight
from .memory import append_run_note, initialize_project_memory, initialize_run_memory, merge_run_memory
from .plan_graph import build_plan_graph, validate_plan_graph
from .repair_loop import attempt_repair_once, build_repair_plan
from .risk_policy import assess_risk
from .router import get_handler, route_task
from .skills import recommend_skills, select_primary_skill
from .spec_gap_detector import detect_spec_gaps
from .store import store
from .task_spec_shell import apply_shell_annotations, build_task_spec_shell
from .workflow_schemas import (
    assert_response_shape,
    clarify_response,
    confirm_response,
    execute_response,
    start_response,
    validate_response,
)

HOOKS = build_default_hook_manager()


class ClarifyValidationError(ValueError):
    """Raised when clarify answers fail schema validation."""


def start_workflow(
    text: str,
    preferred_executor: str | None = None,
    context: dict | None = None,
) -> dict:
    task_type, handler, confidence = route_task(text)
    inferred = infer_initial_answers(task_type, text, context)
    session = store.create(
        text=text,
        preferred_executor=preferred_executor,
        context=context,
        task_type=task_type,
    )
    project_memory = initialize_project_memory(context)
    run_memory = initialize_run_memory(context)
    base_shell = build_task_spec_shell(
        session_id=session["session_id"],
        raw_request=text,
        task_type=task_type,
        state="input_received",
        inferred_answers=inferred,
    )
    skill_selection = select_primary_skill(task_type, text)
    skill_suggestions = recommend_skills(task_type, text, top_n=2)
    hook_ctx = HOOKS.emit(
        "before_clarify",
        {
            "session_id": session["session_id"],
            "task_type": task_type,
            "task_spec_shell": base_shell,
            "project_memory": project_memory,
            "run_memory": run_memory,
            "hook_trace": [],
        },
    )
    run_memory = merge_run_memory(run_memory, hook_ctx.get("run_memory"))
    hook_trace = list(hook_ctx.get("hook_trace") or [])

    if task_type == "other" or not handler:
        spec_gap = detect_spec_gaps(task_type, text, inferred_answers=inferred)
        risk_assessment = assess_risk(base_shell, spec_gap, preferred_executor)
        task_spec_shell = apply_shell_annotations(base_shell, spec_gap, risk_assessment)
        run_memory = append_run_note(run_memory, "Task type routed to 'other'; workflow kept in spec_ready without orchestration.")
        session = store.update(
            session["session_id"],
            state="spec_ready",
            clarify_form_schema=None,
            spec_draft=None,
            inferred_answers=inferred,
            task_spec_shell=task_spec_shell,
            spec_gap=spec_gap,
            risk_assessment=risk_assessment,
            skill_selection=skill_selection,
            skill_suggestions=skill_suggestions,
            project_memory=project_memory,
            run_memory=run_memory,
            hook_trace=hook_trace,
            routing_confidence=confidence,
        )
        payload = start_response(session)
        assert_response_shape("start", payload)
        return payload

    # generic 但语义已经很明确时，直接产出 spec 草案，避免让用户填一整页表单。
    if task_type == "generic" and _looks_specific_request(text) and _generic_can_skip_clarify(text, inferred):
        default_answers = _default_generic_answers(text, inferred)
        spec = handler.build_spec(text, default_answers)
        spec_gap = detect_spec_gaps(task_type, text, inferred_answers=default_answers, spec=spec)
        task_spec_shell = build_task_spec_shell(
            session_id=session["session_id"],
            raw_request=text,
            task_type=task_type,
            state="spec_ready",
            spec=spec,
            inferred_answers=default_answers,
        )
        risk_assessment = assess_risk(task_spec_shell, spec_gap, preferred_executor)
        task_spec_shell = apply_shell_annotations(task_spec_shell, spec_gap, risk_assessment)
        run_memory = append_run_note(run_memory, "Generic request considered specific enough; clarify step skipped.")
        session = store.update(
            session["session_id"],
            state="spec_ready",
            clarify_form_schema=None,
            clarify_answers=default_answers,
            inferred_answers=inferred,
            spec_draft=spec,
            task_spec_shell=task_spec_shell,
            spec_gap=spec_gap,
            risk_assessment=risk_assessment,
            skill_selection=skill_selection,
            skill_suggestions=skill_suggestions,
            project_memory=project_memory,
            run_memory=run_memory,
            hook_trace=hook_trace,
            routing_confidence=confidence,
        )
        payload = start_response(session)
        assert_response_shape("start", payload)
        return payload

    schema = handler.clarify_schema(text)
    schema = _with_common_clarify_fields(schema, task_type)
    schema = apply_inferred_defaults(schema, inferred)
    schema, missing_slots = _build_minimal_clarify_schema(schema, task_type, inferred, text)
    missing_slot_hints = _build_missing_slot_hints(missing_slots, task_type)
    spec_gap = detect_spec_gaps(
        task_type,
        text,
        schema=schema,
        inferred_answers=inferred,
        known_missing_fields=missing_slots,
    )
    risk_assessment = assess_risk(base_shell, spec_gap, preferred_executor)
    task_spec_shell = apply_shell_annotations(base_shell, spec_gap, risk_assessment)
    run_memory = append_run_note(run_memory, "Clarification required before moving to spec_ready.")
    session = store.update(
        session["session_id"],
        state="clarifying",
        clarify_form_schema=schema,
        inferred_answers=inferred,
        missing_slots=missing_slots,
        missing_slot_hints=missing_slot_hints,
        task_spec_shell=task_spec_shell,
        spec_gap=spec_gap,
        risk_assessment=risk_assessment,
        skill_selection=skill_selection,
        skill_suggestions=skill_suggestions,
        project_memory=project_memory,
        run_memory=run_memory,
        hook_trace=hook_trace,
        routing_confidence=confidence,
    )
    payload = start_response(session)
    assert_response_shape("start", payload)
    return payload


def submit_clarifications(session_id: str, answers: dict) -> dict:
    session = _must_session(session_id)
    if session["state"] != "clarifying":
        raise ValueError(f"Invalid state transition: {session['state']} -> spec_ready")

    inferred = session.get("inferred_answers") or {}
    merged_answers = {**inferred, **(answers or {})}
    normalized_answers = _validate_and_normalize_answers(
        session.get("clarify_form_schema"),
        merged_answers,
    )
    handler = _must_handler(session["task_type"])
    spec = handler.build_spec(session["text"], normalized_answers)
    spec_gap = detect_spec_gaps(session["task_type"], session["text"], inferred_answers=normalized_answers, spec=spec)
    task_spec_shell = build_task_spec_shell(
        session_id=session_id,
        raw_request=session["text"],
        task_type=session["task_type"],
        state="spec_ready",
        spec=spec,
        inferred_answers=normalized_answers,
    )
    risk_assessment = assess_risk(task_spec_shell, spec_gap, session.get("preferred_executor"))
    task_spec_shell = apply_shell_annotations(task_spec_shell, spec_gap, risk_assessment)
    skill_selection = select_primary_skill(session["task_type"], session["text"])
    skill_suggestions = recommend_skills(session["task_type"], session["text"], top_n=2)
    run_memory = append_run_note(session.get("run_memory"), "Clarification answers submitted and spec draft generated.")

    session = store.update(
        session_id,
        clarify_answers=normalized_answers,
        spec_draft=spec,
        task_spec_shell=task_spec_shell,
        spec_gap=spec_gap,
        risk_assessment=risk_assessment,
        skill_selection=skill_selection,
        skill_suggestions=skill_suggestions,
        run_memory=run_memory,
        state="spec_ready",
    )
    payload = clarify_response(session)
    assert_response_shape("clarify", payload)
    return payload


def confirm_spec(session_id: str, spec: dict) -> dict:
    session = _must_session(session_id)
    if session["state"] not in {"spec_ready", "clarifying"}:
        raise ValueError(f"Invalid state transition: {session['state']} -> confirm_spec")

    handler = _must_handler(spec.get("task_type") or session["task_type"])

    recommended = ["prompt_only", "local_lmstudio", "openai_compatible"]
    selected = session.get("preferred_executor") or "prompt_only"
    if selected not in recommended:
        selected = "prompt_only"

    route = {
        "recommended_executors": recommended,
        "selected_executor": selected,
        "recommended_models": _recommend_models_for_spec(spec, session.get("text", "")),
    }
    prompts = handler.prompts(spec, route)
    spec_gap = detect_spec_gaps(session["task_type"], session.get("text", ""), spec=spec)
    task_spec_shell = build_task_spec_shell(
        session_id=session_id,
        raw_request=session.get("text", ""),
        task_type=spec.get("task_type") or session["task_type"],
        state="spec_ready",
        spec=spec,
        inferred_answers=session.get("clarify_answers") or session.get("inferred_answers") or {},
    )
    risk_assessment = assess_risk(task_spec_shell, spec_gap, selected)
    task_spec_shell = apply_shell_annotations(task_spec_shell, spec_gap, risk_assessment)
    skill_selection = select_primary_skill(session["task_type"], session.get("text", ""))
    skill_suggestions = recommend_skills(session["task_type"], session.get("text", ""), top_n=2)
    lightweight_spec_validation = validate_task_spec_lightweight(task_spec_shell, spec, spec_gap)
    hook_ctx = HOOKS.emit(
        "after_spec_generated",
        {
            "session_id": session_id,
            "task_type": session["task_type"],
            "task_spec_shell": task_spec_shell,
            "project_memory": session.get("project_memory") or {},
            "run_memory": session.get("run_memory") or {},
            "hook_trace": session.get("hook_trace") or [],
        },
    )
    run_memory = merge_run_memory(session.get("run_memory"), hook_ctx.get("run_memory"))
    run_memory = append_run_note(run_memory, "Spec confirmed and prompts generated.")
    hook_trace = list(hook_ctx.get("hook_trace") or [])
    plan_graph = build_plan_graph(spec)
    if plan_graph:
        preflight_validation = validate_plan_graph(spec, plan_graph)
    else:
        preflight_validation = run_adversarial_residual_validation(spec, "", phase="preflight")
    new_state = "done" if selected == "prompt_only" else "executing"

    session = store.update(
        session_id,
        spec=spec,
        spec_draft=spec,
        task_spec_shell=task_spec_shell,
        spec_gap=spec_gap,
        risk_assessment=risk_assessment,
        skill_selection=skill_selection,
        skill_suggestions=skill_suggestions,
        run_memory=run_memory,
        hook_trace=hook_trace,
        route=route,
        generated_prompts=prompts,
        plan_graph=plan_graph,
        state=new_state,
        lightweight_spec_validation=lightweight_spec_validation,
        preflight_validation=preflight_validation,
        execution=None,
        validation=None,
        logic_validation=None,
        final_output=None,
    )
    payload = confirm_response(session)
    assert_response_shape("confirm", payload)
    return payload


def execute_session(session_id: str, executor: str, executor_config: dict | None) -> dict:
    session = _must_session(session_id)
    if session["task_type"] == "other":
        raise ValueError("Task type 'other' is not supported by workflow execution.")
    if not session.get("spec"):
        raise ValueError("Spec is not confirmed yet.")
    risk_assessment = session.get("risk_assessment") or {}
    if risk_assessment.get("decision") == "needs_clarification":
        raise ValueError("Task still needs clarification before execution.")
    if risk_assessment.get("decision") == "reject":
        raise ValueError("Current risk policy rejects executing this task.")
    plan_graph = session.get("plan_graph") or build_plan_graph(session["spec"])
    preflight_validation = session.get("preflight_validation")
    if not preflight_validation:
        if plan_graph:
            preflight_validation = validate_plan_graph(session["spec"], plan_graph)
        else:
            preflight_validation = run_adversarial_residual_validation(
                session["spec"],
                "",
                phase="preflight",
            )
    if not preflight_validation.get("pass"):
        store.update(session_id, preflight_validation=preflight_validation, plan_graph=plan_graph)
        raise ValueError("Pre-execution logic validation failed. Fix the residual targets before execution.")

    prompt = _select_prompt(session, executor)
    hook_ctx = HOOKS.emit(
        "before_execution",
        {
            "session_id": session_id,
            "executor": executor,
            "task_type": session["task_type"],
            "task_spec_shell": session.get("task_spec_shell") or {},
            "project_memory": session.get("project_memory") or {},
            "run_memory": session.get("run_memory") or {},
            "hook_trace": session.get("hook_trace") or [],
        },
    )
    run_memory = merge_run_memory(session.get("run_memory"), hook_ctx.get("run_memory"))
    run_memory = append_run_note(run_memory, f"Execution started with executor={executor}.")
    hook_trace = list(hook_ctx.get("hook_trace") or [])

    result = run_executor(executor, prompt, executor_config or {}, {"session_id": session_id})
    hook_ctx = HOOKS.emit(
        "after_execution",
        {
            "session_id": session_id,
            "executor": executor,
            "task_type": session["task_type"],
            "execution": result,
            "task_spec_shell": session.get("task_spec_shell") or {},
            "project_memory": session.get("project_memory") or {},
            "run_memory": run_memory,
            "hook_trace": hook_trace,
        },
    )
    run_memory = merge_run_memory(run_memory, hook_ctx.get("run_memory"))
    run_memory = append_run_note(run_memory, "Execution finished.")
    hook_trace = list(hook_ctx.get("hook_trace") or [])

    if result.get("error"):
        state = "done"
    elif executor == "prompt_only":
        state = "done"
    else:
        state = "validating"

    session = store.update(
        session_id,
        state=state,
        plan_graph=plan_graph,
        preflight_validation=preflight_validation,
        execution=result,
        executor_config=executor_config or {},
        run_memory=run_memory,
        hook_trace=hook_trace,
    )
    payload = execute_response(session)
    assert_response_shape("execute", payload)
    return payload


def validate_session_output(
    session_id: str,
    output: str | None = None,
    auto_revise: bool = False,
) -> dict:
    session = _must_session(session_id)
    if session["task_type"] == "other":
        raise ValueError("Task type 'other' is not supported by workflow validation.")

    spec = session.get("spec") or session.get("spec_draft")
    if not spec:
        raise ValueError("No spec found for validation.")

    handler = _must_handler(spec.get("task_type") or session["task_type"])

    execution = session.get("execution") or {}
    current_output = output if output is not None else execution.get("raw_output", "")
    plan_graph = session.get("plan_graph")
    task_spec_shell = session.get("task_spec_shell") or build_task_spec_shell(
        session_id=session_id,
        raw_request=session.get("text", ""),
        task_type=spec.get("task_type") or session["task_type"],
        state=session.get("state", "validating"),
        spec=spec,
        inferred_answers=session.get("clarify_answers") or session.get("inferred_answers") or {},
    )

    report = handler.validate(spec, current_output)
    lightweight_output_validation = validate_output_lightweight(task_spec_shell, spec, current_output)
    logic_validation = run_adversarial_residual_validation(
        spec,
        current_output,
        phase="post_execution",
        plan_graph=plan_graph,
    )
    report = _merge_validation_layers(report, lightweight_output_validation, logic_validation)
    repair_result = {
        "attempted": False,
        "success": False,
        "reason": "not_requested",
        "repair_plan": build_repair_plan(report, lightweight_output_validation, logic_validation),
    }
    final_output = current_output
    run_memory = session.get("run_memory") or {}
    hook_trace = session.get("hook_trace") or []

    if (
        auto_revise
        and not report.get("pass")
    ):
        repair_plan = build_repair_plan(report, lightweight_output_validation, logic_validation)
        repair_attempt = attempt_repair_once(
            execution=execution,
            repair_plan=repair_plan,
            executor_config=session.get("executor_config") or {},
            session_id=session_id,
        )
        repair_result = {
            "attempted": repair_attempt.get("attempted", False),
            "success": repair_attempt.get("success", False),
            "reason": repair_attempt.get("reason", ""),
            "repair_plan": repair_plan,
        }
        if repair_attempt.get("success"):
            final_output = repair_attempt.get("revised_output", "")
            execution = repair_attempt.get("revised_execution", execution)
            report = handler.validate(spec, final_output)
            lightweight_output_validation = validate_output_lightweight(task_spec_shell, spec, final_output)
            logic_validation = run_adversarial_residual_validation(
                spec,
                final_output,
                phase="post_execution",
                plan_graph=plan_graph,
            )
            report = _merge_validation_layers(report, lightweight_output_validation, logic_validation)
            repair_result["repair_plan"] = build_repair_plan(report, lightweight_output_validation, logic_validation)

    hook_ctx = HOOKS.emit(
        "before_final_output",
        {
            "session_id": session_id,
            "task_type": session["task_type"],
            "task_spec_shell": task_spec_shell,
            "project_memory": session.get("project_memory") or {},
            "run_memory": run_memory,
            "hook_trace": hook_trace,
        },
    )
    run_memory = merge_run_memory(run_memory, hook_ctx.get("run_memory"))
    hook_trace = list(hook_ctx.get("hook_trace") or [])

    if not report.get("pass"):
        hook_ctx = HOOKS.emit(
            "on_validation_failed",
            {
                "session_id": session_id,
                "task_type": session["task_type"],
                "validation_issues": report.get("issues") or [],
                "task_spec_shell": task_spec_shell,
                "project_memory": session.get("project_memory") or {},
                "run_memory": run_memory,
                "hook_trace": hook_trace,
            },
        )
        run_memory = merge_run_memory(run_memory, hook_ctx.get("run_memory"))
        run_memory = append_run_note(run_memory, "Validation failed and failure hooks were triggered.")
        hook_trace = list(hook_ctx.get("hook_trace") or [])
    else:
        run_memory = append_run_note(run_memory, "Validation passed.")

    session = store.update(
        session_id,
        state="done",
        execution=execution,
        lightweight_output_validation=lightweight_output_validation,
        repair_result=repair_result,
        validation=report,
        logic_validation=logic_validation,
        run_memory=run_memory,
        hook_trace=hook_trace,
        final_output=handler.postprocess(final_output),
    )
    payload = validate_response(session)
    assert_response_shape("validate", payload)
    return payload


def _merge_validation_layers(report: dict, lightweight_output_validation: dict, logic_validation: dict) -> dict:
    merged = dict(report or {})
    issues = list(merged.get("issues") or [])
    for issue in lightweight_output_validation.get("issues") or []:
        issues.append(
            {
                "type": issue.get("type"),
                "message": issue.get("message"),
                "source": "lightweight_validation",
            }
        )
    for issue in (logic_validation.get("precondition_issues") or []) + (logic_validation.get("attack_findings") or []):
        issues.append(
            {
                "type": issue.get("type"),
                "message": issue.get("message"),
                "source": "logic_validation",
                "step_id": issue.get("step_id"),
            }
        )

    merged["issues"] = issues
    merged["lightweight_validation"] = lightweight_output_validation
    merged["logic_validation"] = logic_validation
    merged["pass"] = bool(merged.get("pass")) and bool(logic_validation.get("pass")) and bool(
        lightweight_output_validation.get("passed")
    )

    repair_prompt = logic_validation.get("repair_prompt", "")
    base_fix_prompt = merged.get("suggested_fix_prompt", "")
    lightweight_repairs = lightweight_output_validation.get("suggested_repairs") or []
    if lightweight_repairs:
        repair_block = "Lightweight validation fixes:\n" + "\n".join(f"- {row}" for row in lightweight_repairs)
        if base_fix_prompt:
            base_fix_prompt = f"{base_fix_prompt}\n\n{repair_block}"
        else:
            base_fix_prompt = repair_block
    if repair_prompt and base_fix_prompt:
        merged["suggested_fix_prompt"] = f"{base_fix_prompt}\n\n{repair_prompt}"
    elif repair_prompt:
        merged["suggested_fix_prompt"] = repair_prompt
    elif base_fix_prompt:
        merged["suggested_fix_prompt"] = base_fix_prompt
    return merged


def get_session(session_id: str) -> dict | None:
    return store.get(session_id)


def _must_session(session_id: str) -> dict:
    session = store.get(session_id)
    if not session:
        raise KeyError(f"Session not found: {session_id}")
    return session


def _must_handler(task_type: str):
    handler = get_handler(task_type)
    if not handler:
        raise ValueError(f"No handler for task_type: {task_type}")
    return handler


def _select_prompt(session: dict, executor: str) -> str:
    prompts = session.get("generated_prompts") or []
    for row in prompts:
        if row.get("executor") == executor:
            return row.get("prompt", "")
    if prompts:
        return prompts[0].get("prompt", "")
    return ""


def _validate_and_normalize_answers(schema: dict | None, answers: dict | None) -> dict:
    if schema is None:
        return answers or {}
    if answers is None:
        answers = {}
    if not isinstance(answers, dict):
        raise ClarifyValidationError("answers must be a JSON object.")

    fields = schema.get("fields") or []
    normalized: dict = {}
    errors: list[str] = []

    for field in fields:
        key = field.get("key")
        field_type = field.get("type")
        default = field.get("default")
        options = [opt.get("value") for opt in (field.get("options") or [])]

        if not key:
            continue
        show_when = field.get("show_when")
        if show_when and not _field_condition_match(show_when, answers, normalized, fields):
            continue

        if key in answers:
            raw_value = answers.get(key)
        elif default is not None:
            raw_value = default
        else:
            raw_value = None

        required = bool(field.get("required", False)) or _field_condition_match(
            field.get("required_when"), answers, normalized, fields
        )
        if required and _is_empty(raw_value, field_type):
            errors.append(f"{key}: required field is missing.")
            continue

        if _is_empty(raw_value, field_type):
            # Optional empty field.
            if field_type == "multi_choice":
                normalized[key] = []
            continue

        ok, casted_or_err = _cast_value(raw_value, field_type, options, field)
        if not ok:
            errors.append(f"{key}: {casted_or_err}")
            continue

        normalized[key] = casted_or_err

    if errors:
        raise ClarifyValidationError("Clarify validation failed: " + "; ".join(errors))

    return normalized


def _is_empty(value, field_type: str | None) -> bool:
    if value is None:
        return True
    if field_type in {"short_text", "multiline_text", "single_choice"}:
        return str(value).strip() == ""
    if field_type == "multi_choice":
        return not isinstance(value, list) or len(value) == 0
    return False


def _cast_value(value, field_type: str | None, options: list, field: dict):
    if field_type in {"short_text", "multiline_text"}:
        if isinstance(value, str):
            return True, value.strip()
        return False, "must be a string."

    if field_type == "single_choice":
        if not isinstance(value, str):
            return False, "must be a string option."
        if options and value not in options:
            return False, f"must be one of: {options}."
        return True, value

    if field_type == "multi_choice":
        if not isinstance(value, list):
            return False, "must be an array."
        for item in value:
            if not isinstance(item, str):
                return False, "all options in array must be strings."
            if options and item not in options:
                return False, f"contains invalid option '{item}', valid: {options}."
        return True, value

    if field_type == "number":
        try:
            num = float(value)
        except (TypeError, ValueError):
            return False, "must be a number."

        min_v = field.get("min")
        max_v = field.get("max")
        if min_v is not None and num < float(min_v):
            return False, f"must be >= {min_v}."
        if max_v is not None and num > float(max_v):
            return False, f"must be <= {max_v}."

        if num.is_integer():
            return True, int(num)
        return True, num

    if field_type == "boolean":
        if isinstance(value, bool):
            return True, value
        if isinstance(value, (int, float)) and value in (0, 1):
            return True, bool(value)
        if isinstance(value, str):
            s = value.strip().lower()
            if s in {"true", "1", "yes", "y"}:
                return True, True
            if s in {"false", "0", "no", "n"}:
                return True, False
        return False, "must be a boolean."

    # Unknown type: keep as-is for forward compatibility.
    return True, value


def _field_condition_match(condition, raw_answers: dict, normalized: dict, fields: list[dict]) -> bool:
    if not condition:
        return False
    if not isinstance(condition, dict):
        return False
    for dep_key, expected in condition.items():
        actual = _lookup_value(dep_key, raw_answers, normalized, fields)
        if actual != expected:
            return False
    return True


def _lookup_value(dep_key: str, raw_answers: dict, normalized: dict, fields: list[dict]):
    if dep_key in normalized:
        return normalized[dep_key]
    if dep_key in raw_answers:
        return raw_answers.get(dep_key)
    for field in fields:
        if field.get("key") == dep_key and field.get("default") is not None:
            return field.get("default")
    return None


def _with_common_clarify_fields(schema: dict, task_type: str) -> dict:
    """Inject a universal clarify layer before task-specific fields."""
    fields = list(schema.get("fields") or [])
    common_fields = [
        {
            "key": "clarified_request",
            "label": "你最终想交付的结果（必填）",
            "type": "multiline_text",
            "required": True,
            "placeholder": "用 1-3 句话写清楚最终要产出什么（例如：一封可直接发送的催发票邮件）。",
            "help_text": "先明确“做什么”，避免后续执行跑偏。",
        },
        {
            "key": "motivation",
            "label": "做这件事的前因/目的（可选）",
            "type": "multiline_text",
            "required": False,
            "placeholder": "例如：月底对账要完成，发票未到导致财务无法入账。",
            "help_text": "说明“为什么现在做”，有助于系统判断优先级和语气。",
        },
        {
            "key": "primary_target",
            "label": "主要作用对象（可选）",
            "type": "short_text",
            "required": False,
            "placeholder": "例如：供应商A、特斯拉商业模式、纽约天气",
            "help_text": "说明“对谁/对什么做”，避免内容太空泛。",
        },
        {
            "key": "stakeholders",
            "label": "还涉及哪些对象（可选）",
            "type": "short_text",
            "required": False,
            "placeholder": "例如：财务、法务、老板、客户",
            "help_text": "如果有次要相关方，写出来便于平衡表达。",
        },
        {
            "key": "style_modifiers",
            "label": "风格修饰词（可选）",
            "type": "multiline_text",
            "required": False,
            "placeholder": "一行一个，例如：新颖\n简洁\n可信",
            "help_text": "系统会自动抽取你原话中的形容词，你也可以手动补充。",
        },
        {
            "key": "success_criteria",
            "label": "你怎么判断结果“够好”（可选）",
            "type": "multiline_text",
            "required": False,
            "placeholder": "一行一条，例如：\n结论要有依据\n语气不能太强硬\n控制在200字",
            "help_text": "这是验收标准，不填也可以。",
        },
        {
            "key": "hard_constraints",
            "label": "硬性约束（可选）",
            "type": "multiline_text",
            "required": False,
            "placeholder": "一行一条，例如：\n不能提竞品名\n必须用中文\n不能编造数据",
            "help_text": "任何不能违反的限制都写这里。",
        },
        {
            "key": "output_preference",
            "label": "输出方式偏好",
            "type": "single_choice",
            "required": True,
            "default": "direct",
            "options": [
                {"value": "direct", "label": "直接给最终结果"},
                {"value": "outline_then_final", "label": "先大纲再最终结果"},
                {"value": "options_then_pick", "label": "先给多个方案再细化"},
            ],
            "help_text": "决定执行器生成内容的组织方式。",
        },
    ]

    return {
        **schema,
        "description": (
            f"{schema.get('description', '')}\n"
            "先补齐“前因-对象-交付-验收”四要素，再填写任务专用问题。"
        ),
        "fields": common_fields + fields,
    }


def _looks_specific_request(text: str) -> bool:
    t = (text or "").strip()
    if len(t) < 4:
        return False

    specific_patterns = [
        r"解释.+(意思|含义)",
        r"什么是.+",
        r".+是什么意思",
        r"请说明.+",
        r"define\s+.+",
        r"explain\s+.+",
        r"what\s+is\s+.+",
    ]
    if any(re.search(p, t, flags=re.IGNORECASE) for p in specific_patterns):
        return True

    # 含明确宾语且非泛泛请求，通常可直接进入 spec_ready。
    has_explicit_object = len(t) >= 8 and (" " in t or any("\u4e00" <= c <= "\u9fff" for c in t))
    vague_patterns = [r"帮我想想", r"给点建议", r"随便写", r"不知道怎么做"]
    is_vague = any(re.search(p, t) for p in vague_patterns)
    return has_explicit_object and not is_vague


def _default_generic_answers(text: str, inferred: dict | None = None) -> dict:
    defaults = {
        "clarified_request": text.strip(),
        "motivation": "",
        "primary_target": "",
        "stakeholders": "",
        "style_modifiers": "",
        "success_criteria": "",
        "hard_constraints": "",
        "output_preference": "direct",
        "task_domain": "analysis",
        "target_audience": "",
        "expected_output_type": "structured",
        "background": "用户未提供额外背景信息。",
    }
    inferred = inferred or {}
    defaults.update({k: v for k, v in inferred.items() if v not in (None, "")})
    return defaults


def _build_minimal_clarify_schema(
    schema: dict,
    task_type: str,
    inferred: dict,
    text: str,
) -> tuple[dict, list[str]]:
    """Reduce clarify schema to only currently-missing key questions."""
    fields = list(schema.get("fields") or [])
    key_to_field = {f.get("key"): f for f in fields if f.get("key")}

    required_missing = []
    for field in fields:
        key = field.get("key")
        if not key:
            continue
        if not _field_active(field, inferred):
            continue
        required_now = bool(field.get("required")) or _field_condition_match(
            field.get("required_when"), inferred, inferred, fields
        )
        if not required_now:
            continue
        val = inferred.get(key, field.get("default"))
        if _is_empty(val, field.get("type")):
            required_missing.append(key)

    target_missing = []
    if task_type == "generic":
        weather_like = _looks_like_weather_like_text(text)
        if weather_like:
            for k in ("location", "time_range"):
                if _is_empty(inferred.get(k), (key_to_field.get(k) or {}).get("type")):
                    target_missing.append(k)
        else:
            if _is_empty(inferred.get("primary_target"), "short_text"):
                target_missing.append("primary_target")

    prioritized = []
    for k in required_missing + target_missing:
        if k not in prioritized and k in key_to_field:
            prioritized.append(k)

    if not prioritized:
        # 没有缺失关键槽位时，保留原 schema（避免回归）。
        return schema, []

    selected = []
    added = set()

    # 始终包含目标字段，便于用户快速确认。
    for key in ("clarified_request",):
        if key in key_to_field and key not in added:
            selected.append(key_to_field[key])
            added.add(key)

    for key in prioritized[:3]:
        if key in key_to_field and key not in added:
            f = dict(key_to_field[key])
            if key in target_missing:
                f["required"] = True
            selected.append(f)
            added.add(key)

    minimal = {
        **schema,
        "description": "只补齐当前缺失的关键信息（最少问题），即可进入下一步。",
        "fields": selected,
    }
    return minimal, prioritized


def _build_missing_slot_hints(missing_slots: list[str], task_type: str) -> dict:
    common = {
        "clarified_request": "明确最终交付物，避免输出方向跑偏。",
        "primary_target": "明确作用对象，避免结果过于泛化。",
        "background": "补充上下文，避免事实缺失导致内容空泛。",
        "audience": "明确受众，便于控制表达深度和语气。",
        "location": "地点是查询环境信息（如天气）的关键参数。",
        "time_range": "时间范围会直接影响结果内容与有效性。",
    }
    task_specific = {
        "email": {
            "background": "邮件场景需要背景，才能写出可执行且有说服力的正文。",
        },
        "writing": {
            "audience": "写作任务必须有受众，才能确定语气、角度和信息密度。",
        },
        "generic": {
            "primary_target": "通用任务先明确对象，再决定后续分析或执行路径。",
        },
    }.get(task_type, {})

    hints = {}
    for slot in missing_slots or []:
        hints[slot] = task_specific.get(slot) or common.get(slot) or "这是推进下一步所需的关键参数。"
    return hints


def _field_active(field: dict, answers: dict) -> bool:
    cond = field.get("show_when")
    if not cond:
        return True
    if not isinstance(cond, dict):
        return True
    for dep_key, expected in cond.items():
        actual = answers.get(dep_key)
        if actual != expected:
            return False
    return True


def _looks_like_weather_like_text(text: str) -> bool:
    t = (text or "").lower()
    return any(w in t for w in ("天气", "forecast", "weather", "temperature", "降雨", "气温"))


def _generic_can_skip_clarify(text: str, inferred: dict) -> bool:
    """Only skip clarify when inferred slots are reliable enough."""
    t = (text or "").lower()
    weather_like = any(w in t for w in ("天气", "forecast", "weather", "temperature"))
    if weather_like:
        location = (inferred or {}).get("location", "")
        time_range = (inferred or {}).get("time_range", "")
        return bool(str(location).strip()) and bool(str(time_range).strip())

    # 通用任务至少要有较可信的目标描述，才可直接跳过澄清。
    target = (inferred or {}).get("primary_target", "")
    objective = (inferred or {}).get("clarified_request", "")
    return bool(str(target).strip()) and len(str(objective).strip()) >= 8


def _recommend_models_for_spec(spec: dict, original_text: str) -> list[dict]:
    task_type = spec.get("task_type")
    map_type = {
        "email": "writing",
        "writing": "writing",
        "code": "coding",
        "generic": "reasoning",
    }.get(task_type, "writing")

    classification = {
        "task_types": [{"type": map_type, "confidence": 0.8}],
        "complexity": "medium",
        "intent": spec.get("objective") or original_text,
        "key_entities": [],
        "source": "workflow",
    }
    recs = recommend_models(classification, top_n=3)
    return [
        {
            "name": r.get("name"),
            "provider": r.get("provider"),
            "reason": r.get("reason"),
            "match_pct": r.get("match_pct"),
        }
        for r in recs
    ]
