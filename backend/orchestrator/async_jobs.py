from __future__ import annotations

from celery.result import AsyncResult

from celery_app import celery
from .async_tasks import execute_workflow_task, validate_workflow_task


def enqueue_execute(session_id: str, executor: str, executor_config: dict | None = None) -> str:
    task = execute_workflow_task.delay(session_id=session_id, executor=executor, executor_config=executor_config or {})
    return task.id


def enqueue_validate(session_id: str, output: str | None = None, auto_revise: bool = False) -> str:
    task = validate_workflow_task.delay(session_id=session_id, output=output, auto_revise=auto_revise)
    return task.id


def get_job(job_id: str) -> dict:
    job = AsyncResult(job_id, app=celery)
    payload = {
        "job_id": job.id,
        "state": job.state,
        "ready": job.ready(),
        "successful": job.successful() if job.ready() else None,
    }
    if job.ready():
        payload["result"] = job.result
    return payload
