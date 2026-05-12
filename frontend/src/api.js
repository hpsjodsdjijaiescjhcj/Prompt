const API_BASE = 'http://localhost:5001';

export async function analyzeInput(input) {
  const res = await fetch(`${API_BASE}/api/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ input }),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error || '请求失败');
  }
  return res.json();
}

export async function fetchHistory() {
  const res = await fetch(`${API_BASE}/api/history`);
  if (!res.ok) return { history: [] };
  return res.json();
}

export async function deleteHistory(historyId) {
  const res = await fetch(`${API_BASE}/api/history/${historyId}`, {
    method: 'DELETE',
    headers: { 'Content-Type': 'application/json' },
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.error?.message || '删除失败');
  }
  return res.json();
}

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    return res.json();
  } catch {
    return { status: 'error', ollama_available: false };
  }
}

async function postJson(path, body, idempotencyKey = null) {
  const headers = { 'Content-Type': 'application/json' };
  if (idempotencyKey) {
    headers['Idempotency-Key'] = idempotencyKey;
  }
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers,
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) {
    const msg = typeof data?.error === 'string'
      ? data.error
      : (data?.error?.message || '请求失败');
    throw new Error(msg);
  }
  return data;
}

export function workflowStart(text, preferredExecutor = null, context = {}) {
  return postJson('/api/workflow/start', {
    text,
    preferred_executor: preferredExecutor,
    context,
  });
}

export function workflowClarify(sessionId, answers) {
  return postJson('/api/workflow/clarify', {
    session_id: sessionId,
    answers,
  });
}

export function workflowConfirmSpec(sessionId, spec) {
  return postJson('/api/workflow/confirm_spec', {
    session_id: sessionId,
    spec,
  });
}

export function workflowExecute(sessionId, executor, executorConfig = {}) {
  return postJson('/api/workflow/execute', {
    session_id: sessionId,
    executor,
    executor_config: executorConfig,
  });
}

export function workflowValidate(sessionId, autoRevise = false, output = null) {
  return postJson('/api/workflow/validate', {
    session_id: sessionId,
    auto_revise: autoRevise,
    output,
  });
}

export function workflowExecuteAsync(sessionId, executor, executorConfig = {}) {
  return postJson('/api/v1/workflow/execute', {
    session_id: sessionId,
    executor,
    executor_config: executorConfig,
  });
}

export function workflowValidateAsync(sessionId, autoRevise = false, output = null) {
  return postJson('/api/v1/workflow/validate', {
    session_id: sessionId,
    auto_revise: autoRevise,
    output,
  });
}

export async function workflowJobStatus(jobId) {
  const res = await fetch(`${API_BASE}/api/v1/jobs/${jobId}`);
  const data = await res.json();
  if (!res.ok) {
    const msg = typeof data?.error === 'string'
      ? data.error
      : (data?.error?.message || '请求失败');
    throw new Error(msg);
  }
  return data;
}
