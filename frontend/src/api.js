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

export async function checkHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    return res.json();
  } catch {
    return { status: 'error', ollama_available: false };
  }
}
