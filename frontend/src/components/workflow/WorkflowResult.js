import React, { useState, useMemo } from 'react';

/* ── Copy helper ──────────────────────────────────────────── */
function copyText(text) {
  if (!text) return Promise.resolve();
  if (navigator.clipboard?.writeText) return navigator.clipboard.writeText(text);
  const ta = document.createElement('textarea');
  ta.value = text;
  document.body.appendChild(ta);
  ta.select();
  document.execCommand('copy');
  document.body.removeChild(ta);
  return Promise.resolve();
}

/* ── Plan Graph ───────────────────────────────────────────── */
function PlanGraph({ planGraph, preflight }) {
  if (!planGraph?.nodes?.length) return null;

  return (
    <div style={{ marginBottom: 16 }}>
      <div className="spec-section-title" style={{ marginBottom: 10 }}>
        执行计划图
      </div>
      <div className="plan-graph">
        {planGraph.nodes.map((node) => {
          const ns = preflight?.node_statuses?.[node.id] || {};
          const status = ns.status || 'pass';
          const missing = ns.missing_inputs || [];
          const unmet   = ns.unmet_dependencies || [];

          return (
            <div key={node.id} className={`plan-node ${status}`}>
              <div className="plan-node-head">
                <div>
                  <strong>{node.label || node.id}</strong>
                  <span className="text-muted text-xs" style={{ marginLeft: 8 }}>
                    {node.kind}
                  </span>
                </div>
                <span className={`plan-badge ${status}`}>
                  {status === 'pass' ? '✓ 通过' : status === 'fail' ? '✗ 失败' : '⚠ 警告'}
                </span>
              </div>
              {(node.depends_on?.length > 0 || node.inputs?.length > 0 || missing.length > 0 || unmet.length > 0) && (
                <div className="plan-node-body">
                  {node.depends_on?.length > 0 && (
                    <div className="plan-node-meta">
                      <span className="plan-meta-tag">依赖: {node.depends_on.join(', ')}</span>
                    </div>
                  )}
                  {missing.length > 0 && (
                    <div style={{ color: 'var(--danger)', fontSize: 12, marginTop: 4 }}>
                      缺少输入: {missing.join(', ')}
                    </div>
                  )}
                  {unmet.length > 0 && (
                    <div style={{ color: 'var(--danger)', fontSize: 12, marginTop: 4 }}>
                      依赖未满足: {unmet.join(', ')}
                    </div>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

/* ── Validation Report ────────────────────────────────────── */
function ValidationReport({ validation, lightweightOutput, repairResult, logicValidation }) {
  if (!validation && !lightweightOutput && !repairResult && !logicValidation) return null;

  return (
    <div>
      <div className="spec-section-title" style={{ marginBottom: 10 }}>验收报告</div>

      {validation && (
        <div className="validation-result">
          <div className={`validation-header ${validation.pass ? 'pass' : 'fail'}`}>
            <span>{validation.pass ? '✅' : '❌'}</span>
            主验收：{validation.pass ? '通过' : '未通过'}
          </div>
          {(validation.issues || []).length > 0 && (
            <div className="validation-body">
              {validation.issues.map((issue, i) => (
                <div key={i} className="validation-issue">
                  <span>•</span>
                  <span><strong>{issue.type}</strong>：{issue.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {lightweightOutput && (
        <div className="validation-result">
          <div className={`validation-header ${lightweightOutput.passed ? 'pass' : 'fail'}`}>
            <span>{lightweightOutput.passed ? '✅' : '❌'}</span>
            格式校验：{lightweightOutput.passed ? '通过' : '未通过'}
          </div>
          {(lightweightOutput.issues || []).length > 0 && (
            <div className="validation-body">
              {lightweightOutput.issues.map((issue, i) => (
                <div key={i} className="validation-issue">
                  <span>•</span>
                  <span>{issue.type}：{issue.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {logicValidation && (
        <div className="validation-result">
          <div className={`validation-header ${logicValidation.pass !== false ? 'pass' : 'fail'}`}>
            <span>{logicValidation.pass !== false ? '✅' : '❌'}</span>
            逻辑校验
            {logicValidation.risk_level && (
              <span style={{ marginLeft: 8, fontWeight: 400, fontSize: 12 }}>
                风险等级：{logicValidation.risk_level}
              </span>
            )}
          </div>
          {(logicValidation.precondition_issues?.length > 0 || logicValidation.attack_findings?.length > 0) && (
            <div className="validation-body">
              {[...(logicValidation.precondition_issues || []), ...(logicValidation.attack_findings || [])].map((issue, i) => (
                <div key={i} className="validation-issue">
                  <span>•</span>
                  <span>{issue.type}：{issue.message}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {repairResult && (
        <div className={`validation-result`}>
          <div className={`validation-header ${repairResult.success ? 'pass' : 'fail'}`}>
            <span>{repairResult.success ? '✅' : '⚠️'}</span>
            自动修复：{repairResult.success ? '修复成功' : '修复未改善'}
            {repairResult.reason && (
              <span style={{ marginLeft: 8, fontWeight: 400, fontSize: 12 }}>
                — {repairResult.reason}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── WorkflowResult ───────────────────────────────────────── */
export default function WorkflowResult({ data, onExecute, onValidate, loading }) {
  const [executor, setExecutor] = useState(
    data?.route?.selected_executor || 'prompt_only'
  );
  const [config, setConfig] = useState({ api_base_url: '', api_key: '', model: '' });
  const [copied, setCopied]   = useState(false);

  const promptText = useMemo(() => {
    const prompts = data?.generated_prompts || [];
    return prompts.find((p) => p.executor === executor)?.prompt || prompts[0]?.prompt || '';
  }, [data, executor]);

  const execution  = data?.execution;
  const validation = data?.validation;
  const preflight  = data?.preflight_validation;
  const planGraph  = preflight?.plan_graph || data?.plan_graph;
  const logicVal   = validation?.logic_validation;
  const lightOut   = data?.lightweight_output_validation || validation?.lightweight_validation;
  const repair     = data?.repair_result;

  const canExecute = executor !== 'prompt_only' && (preflight?.pass ?? true);
  const hasOutput  = !!(execution?.raw_output || data?.final_output);

  const execOptions = data?.route?.recommended_executors || ['prompt_only'];

  const handleCopy = async () => {
    await copyText(promptText);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="card fade-in">
      <div className="card-header">
        <div className="card-title">
          <span className="card-title-icon">⚡</span>
          执行与结果
        </div>
        <span className="card-badge">
          {data?.state === 'done' ? '已完成' : '执行阶段'}
        </span>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

        {/* ── Model Recommendations ──────────────────── */}
        {data?.route?.recommended_models?.length > 0 && (
          <div>
            <div className="spec-section-title" style={{ marginBottom: 10 }}>推荐模型</div>
            <div className="model-cards">
              {data.route.recommended_models.slice(0, 4).map((m, i) => (
                <div key={`${m.name}-${i}`} className={`model-card ${i === 0 ? 'rank-1' : ''}`}>
                  <div className="model-name">{m.name}</div>
                  <div className="model-provider">{m.provider}</div>
                  <span className="model-match">{m.match_pct}% 匹配</span>
                  <div className="model-reason">{m.reason}</div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Plan Graph ────────────────────────────── */}
        {planGraph && <PlanGraph planGraph={planGraph} preflight={preflight} />}

        {/* ── Executor Selection ────────────────────── */}
        <div>
          <div className="spec-section-title" style={{ marginBottom: 10 }}>执行器</div>

          <div className="executor-tabs">
            {execOptions.map((ex) => (
              <button
                key={ex}
                className={`executor-tab ${executor === ex ? 'active' : ''}`}
                onClick={() => setExecutor(ex)}
              >
                {ex === 'prompt_only' ? '📝 仅生成提示词' : ex === 'local_lmstudio' ? '🖥 本地 LMStudio' : `🔌 ${ex}`}
              </button>
            ))}
          </div>

          {executor !== 'prompt_only' && (
            <div className="form-grid-2" style={{ marginBottom: 16 }}>
              <div className="form-field">
                <div className="form-label">API Base URL</div>
                <input
                  className="form-input"
                  type="text"
                  placeholder="https://api.example.com/v1"
                  value={config.api_base_url}
                  onChange={(e) => setConfig((p) => ({ ...p, api_base_url: e.target.value }))}
                />
              </div>
              <div className="form-field">
                <div className="form-label">Model</div>
                <input
                  className="form-input"
                  type="text"
                  placeholder="gpt-4o / claude-3-5-sonnet"
                  value={config.model}
                  onChange={(e) => setConfig((p) => ({ ...p, model: e.target.value }))}
                />
              </div>
              <div className="form-field form-span-2">
                <div className="form-label">API Key</div>
                <input
                  className="form-input"
                  type="password"
                  placeholder="sk-..."
                  value={config.api_key}
                  onChange={(e) => setConfig((p) => ({ ...p, api_key: e.target.value }))}
                />
              </div>
            </div>
          )}

          {/* Generated Prompt */}
          {promptText && (
            <div>
              <div className="form-label" style={{ marginBottom: 8 }}>
                生成的提示词
              </div>
              <div className="prompt-output">{promptText}</div>
              <button
                className="btn btn-ghost btn-sm"
                style={{ marginTop: 8 }}
                onClick={handleCopy}
              >
                {copied ? '✓ 已复制' : '复制提示词'}
              </button>
            </div>
          )}

          {/* Action buttons */}
          {!hasOutput && (
            <div className="gap-row" style={{ marginTop: 16 }}>
              <button
                type="button"
                className="btn btn-primary"
                disabled={loading || !canExecute}
                onClick={() => onExecute(executor, config)}
                title={!canExecute && executor !== 'prompt_only' ? '执行前门控未通过，无法执行' : ''}
              >
                {loading ? '执行中...' : '▶ 开始执行'}
              </button>
              {executor !== 'prompt_only' && !preflight?.pass && (
                <span className="text-sm" style={{ color: 'var(--danger)' }}>
                  ⚠ 预检未通过，执行被锁定
                </span>
              )}
            </div>
          )}
        </div>

        {/* ── Output ────────────────────────────────── */}
        {hasOutput && (
          <div>
            <div className="spec-section-title" style={{ marginBottom: 10 }}>
              执行输出
            </div>
            <div className="raw-output">
              {data?.final_output || execution?.raw_output}
            </div>

            {!validation && (
              <div className="gap-row" style={{ marginTop: 12 }}>
                <button
                  type="button"
                  className="btn btn-secondary"
                  disabled={loading}
                  onClick={() => onValidate(false)}
                >
                  {loading ? '验收中...' : '✅ 运行验收'}
                </button>
                {executor !== 'prompt_only' && (
                  <button
                    type="button"
                    className="btn btn-ghost"
                    disabled={loading}
                    onClick={() => onValidate(true)}
                  >
                    🔄 自动修复后验收
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* ── Validation Results ─────────────────────── */}
        <ValidationReport
          validation={validation}
          lightweightOutput={lightOut}
          repairResult={repair}
          logicValidation={logicVal}
        />

      </div>
    </div>
  );
}
