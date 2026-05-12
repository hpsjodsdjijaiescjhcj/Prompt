from __future__ import annotations

from celery_app import celery

from .service import execute_session, validate_session_output


@celery.task(name="workflow.execute")
def execute_workflow_task(session_id: str, executor: str, executor_config: dict | None = None):
    try:
        result = execute_session(session_id=session_id, executor=executor, executor_config=executor_config or {})
        return {"ok": True, "result": result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


@celery.task(name="workflow.validate")
def validate_workflow_task(session_id: str, output: str | None = None, auto_revise: bool = False):
    try:
        result = validate_session_output(session_id=session_id, output=output, auto_revise=auto_revise)
        return {"ok": True, "result": result}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}
