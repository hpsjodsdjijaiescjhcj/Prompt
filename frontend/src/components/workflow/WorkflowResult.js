import React, { useMemo, useState } from 'react';

function copyText(text) {
  if (!text) return;
  if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(text);
  const ta = document.createElement('textarea');
  ta.value = text;
  document.body.appendChild(ta);
  ta.select();
  document.execCommand('copy');
  document.body.removeChild(ta);
  return Promise.resolve();
}

export default function WorkflowResult({ data, onExecute, onValidate, loading }) {
  const [executor, setExecutor] = useState(data?.route?.selected_executor || 'prompt_only');
  const [config, setConfig] = useState({ api_base_url: '', api_key: '', model: '' });
  const [copiedIdx, setCopiedIdx] = useState(null);

  const promptText = useMemo(
    () => (data?.generated_prompts || []).find((p) => p.executor === executor)?.prompt || (data?.generated_prompts || [])[0]?.prompt || '',
    [data, executor]
  );

  const execution = data?.execution;
  const validation = data?.validation;

  return (
    <div className="wf-card">
      <h3>Workflow Results</h3>

      {(data?.route?.recommended_models || []).length > 0 && (
        <div className="wf-field">
          <label>Recommended Models</label>
          <div className="wf-model-list">
            {data.route.recommended_models.map((m, idx) => (
              <div className="wf-model-item" key={`${m.name}-${idx}`}>
                <div><strong>{m.name}</strong> <span className="wf-muted">by {m.provider}</span></div>
                <div className="wf-muted">Match: {m.match_pct}%</div>
                <div className="wf-muted">{m.reason}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="wf-field">
        <label>Executor</label>
        <select className="wf-input" value={executor} onChange={(e) => setExecutor(e.target.value)}>
          {(data?.route?.recommended_executors || ['prompt_only']).map((ex) => (
            <option value={ex} key={ex}>{ex}</option>
          ))}
        </select>
      </div>

      {executor !== 'prompt_only' && (
        <div className="wf-grid-2">
          <div className="wf-field">
            <label>API Base URL</label>
            <input className="wf-input" value={config.api_base_url} onChange={(e) => setConfig((p) => ({ ...p, api_base_url: e.target.value }))} />
          </div>
          <div className="wf-field">
            <label>Model</label>
            <input className="wf-input" value={config.model} onChange={(e) => setConfig((p) => ({ ...p, model: e.target.value }))} />
          </div>
          <div className="wf-field wf-span-2">
            <label>API Key</label>
            <input className="wf-input" type="password" value={config.api_key} onChange={(e) => setConfig((p) => ({ ...p, api_key: e.target.value }))} />
          </div>
        </div>
      )}

      <div className="wf-field">
        <label>Generated Prompt</label>
        <pre className="wf-pre">{promptText || 'No prompt available.'}</pre>
        <button
          className="action-btn ghost"
          type="button"
          onClick={() => {
            copyText(promptText);
            setCopiedIdx(0);
            setTimeout(() => setCopiedIdx(null), 1200);
          }}
        >
          {copiedIdx === 0 ? 'Copied' : 'Copy Prompt'}
        </button>
      </div>

      <div className="wf-actions">
        <button
          type="button"
          className="action-btn"
          disabled={loading || executor === 'prompt_only'}
          onClick={() => onExecute(executor, config)}
        >
          {loading ? 'Running...' : 'Run Execution'}
        </button>
        <button
          type="button"
          className="action-btn ghost"
          disabled={loading || (!execution?.raw_output && !data?.final_output)}
          onClick={() => onValidate(false)}
        >
          Run Validation
        </button>
        <button
          type="button"
          className="action-btn ghost"
          disabled={loading || (!execution?.raw_output && !data?.final_output) || executor === 'prompt_only'}
          onClick={() => onValidate(true)}
        >
          Auto Revise
        </button>
      </div>

      {(execution?.raw_output || data?.final_output) && (
        <div className="wf-field">
          <label>Output</label>
          <pre className="wf-pre">{data?.final_output || execution?.raw_output}</pre>
        </div>
      )}

      {validation && (
        <div className={`wf-validation ${validation.pass ? 'pass' : 'fail'}`}>
          <strong>{validation.pass ? 'PASS' : 'FAIL'}</strong>
          {!validation.pass && (validation.issues || []).map((issue, idx) => (
            <div key={idx}>- {issue.type}: {issue.message}</div>
          ))}
        </div>
      )}
    </div>
  );
}
