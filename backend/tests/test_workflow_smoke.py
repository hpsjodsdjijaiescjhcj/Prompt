from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import app as app_module


def test_health_endpoint():
    client = app_module.app.test_client()
    resp = client.get('/api/health')
    assert resp.status_code == 200
    body = resp.get_json()
    assert body['status'] == 'ok'
    liveness = client.get('/api/health/liveness')
    assert liveness.status_code == 200
    openapi = client.get('/openapi.json')
    assert openapi.status_code == 200


def test_workflow_start_and_clarify_email():
    client = app_module.app.test_client()

    start_resp = client.post('/api/workflow/start', json={'text': '帮我写一封催发票邮件'})
    assert start_resp.status_code == 200
    start_data = start_resp.get_json()
    assert start_data['task_type'] in {'email', 'generic', 'writing', 'code', 'other'}

    if start_data['state'] == 'clarifying':
        session_id = start_data['session_id']
        clarify_resp = client.post('/api/workflow/clarify', json={'session_id': session_id, 'answers': {
            'clarified_request': '写一封催供应商开票邮件',
            'output_preference': 'direct',
            'recipient_type': 'vendor',
            'relationship': 'existing',
            'purpose': 'request_invoice',
            'tone': 'professional',
            'language': 'zh',
            'word_limit': 180,
            'include_deadline': True,
            'deadline_text': '请于5月10日前回复',
            'include_bullets': True,
            'background': '订单已完成，发票未回传，影响对账',
        }})
        assert clarify_resp.status_code in {200, 400}


def test_workflow_execute_idempotency_conflict_without_redis_lock():
    # This test only checks API shape. Lock conflict requires redis and concurrent calls.
    client = app_module.app.test_client()

    start_resp = client.post('/api/workflow/start', json={'text': '解释四面楚歌的意思'})
    assert start_resp.status_code == 200


def test_v2_vertical_slice_executes_without_external_llm(monkeypatch):
    monkeypatch.delenv("DOUBAO_API_KEY", raising=False)
    monkeypatch.delenv("QWEN_API_KEY", raising=False)

    from orchestrator.service_v2 import OrchestrationService

    service = OrchestrationService(llm_client=None, store=None)

    session = service.create_session(
        "帮我写一封专业邮件，提醒供应商尽快补开发票",
        selected_domains=["communication"],
        selected_characteristics=["generative"],
    )

    clarification = service.process_clarification(session.session_id)
    assert "should_skip" in clarification

    if not clarification["should_skip"]:
        service.submit_clarification_answers(
            session.session_id,
            {
                "recipient": "供应商",
                "communication_goal": "request",
                "tone_preference": "formal",
                "background": "订单已经完成，发票尚未回传，影响对账。",
                "acceptance_criteria": "包含明确请求\n语气专业",
            },
        )

    spec_result = service.align_specification(session.session_id)
    assert spec_result["success"] is True
    assert spec_result["specification"]["objective"]

    preflight = service.run_preflight(session.session_id)
    assert preflight["passed"] is True

    execution = service.execute(session.session_id)
    assert execution["success"] is True
    assert execution["output"].strip()
    assert execution["inference_mode"] == "fallback_rule"
    assert execution["provider"] == "local"

    validation = service.validate_output(session.session_id)
    assert validation["passed"] is True
