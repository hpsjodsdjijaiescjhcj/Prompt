/**
 * WorkflowOrchestrator - Main Workflow UI Component
 * 
 * Displays complete workflow with all phases:
 * Input → Clarification → Specification → Preflight → Execution → Validation
 */

import React, { useState, useEffect } from 'react';
import APIClient from '../../api_v2';
import './WorkflowOrchestrator.css';

const WORKFLOW_PHASES = [
  { id: 'input', label: '输入', icon: '📝' },
  { id: 'clarify', label: '澄清', icon: '❓' },
  { id: 'spec', label: '规格', icon: '📋' },
  { id: 'preflight', label: '预检', icon: '✓' },
  { id: 'execute', label: '执行', icon: '⚙️' },
  { id: 'validate', label: '验证', icon: '✅' },
];

export default function WorkflowOrchestrator({ userText, onComplete }) {
  const [sessionId, setSessionId] = useState(null);
  const [currentPhase, setCurrentPhase] = useState('input');
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // ════════════════════════════════════════════════════════════════════════
  // PHASE 1: CREATE SESSION
  // ════════════════════════════════════════════════════════════════════════

  useEffect(() => {
    if (!userText || sessionId) return;

    const initSession = async () => {
      try {
        setLoading(true);
        const result = await APIClient.createSession(userText);
        setSessionId(result.session_id);

        const clarification = await APIClient.processClarification(result.session_id);
        const updated = await APIClient.getSession(result.session_id);
        setSession(updated);

        if (clarification.should_skip) {
          await APIClient.alignSpecification(result.session_id);
          const specReady = await APIClient.getSession(result.session_id);
          setSession(specReady);
          setCurrentPhase('spec');
        } else {
          setCurrentPhase('clarify');
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    initSession();
  }, [userText, sessionId]);

  // ════════════════════════════════════════════════════════════════════════
  // PHASE 2: CLARIFICATION
  // ════════════════════════════════════════════════════════════════════════

  const handleClarification = async (answers) => {
    try {
      setLoading(true);
      await APIClient.submitClarificationAnswers(sessionId, answers);
      const updated = await APIClient.getSession(sessionId);
      setSession(updated);
      setCurrentPhase('spec');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ════════════════════════════════════════════════════════════════════════
  // PHASE 3: SPECIFICATION
  // ════════════════════════════════════════════════════════════════════════

  const handleSpecUpdate = async (updates) => {
    try {
      setLoading(true);
      await APIClient.updateSpecification(sessionId, updates);
      const updated = await APIClient.getSession(sessionId);
      setSession(updated);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleProceedToPreflight = async () => {
    try {
      setLoading(true);
      await APIClient.alignSpecification(sessionId);
      const updated = await APIClient.getSession(sessionId);
      setSession(updated);
      setCurrentPhase('preflight');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ════════════════════════════════════════════════════════════════════════
  // PHASE 4: PREFLIGHT
  // ════════════════════════════════════════════════════════════════════════

  const handleRunPreflight = async () => {
    try {
      setLoading(true);
      const result = await APIClient.runPreflight(sessionId);
      const updated = await APIClient.getSession(sessionId);
      setSession(updated);

      if (result.passed) {
        setCurrentPhase('execute');
      } else {
        setError(`预检失败: ${result.issues.map(i => i.message).join(', ')}`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ════════════════════════════════════════════════════════════════════════
  // PHASE 5: EXECUTION
  // ════════════════════════════════════════════════════════════════════════

  const handleExecute = async () => {
    try {
      setLoading(true);
      const result = await APIClient.execute(sessionId);

      if (result.success) {
        const updated = await APIClient.getSession(sessionId);
        setSession(updated);
        setCurrentPhase('validate');
      } else {
        setError(`执行失败: ${result.error}`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ════════════════════════════════════════════════════════════════════════
  // PHASE 6: VALIDATION
  // ════════════════════════════════════════════════════════════════════════

  const handleValidate = async () => {
    try {
      setLoading(true);
      const result = await APIClient.validateOutput(sessionId);
      const updated = await APIClient.getSession(sessionId);
      setSession(updated);

      if (result.passed) {
        setCurrentPhase('complete');
        if (onComplete) {
          onComplete(updated);
        }
      } else {
        setError(`验证失败: ${result.issues.map(i => i.message).join(', ')}`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // ════════════════════════════════════════════════════════════════════════
  // RENDER
  // ════════════════════════════════════════════════════════════════════════

  if (!sessionId) {
    return <div className="workflow-loading">初始化中...</div>;
  }

  return (
    <div className="workflow-orchestrator">
      {/* Phase Progress Bar */}
      <div className="workflow-phases">
        {WORKFLOW_PHASES.map((phase) => (
          <div
            key={phase.id}
            className={`phase-item ${
              currentPhase === phase.id ? 'active' : ''
            } ${
              WORKFLOW_PHASES.findIndex(p => p.id === currentPhase) >
              WORKFLOW_PHASES.findIndex(p => p.id === phase.id)
                ? 'completed'
                : ''
            }`}
          >
            <div className="phase-icon">{phase.icon}</div>
            <div className="phase-label">{phase.label}</div>
          </div>
        ))}
      </div>

      {/* Error Display */}
      {error && (
        <div className="workflow-error">
          <span>⚠️ {error}</span>
          <button onClick={() => setError(null)}>关闭</button>
        </div>
      )}

      {/* Phase Content */}
      <div className="workflow-content">
        {currentPhase === 'clarify' && (
          <ClarificationPhase
            session={session}
            onSubmit={handleClarification}
            loading={loading}
          />
        )}

        {currentPhase === 'spec' && (
          <SpecificationPhase
            session={session}
            onUpdate={handleSpecUpdate}
            onProceed={handleProceedToPreflight}
            loading={loading}
          />
        )}

        {currentPhase === 'preflight' && (
          <PreflightPhase
            session={session}
            onRun={handleRunPreflight}
            loading={loading}
          />
        )}

        {currentPhase === 'execute' && (
          <ExecutionPhase
            session={session}
            onExecute={handleExecute}
            loading={loading}
          />
        )}

        {currentPhase === 'validate' && (
          <ValidationPhase
            session={session}
            onValidate={handleValidate}
            loading={loading}
          />
        )}

        {currentPhase === 'complete' && (
          <CompletionPhase session={session} />
        )}
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// PHASE COMPONENTS
// ════════════════════════════════════════════════════════════════════════

function ClarificationPhase({ session, onSubmit, loading }) {
  const [answers, setAnswers] = useState({});

  const schema = session?.clarification_schema;

  if (!schema || schema.fields.length === 0) {
    return (
      <div className="phase-content">
        <h3>✓ 输入已足够完整</h3>
        <p>系统已理解您的需求，无需补充信息。</p>
        <button
          className="btn-primary"
          onClick={() => onSubmit({})}
          disabled={loading}
        >
          继续 →
        </button>
      </div>
    );
  }

  return (
    <div className="phase-content">
      <h3>❓ 澄清信息</h3>
      <p>为了更好地理解您的需求，请补充以下信息：</p>

      <form className="clarification-form">
        {schema.fields.map((field) => (
          <div key={field.key} className="form-group">
            <label>{field.label}</label>
            {field.required && <span className="required">*</span>}

            {field.field_type === 'short_text' && (
              <input
                type="text"
                placeholder={field.placeholder}
                value={answers[field.key] || ''}
                onChange={(e) =>
                  setAnswers({ ...answers, [field.key]: e.target.value })
                }
              />
            )}

            {field.field_type === 'multiline_text' && (
              <textarea
                placeholder={field.placeholder}
                value={answers[field.key] || ''}
                onChange={(e) =>
                  setAnswers({ ...answers, [field.key]: e.target.value })
                }
              />
            )}

            {field.field_type === 'single_choice' && (
              <select
                value={answers[field.key] || ''}
                onChange={(e) =>
                  setAnswers({ ...answers, [field.key]: e.target.value })
                }
              >
                <option value="">-- 请选择 --</option>
                {field.options.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            )}

            {field.field_type === 'multi_choice' && (
              <div className="checkbox-group">
                {field.options.map((opt) => (
                  <label key={opt.value} className="checkbox">
                    <input
                      type="checkbox"
                      checked={
                        (answers[field.key] || []).includes(opt.value)
                      }
                      onChange={(e) => {
                        const current = answers[field.key] || [];
                        setAnswers({
                          ...answers,
                          [field.key]: e.target.checked
                            ? [...current, opt.value]
                            : current.filter((v) => v !== opt.value),
                        });
                      }}
                    />
                    {opt.label}
                  </label>
                ))}
              </div>
            )}
          </div>
        ))}
      </form>

      <button
        className="btn-primary"
        onClick={() => onSubmit(answers)}
        disabled={loading}
      >
        {loading ? '提交中...' : '提交 →'}
      </button>
    </div>
  );
}

function SpecificationPhase({ session, onUpdate, onProceed, loading }) {
  const spec = session?.specification;

  if (!spec) {
    return <div className="phase-content">规格生成中...</div>;
  }

  return (
    <div className="phase-content">
      <h3>📋 任务规格</h3>

      <div className="spec-section">
        <h4>目标</h4>
        <p>{spec.objective}</p>
      </div>

      <div className="spec-section">
        <h4>背景信息</h4>
        <pre>{JSON.stringify(spec.context, null, 2)}</pre>
      </div>

      <div className="spec-section">
        <h4>约束条件</h4>
        <pre>{JSON.stringify(spec.constraints, null, 2)}</pre>
      </div>

      <div className="spec-section">
        <h4>验收标准</h4>
        <ul>
          {spec.acceptance_criteria.map((c, i) => (
            <li key={i}>{c}</li>
          ))}
        </ul>
      </div>

      <button
        className="btn-primary"
        onClick={onProceed}
        disabled={loading}
      >
        {loading ? '处理中...' : '继续 →'}
      </button>
    </div>
  );
}

function PreflightPhase({ session, onRun, loading }) {
  const validation = session?.preflight_validation;

  return (
    <div className="phase-content">
      <h3>✓ 执行前检查</h3>

      {validation ? (
        <>
          <div className={`validation-result ${validation.passed ? 'passed' : 'failed'}`}>
            {validation.passed ? '✓ 检查通过' : '✗ 检查失败'}
          </div>

          {validation.issues.length > 0 && (
            <div className="issues-list">
              {validation.issues.map((issue, i) => (
                <div key={i} className={`issue ${issue.severity}`}>
                  <strong>{issue.message}</strong>
                  <p>{issue.suggestion}</p>
                </div>
              ))}
            </div>
          )}
        </>
      ) : (
        <p>正在运行预检...</p>
      )}

      <button
        className="btn-primary"
        onClick={onRun}
        disabled={loading}
      >
        {loading ? '检查中...' : '运行检查 →'}
      </button>
    </div>
  );
}

function ExecutionPhase({ session, onExecute, loading }) {
  return (
    <div className="phase-content">
      <h3>⚙️ 执行任务</h3>
      <p>系统已准备好执行您的任务。</p>

      <button
        className="btn-primary"
        onClick={onExecute}
        disabled={loading}
      >
        {loading ? '执行中...' : '开始执行 →'}
      </button>
    </div>
  );
}

function ValidationPhase({ session, onValidate, loading }) {
  const result = session?.execution_result;

  return (
    <div className="phase-content">
      <h3>✅ 验证输出</h3>

      {result && (
        <div className="execution-result">
          <h4>执行结果</h4>
          <pre>{result.output}</pre>
        </div>
      )}

      <button
        className="btn-primary"
        onClick={onValidate}
        disabled={loading}
      >
        {loading ? '验证中...' : '验证结果 →'}
      </button>
    </div>
  );
}

function CompletionPhase({ session }) {
  const result = session?.execution_result;

  return (
    <div className="phase-content">
      <h3>✅ 任务完成</h3>

      {result && (
        <div className="completion-result">
          <h4>最终输出</h4>
          <pre>{result.output}</pre>
          <p className="execution-time">
            执行耗时: {result.execution_time_ms}ms
          </p>
        </div>
      )}
    </div>
  );
}
