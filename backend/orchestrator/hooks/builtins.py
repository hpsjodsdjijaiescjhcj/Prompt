from __future__ import annotations

from .manager import HookManager


def hook_mark_before_clarify(ctx: dict) -> dict:
    run_memory = dict(ctx.get("run_memory") or {})
    events = list(run_memory.get("events") or [])
    events.append("before_clarify")
    run_memory["events"] = events
    ctx["run_memory"] = run_memory
    return ctx


def hook_capture_spec_snapshot(ctx: dict) -> dict:
    run_memory = dict(ctx.get("run_memory") or {})
    snapshots = list(run_memory.get("spec_snapshots") or [])
    task_spec_shell = ctx.get("task_spec_shell") or {}
    snapshots.append(
        {
            "status": task_spec_shell.get("status"),
            "goal": task_spec_shell.get("normalized_goal"),
            "missing_fields": list(task_spec_shell.get("missing_fields") or []),
        }
    )
    run_memory["spec_snapshots"] = snapshots[-5:]
    ctx["run_memory"] = run_memory
    return ctx


def hook_record_validation_failure(ctx: dict) -> dict:
    run_memory = dict(ctx.get("run_memory") or {})
    failures = list(run_memory.get("validation_failures") or [])
    issues = ctx.get("validation_issues") or []
    failures.append(
        {
            "count": len(issues),
            "types": [i.get("type") for i in issues[:5]],
        }
    )
    run_memory["validation_failures"] = failures[-10:]
    ctx["run_memory"] = run_memory
    return ctx


def hook_mark_before_execution(ctx: dict) -> dict:
    run_memory = dict(ctx.get("run_memory") or {})
    events = list(run_memory.get("events") or [])
    events.append("before_execution")
    run_memory["events"] = events
    ctx["run_memory"] = run_memory
    return ctx


def hook_mark_after_execution(ctx: dict) -> dict:
    run_memory = dict(ctx.get("run_memory") or {})
    events = list(run_memory.get("events") or [])
    events.append("after_execution")
    run_memory["events"] = events
    ctx["run_memory"] = run_memory
    return ctx


def hook_mark_before_final_output(ctx: dict) -> dict:
    run_memory = dict(ctx.get("run_memory") or {})
    events = list(run_memory.get("events") or [])
    events.append("before_final_output")
    run_memory["events"] = events
    ctx["run_memory"] = run_memory
    return ctx


def build_default_hook_manager() -> HookManager:
    manager = HookManager()
    manager.register("before_clarify", hook_mark_before_clarify)
    manager.register("after_spec_generated", hook_capture_spec_snapshot)
    manager.register("before_execution", hook_mark_before_execution)
    manager.register("after_execution", hook_mark_after_execution)
    manager.register("before_final_output", hook_mark_before_final_output)
    manager.register("on_validation_failed", hook_record_validation_failure)
    return manager
