from __future__ import annotations

import os

import pytest


@pytest.mark.integration
def test_mysql_redis_connectivity():
    mysql_url = os.getenv("MYSQL_URL", "")
    redis_url = os.getenv("REDIS_URL", "")
    if not mysql_url or not redis_url:
        pytest.skip("MYSQL_URL or REDIS_URL not set")

    from infrastructure.db import mysql_available, init_mysql_schema
    from infrastructure.redis_client import redis_available

    assert mysql_available() is True
    assert init_mysql_schema() is True
    assert redis_available() is True


@pytest.mark.integration
def test_celery_eager_execute_job_flow():
    redis_url = os.getenv("REDIS_URL", "")
    if not redis_url:
        pytest.skip("REDIS_URL not set")

    try:
        from celery_app import celery
    except Exception:
        pytest.skip("celery is not installed")
    celery.conf.task_always_eager = True
    celery.conf.task_eager_propagates = True

    from orchestrator.async_jobs import enqueue_execute, get_job
    from orchestrator.service import start_workflow, submit_clarifications, confirm_spec

    start = start_workflow("帮我写一封邮件催发票")
    if start.get("state") == "clarifying":
        spec_ready = submit_clarifications(start["session_id"], {
            "clarified_request": "写一封催供应商开票邮件",
            "output_preference": "direct",
            "recipient_type": "vendor",
            "relationship": "existing",
            "purpose": "request_invoice",
            "tone": "professional",
            "language": "zh",
            "word_limit": 180,
            "include_deadline": False,
            "include_bullets": False,
            "background": "订单完成未收票，影响结算",
        })
        spec = spec_ready.get("spec_draft")
    else:
        spec = start.get("spec_draft")

    confirm_spec(start["session_id"], spec)
    job_id = enqueue_execute(start["session_id"], "prompt_only", {})
    status = get_job(job_id)
    assert status["ready"] is True
    assert status["result"]["ok"] is True
