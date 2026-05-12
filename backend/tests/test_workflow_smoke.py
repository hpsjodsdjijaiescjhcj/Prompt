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
