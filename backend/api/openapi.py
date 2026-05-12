from __future__ import annotations

OPENAPI_SPEC = {
    "openapi": "3.0.3",
    "info": {
        "title": "TaskForge API",
        "version": "1.0.0",
        "description": "Task orchestration workflow API",
    },
    "paths": {
        "/api/health": {"get": {"summary": "Health check"}},
        "/api/health/liveness": {"get": {"summary": "Liveness probe"}},
        "/api/health/readiness": {"get": {"summary": "Readiness probe"}},
        "/metrics": {"get": {"summary": "Prometheus metrics"}},
        "/api/history": {"get": {"summary": "Analyze history"}},
        "/api/analyze": {"post": {"summary": "Legacy analyze"}},
        "/api/workflow/start": {"post": {"summary": "Start workflow"}},
        "/api/workflow/clarify": {"post": {"summary": "Submit clarifications"}},
        "/api/workflow/confirm_spec": {"post": {"summary": "Confirm spec"}},
        "/api/workflow/execute": {"post": {"summary": "Execute workflow"}},
        "/api/workflow/validate": {"post": {"summary": "Validate workflow output"}},
        "/api/v1/workflow/start": {"post": {"summary": "Start workflow (v1)"}},
        "/api/v1/workflow/clarify": {"post": {"summary": "Clarify workflow (v1)"}},
        "/api/v1/workflow/confirm_spec": {"post": {"summary": "Confirm spec (v1)"}},
        "/api/v1/workflow/execute": {"post": {"summary": "Execute workflow async (v1)"}},
        "/api/v1/workflow/validate": {"post": {"summary": "Validate workflow async (v1)"}},
        "/api/v1/jobs/{job_id}": {"get": {"summary": "Get async job status"}},
    },
}
