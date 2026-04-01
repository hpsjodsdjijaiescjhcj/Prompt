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
  const preflightValidation = data?.preflight_validation;
  const planGraph = preflightValidation?.plan_graph || data?.plan_graph;
  const logicValidation = validation?.logic_validation;
  const taskSpecShell = data?.task_spec_shell;
  const skillSelection = data?.skill_selection;
  const skillSuggestions = data?.skill_suggestions || [];
  const lightweightSpecValidation = data?.lightweight_spec_validation;
  const lightweightOutputValidation = data?.lightweight_output_validation || validation?.lightweight_validation;
  const repairResult = data?.repair_result;
  const canExecute = executor !== 'prompt_only' && (preflightValidation?.pass ?? true);

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

      {taskSpecShell && (
        <div className="wf-field">
          <label>Unified Task Spec</label>
          <div className="wf-model-list">
            <div className="wf-model-item">
              <div><strong>Goal</strong></div>
              <div className="wf-muted">{taskSpecShell.normalized_goal || 'N/A'}</div>
            </div>
            <div className="wf-model-item">
              <div><strong>Status</strong></div>
              <div className="wf-muted">{taskSpecShell.status || 'N/A'}</div>
            </div>
            <div className="wf-model-item">
              <div><strong>Expected Artifacts</strong></div>
              <div className="wf-muted">{(taskSpecShell.expected_artifacts || []).join(', ') || 'N/A'}</div>
            </div>
            <div className="wf-model-item">
              <div><strong>Missing Fields</strong></div>
              <div className="wf-muted">{(taskSpecShell.missing_fields || []).join(', ') || 'None'}</div>
            </div>
          </div>
        </div>
      )}

      {(skillSelection || skillSuggestions.length > 0) && (
        <div className="wf-field">
          <label>Skill Registry</label>
          <div className="wf-model-list">
            {skillSelection && (
              <div className="wf-model-item">
                <div><strong>Selected Skill</strong> <span className="wf-muted">{skillSelection.name}</span></div>
                <div className="wf-muted">{skillSelection.description}</div>
              </div>
            )}
            {skillSuggestions.map((skill) => (
              <div className="wf-model-item" key={`skill-${skill.name}`}>
                <div><strong>{skill.name}</strong> <span className="wf-muted">score: {skill.score}</span></div>
                <div className="wf-muted">{skill.description}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {lightweightSpecValidation && (
        <div className={`wf-validation ${lightweightSpecValidation.passed ? 'pass' : 'fail'}`}>
          <strong>Lightweight Spec Validation: {lightweightSpecValidation.passed ? 'PASS' : 'FAIL'}</strong>
          {(lightweightSpecValidation.issues || []).map((issue, idx) => (
            <div key={`spec-light-${idx}`}>- {issue.type}: {issue.message}</div>
          ))}
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
          disabled={loading || !canExecute}
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

      {preflightValidation && (
        <div className={`wf-validation ${preflightValidation.pass ? 'pass' : 'fail'}`}>
          <strong>Pre-Execution Logic Gate: {preflightValidation.pass ? 'PASS' : 'FAIL'}</strong>
          {(preflightValidation.precondition_issues || []).map((issue, idx) => (
            <div key={`preflight-pre-${idx}`}>- {issue.type}: {issue.message}</div>
          ))}
          {(preflightValidation.attack_findings || []).map((issue, idx) => (
            <div key={`preflight-legacy-${idx}`}>- {issue.type}: {issue.message}</div>
          ))}
          {(preflightValidation.graph_findings || []).map((issue, idx) => (
            <div key={`preflight-atk-${idx}`}>- {issue.type}: {issue.message}</div>
          ))}
          {(preflightValidation.broken_dependencies || []).map((issue, idx) => (
            <div key={`preflight-broken-${idx}`}>- {issue.type}: {issue.message}</div>
          ))}
        </div>
      )}

      {planGraph && (
        <div className="wf-logic-card">
          <div className="wf-logic-head">
            <strong>Pre-Execution Plan Graph</strong>
            <span className={`wf-risk wf-risk-${preflightValidation?.risk_level || 'low'}`}>
              Risk: {preflightValidation?.risk_level || 'low'}
            </span>
          </div>

          <div className="wf-plan-graph">
            {(planGraph.nodes || []).map((node) => {
              const status = preflightValidation?.node_statuses?.[node.id]?.status || 'pass';
              const missingInputs = preflightValidation?.node_statuses?.[node.id]?.missing_inputs || [];
              const unmetDependencies = preflightValidation?.node_statuses?.[node.id]?.unmet_dependencies || [];
              const nodeTargets = (preflightValidation?.residual_targets || []).filter((target) => target.target_id === node.id);

              return (
                <div className={`wf-plan-node ${status}`} key={node.id}>
                  <div className="wf-plan-node-head">
                    <div>
                      <strong>{node.label}</strong>
                      <div className="wf-muted">{node.id} · {node.kind}</div>
                    </div>
                    <span className={`wf-plan-badge ${status}`}>{status}</span>
                  </div>

                  {(node.depends_on || []).length > 0 && (
                    <div className="wf-plan-meta">
                      Depends on: {(node.depends_on || []).join(', ')}
                    </div>
                  )}

                  {(node.inputs || []).length > 0 && (
                    <div className="wf-plan-meta">
                      Inputs: {(node.inputs || []).join(', ')}
                    </div>
                  )}

                  {missingInputs.length > 0 && (
                    <div className="wf-logic-issue">Missing inputs: {missingInputs.join(', ')}</div>
                  )}
                  {unmetDependencies.length > 0 && (
                    <div className="wf-logic-issue">Broken dependencies: {unmetDependencies.join(', ')}</div>
                  )}

                  {nodeTargets.map((target) => (
                    <div className="wf-plan-target" key={`${node.id}-${target.target_id}`}>
                      <div className="wf-muted">{(target.issue_types || []).join(', ')}</div>
                      {(target.messages || []).map((message, idx) => (
                        <div className="wf-logic-issue" key={`${node.id}-${idx}`}>- {message}</div>
                      ))}
                    </div>
                  ))}
                </div>
              );
            })}
          </div>

          {(planGraph.edges || []).length > 0 && (
            <div className="wf-field">
              <label>Dependencies</label>
              <div className="wf-model-list">
                {planGraph.edges.map((edge) => {
                  const edgeId = `${edge.from}->${edge.to}`;
                  const edgeOk = preflightValidation?.edge_statuses?.[edgeId]?.pass;
                  return (
                    <div className={`wf-model-item ${edgeOk ? '' : 'wf-edge-fail'}`} key={edgeId}>
                      <div><strong>{edge.from}</strong> -> <strong>{edge.to}</strong></div>
                      <div className="wf-muted">{edge.reason}</div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {preflightValidation?.repair_prompt && (
            <div className="wf-field">
              <label>Plan Graph Repair Prompt</label>
              <pre className="wf-pre">{preflightValidation.repair_prompt}</pre>
            </div>
          )}
        </div>
      )}

      {(execution?.raw_output || data?.final_output) && (
        <div className="wf-field">
          <label>Output</label>
          <pre className="wf-pre">{data?.final_output || execution?.raw_output}</pre>
        </div>
      )}

      {validation && (
        <div className={`wf-validation ${validation.pass ? 'pass' : 'fail'}`}>
          <strong>{validation.pass ? 'PASS' : 'FAIL'}</strong>
          {(validation.issues || []).map((issue, idx) => (
            <div key={idx}>- {issue.type}: {issue.message}</div>
          ))}
        </div>
      )}

      {lightweightOutputValidation && (
        <div className={`wf-validation ${lightweightOutputValidation.passed ? 'pass' : 'fail'}`}>
          <strong>Lightweight Output Validation: {lightweightOutputValidation.passed ? 'PASS' : 'FAIL'}</strong>
          {(lightweightOutputValidation.issues || []).map((issue, idx) => (
            <div key={`out-light-${idx}`}>- {issue.type}: {issue.message}</div>
          ))}
        </div>
      )}

      {repairResult && (
        <div className={`wf-validation ${repairResult.success ? 'pass' : 'fail'}`}>
          <strong>Repair Loop: {repairResult.success ? 'SUCCESS' : 'NO_CHANGE'}</strong>
          <div>- attempted: {String(Boolean(repairResult.attempted))}</div>
          <div>- reason: {repairResult.reason || '-'}</div>
        </div>
      )}

      {logicValidation && (
        <div className="wf-logic-card">
          <div className="wf-logic-head">
            <strong>Post-Execution Validation</strong>
            <span className={`wf-risk wf-risk-${logicValidation.risk_level || 'low'}`}>
              Risk: {logicValidation.risk_level || 'low'}
            </span>
          </div>

          {(logicValidation.plan_outline || []).length > 0 && (
            <div className="wf-field">
              <label>Plan Outline</label>
              <div className="wf-model-list">
                {logicValidation.plan_outline.map((step) => (
                  <div className="wf-model-item" key={step.id}>
                    <div><strong>{step.id}</strong> <span className="wf-muted">{step.name}</span></div>
                    <div className="wf-muted">{step.description}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(logicValidation.precondition_issues || []).length > 0 && (
            <div className="wf-field">
              <label>Precondition Gaps</label>
              {(logicValidation.precondition_issues || []).map((issue, idx) => (
                <div className="wf-logic-issue" key={`pre-${idx}`}>- {issue.type}: {issue.message}</div>
              ))}
            </div>
          )}

          {(logicValidation.attack_findings || []).length > 0 && (
            <div className="wf-field">
              <label>Adversarial Findings</label>
              {(logicValidation.attack_findings || []).map((issue, idx) => (
                <div className="wf-logic-issue" key={`atk-${idx}`}>- {issue.type}: {issue.message}</div>
              ))}
            </div>
          )}

          {(logicValidation.residual_targets || []).length > 0 && (
            <div className="wf-field">
              <label>Residual Repair Targets</label>
              <div className="wf-model-list">
                {logicValidation.residual_targets.map((target) => (
                  <div className="wf-model-item" key={target.step_id}>
                    <div><strong>{target.step_id}</strong> <span className="wf-muted">{target.step_name}</span></div>
                    <div className="wf-muted">{(target.issue_types || []).join(', ')}</div>
                    {(target.messages || []).map((message, idx) => (
                      <div className="wf-logic-issue" key={`${target.step_id}-${idx}`}>- {message}</div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          )}

          {logicValidation.repair_prompt && (
            <div className="wf-field">
              <label>Residual Repair Prompt</label>
              <pre className="wf-pre">{logicValidation.repair_prompt}</pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
