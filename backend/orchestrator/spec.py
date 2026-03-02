from __future__ import annotations

from datetime import datetime, timezone


WORKFLOW_STATES = {
    "input_received",
    "clarifying",
    "spec_ready",
    "executing",
    "validating",
    "done",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_session_record(
    session_id: str,
    text: str,
    preferred_executor: str | None,
    context: dict | None,
    task_type: str,
) -> dict:
    ts = now_iso()
    return {
        "session_id": session_id,
        "state": "input_received",
        "text": text,
        "preferred_executor": preferred_executor,
        "context": context or {},
        "task_type": task_type,
        "clarify_form_schema": None,
        "clarify_answers": {},
        "spec_draft": None,
        "spec": None,
        "route": None,
        "generated_prompts": [],
        "execution": None,
        "validation": None,
        "final_output": None,
        "created_at": ts,
        "updated_at": ts,
    }
