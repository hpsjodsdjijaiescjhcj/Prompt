/**
 * WorkflowContainer - Enterprise-Grade Workflow UI
 * 
 * Modern, responsive design with:
 * - Clear phase progression
 * - Complete input snapshot display
 * - Real-time spec and preflight status
 * - Accessible error handling
 */

import React, { useState, useEffect, useCallback } from 'react';
import APIClient from '../../api_v2';
import { translateFieldLabel, translateFieldValue, translateAcceptanceCriteria } from '../../i18n/fieldTranslations';
import WorkflowStagePanel from './WorkflowStagePanel';
import ClarifyForm from './ClarifyForm';
import './WorkflowContainer.css';

const PHASE_STATUS_META = {
  completed: { label: '已通过', tone: 'success', icon: '✓' },
  active: { label: '进行中', tone: 'active', icon: '●' },
  failed: { label: '执行失败', tone: 'danger', icon: '!' },
  pending: { label: '等待中', tone: 'muted', icon: '○' },
};

const WORKFLOW_PHASES = [
  { id: 'input', label: '输入', icon: '📝', description: '输入任务需求' },
  { id: 'clarify', label: '澄清', icon: '❓', description: '补充必要信息' },
  { id: 'spec', label: '规格', icon: '📋', description: '生成执行规格' },
  { id: 'preflight', label: '预检', icon: '✓', description: '逻辑校验' },
  { id: 'execute', label: '执行', icon: '⚙️', description: '任务执行' },
  { id: 'validate', label: '验证', icon: '✅', description: '结果验证' },
];

const STATE_TO_PHASE = {
  input_received: 'input',
  clarifying: 'clarify',
  spec_ready: 'spec',
  preflight_check: 'preflight',
  preflight_failed: 'preflight',
  preflight_passed: 'execute',
  ready_for_execution: 'execute',
  executing: 'execute',
  executed: 'validate',
  validating: 'validate',
  validation_failed: 'validate',
  completed: 'validate',
  failed: 'validate',
  done: 'validate',
};

function derivePhase(sessionLike) {
  const state = sessionLike?.state;
  return STATE_TO_PHASE[state] || 'clarify';
}

function getPhaseStatus({ phaseId, currentPhase, session, loading, error }) {
  const currentIndex = WORKFLOW_PHASES.findIndex((p) => p.id === currentPhase);
  const phaseIndex = WORKFLOW_PHASES.findIndex((p) => p.id === phaseId);
  const state = session?.state;

  if (phaseId === currentPhase) {
    if (error && (state === 'preflight_failed' || state === 'validation_failed' || state === 'failed')) {
      return 'failed';
    }
    return loading ? 'active' : 'active';
  }

  if (phaseId === 'preflight' && state === 'preflight_failed') {
    return 'failed';
  }

  if (phaseId === 'validate' && (state === 'validation_failed' || state === 'failed')) {
    return 'failed';
  }

  if (phaseIndex < currentIndex) {
    return 'completed';
  }

  return 'pending';
}

export default function WorkflowContainer({
  userText,
  initialData,
  onComplete,
  onWorkflowUpdate,
}) {
   const [sessionId, setSessionId] = useState(initialData?.session_id || null);
   const [currentPhase, setCurrentPhase] = useState(derivePhase(initialData));
   const [session, setSession] = useState(initialData || null);
   const [loading, setLoading] = useState(false);
   const [error, setError] = useState(null);
   const [runtimeStatus, setRuntimeStatus] = useState(null);

  // ════════════════════════════════════════════════════════════════════════
  // INITIALIZATION
  // ════════════════════════════════════════════════════════════════════════

  useEffect(() => {
    if (initialData?.session_id) {
      setSessionId(initialData.session_id);
      setSession(initialData);
      setCurrentPhase(derivePhase(initialData));
    }
  }, [initialData]);

  useEffect(() => {
    if (!session) return;
    if (onWorkflowUpdate) {
      onWorkflowUpdate(session);
    }
  }, [session, onWorkflowUpdate]);

  useEffect(() => {
    let cancelled = false;
    APIClient.getRuntimeStatus()
      .then((status) => {
        if (!cancelled) {
          setRuntimeStatus(status);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setRuntimeStatus({ llm: { configured: false, provider: 'local', model: 'deterministic-fallback' } });
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

   useEffect(() => {
     if (!userText || sessionId || initialData?.session_id) return;

     const initSession = async () => {
       try {
         setLoading(true);
         const result = await APIClient.createSession(userText);
         setSessionId(result.session_id);

         const clarification = await APIClient.processClarification(result.session_id);
         const updated = await APIClient.getSession(result.session_id);
         
         // Attach clarification schema to session for rendering
         if (clarification.schema) {
           updated.clarification_schema = clarification.schema;
         }
         setSession(updated);

          if (clarification.should_skip) {
            // 自动跳过澄清，直接生成规格
            const specResult = await APIClient.alignSpecification(result.session_id);
            const specUpdated = await APIClient.getSession(result.session_id);
            setSession(specUpdated.specification ? specUpdated : { ...specUpdated, specification: specResult.specification || specUpdated.specification });
            setCurrentPhase('spec');
          } else {
            setCurrentPhase('clarify');
          }
       } catch (err) {
         setError({
           title: '初始化失败',
           message: err.message,
           type: 'error',
         });
       } finally {
         setLoading(false);
       }
     };

     initSession();
   }, [userText, sessionId, initialData]);

  // ════════════════════════════════════════════════════════════════════════
  // PHASE HANDLERS
  // ════════════════════════════════════════════════════════════════════════

  const handleClarification = useCallback(async (answers = {}) => {
    try {
      setLoading(true);
      await APIClient.submitClarificationAnswers(sessionId, answers);
      const specResult = await APIClient.alignSpecification(sessionId);
      const updated = await APIClient.getSession(sessionId);
      setSession(updated.specification ? updated : { ...updated, specification: specResult.specification || updated.specification });
      setCurrentPhase('spec');
    } catch (err) {
      setError({
        title: '澄清提交失败',
        message: err.message,
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const handleSkipToSpec = useCallback(async () => {
    try {
      setLoading(true);
      const specResult = await APIClient.alignSpecification(sessionId);
      const updated = await APIClient.getSession(sessionId);
      setSession(updated.specification ? updated : { ...updated, specification: specResult.specification || updated.specification });
      setCurrentPhase('spec');
    } catch (err) {
      setError({
        title: '规格生成失败',
        message: err.message,
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const handleSpecUpdate = useCallback(async (updates) => {
    try {
      setLoading(true);
      await APIClient.updateSpecification(sessionId, updates);
      const updated = await APIClient.getSession(sessionId);
      setSession(updated);
      setError({
        title: '规格已更新',
        message: '您的更改已保存',
        type: 'success',
      });
    } catch (err) {
      setError({
        title: '规格更新失败',
        message: err.message,
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const handleProceedToPreflight = useCallback(async () => {
    try {
      setLoading(true);
      await APIClient.alignSpecification(sessionId);
      const updated = await APIClient.getSession(sessionId);
      setSession(updated);
      setCurrentPhase('preflight');
    } catch (err) {
      setError({
        title: '规格对齐失败',
        message: err.message,
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const handleRunPreflight = useCallback(async () => {
    try {
      setLoading(true);
      const result = await APIClient.runPreflight(sessionId);
      const updated = await APIClient.getSession(sessionId);
      setSession({ ...updated, preflight_validation: result });

      if (result.passed) {
        setCurrentPhase('execute');
      } else {
        setError({
          title: '预检未通过',
          message: '请根据建议修改规格',
          issues: result.issues,
          suggestions: result.recovery_suggestions,
          type: 'warning',
        });
      }
    } catch (err) {
      setError({
        title: '预检执行失败',
        message: err.message,
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const handleExecute = useCallback(async () => {
    try {
      setLoading(true);
      const result = await APIClient.execute(sessionId);

        if (result.success) {
          const updated = await APIClient.getSession(sessionId);
          setSession({ ...updated, execution_result: result.output ? result : updated.execution_result });
          setCurrentPhase('validate');
      } else {
        setError({
          title: '执行失败',
          message: result.error,
          type: 'error',
        });
      }
    } catch (err) {
      setError({
        title: '执行异常',
        message: err.message,
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  }, [sessionId]);

  const handleValidate = useCallback(async () => {
    try {
      setLoading(true);
      const result = await APIClient.validateOutput(sessionId);
      const updated = await APIClient.getSession(sessionId);
      setSession({ ...updated, output_validation: result });

      if (result.passed) {
        setCurrentPhase('complete');
        if (onComplete) {
          onComplete(updated);
        }
      } else {
        setError({
          title: '验证未通过',
          message: '请检查输出是否满足验收标准',
          issues: result.issues,
          type: 'warning',
        });
      }
    } catch (err) {
      setError({
        title: '验证失败',
        message: err.message,
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  }, [sessionId, onComplete]);

  // ════════════════════════════════════════════════════════════════════════
  // RENDER
  // ════════════════════════════════════════════════════════════════════════

  if (!sessionId && !userText) {
    return (
      <div className="workflow-loading">
        <div className="spinner"></div>
        <p>等待工作流数据...</p>
      </div>
    );
  }

  if (!sessionId) {
    return (
      <div className="workflow-loading">
        <div className="spinner"></div>
        <p>初始化工作流...</p>
      </div>
    );
  }

  return (
    <div className="workflow-container">
      <div className="workflow-header">
        <h1>AI 任务编排系统</h1>
        <p>把模糊需求变成可执行、可验证、可优化的任务流程</p>
      </div>

      <div className="workflow-body">
        <div className="workflow-main">
          {error && (
            <ErrorPanel
              error={error}
              onClose={() => setError(null)}
            />
          )}

          {session && (
            <SnapshotPanel session={session} />
          )}

          {session && (
            <WorkflowStagePanel session={session} currentPhase={currentPhase} />
          )}

          <div className="workflow-content">
            {currentPhase === 'clarify' && session?.clarification_schema && (
              <ClarificationPhase
                session={session}
                onSubmit={handleClarification}
                onSkip={handleSkipToSpec}
                loading={loading}
              />
            )}

            {currentPhase === 'spec' && (
              session?.specification ? (
                <SpecificationPhase
                  session={session}
                  onUpdate={handleSpecUpdate}
                  onProceed={handleProceedToPreflight}
                  loading={loading}
                />
              ) : (
                <div className="phase-card">
                  <div className="phase-card-header">
                    <h2>📋 规格生成中</h2>
                    <p className="phase-card-desc">正在根据你的输入构建执行规格，请稍候刷新当前会话。</p>
                  </div>
                </div>
              )
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
                runtimeStatus={runtimeStatus}
              />
            )}

            {currentPhase === 'validate' && session?.execution_result && (
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

        <WorkflowProgressSidebar
          currentPhase={currentPhase}
          session={session}
          loading={loading}
          error={error}
        />
      </div>
    </div>
  );
}

// ════════════════════════════════════════════════════════════════════════
// COMPONENTS
// ════════════════════════════════════════════════════════════════════════

function ErrorPanel({ error, onClose }) {
  return (
    <div className={`error-panel error-${error.type}`}>
      <div className="error-header">
        <span className="error-icon">
          {error.type === 'error' && '❌'}
          {error.type === 'warning' && '⚠️'}
          {error.type === 'success' && '✅'}
        </span>
        <h3>{error.title}</h3>
        <button className="btn-close" onClick={onClose}>×</button>
      </div>
      <p className="error-message">{error.message}</p>
      {error.issues && (
        <div className="error-issues">
          <h4>问题详情：</h4>
          <ul>
            {error.issues.map((issue, idx) => (
              <li key={idx}>
                <strong>{issue.message}</strong>
                {issue.suggestion && <p>{issue.suggestion}</p>}
              </li>
            ))}
          </ul>
        </div>
      )}
      {error.suggestions && (
        <div className="error-suggestions">
          <h4>修复建议：</h4>
          <ul>
            {error.suggestions.map((suggestion, idx) => (
              <li key={idx}>{suggestion}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function SnapshotPanel({ session }) {
  const translatedContext = Object.fromEntries(
    Object.entries(session.specification?.context || {}).map(([key, value]) => [
      translateFieldLabel(key, 'zh'),
      Array.isArray(value)
        ? translateFieldValue(value, 'zh')
        : translateFieldValue(value, 'zh'),
    ])
  );

  return (
    <div className="snapshot-panel">
      <h3>📸 完整快照</h3>
      <div className="snapshot-content">
        <div className="snapshot-section">
          <h4>用户输入</h4>
          <p>{session.user_input.text}</p>
        </div>
        {session.specification && (
          <>
            <div className="snapshot-section">
              <h4>任务目标</h4>
              <p>{session.specification.objective}</p>
            </div>
            <div className="snapshot-section">
              <h4>背景信息</h4>
              <pre>{JSON.stringify(translatedContext, null, 2)}</pre>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function ClarificationPhase({ session, onSubmit, onSkip, loading }) {
  if (!session.clarification_schema) {
    return <div className="phase-content">加载澄清表单中...</div>;
  }

  const schema = session.clarification_schema;

  if (!schema.fields || schema.fields.length === 0) {
    return (
      <div className="phase-card">
        <div className="phase-card-header">
          <h2>✅ {schema.title || '无需补充信息'}</h2>
          <p className="phase-card-desc">{schema.description}</p>
        </div>
        <div className="clarify-skip-state">
          <p>当前输入已满足最少必要信息要求。你可以直接生成规格，也可以回到输入区补充更多上下文。</p>
          <div className="phase-actions">
            <button className="btn-primary" onClick={onSkip} disabled={loading}>
              {loading ? '生成中...' : '直接生成规格'}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="phase-card">
      <div className="phase-card-header">
        <h2>❓ {schema.title || '补充信息'}</h2>
        <p className="phase-card-desc">{schema.description}</p>
      </div>
      <ClarifyForm
        schema={schema}
        onSubmit={onSubmit}
        loading={loading}
      />
    </div>
  );
}

function SpecificationPhase({ session, onUpdate, onProceed, loading }) {
   const spec = session.specification;
   const [editMode, setEditMode] = useState(false);
   const [editedSpec, setEditedSpec] = useState(spec);
  const translatedContext = Object.fromEntries(
    Object.entries(spec.context || {}).map(([key, value]) => [
      translateFieldLabel(key, 'zh'),
      translateFieldValue(value, 'zh'),
    ])
  );
  const translatedAcceptanceCriteria = translateAcceptanceCriteria(spec.acceptance_criteria, 'zh');

  if (!spec) {
    return <div>规格生成中...</div>;
  }

  const handleSaveEdit = async () => {
    try {
      await onUpdate(editedSpec);
      setEditMode(false);
    } catch (err) {
      console.error('保存失败:', err);
    }
  };

  return (
    <div className="phase-content">
      <h2>执行规格</h2>
      
       {/* Edit Mode Toggle */}
       <div className="spec-toolbar">
         <button
           className="btn-secondary"
           onClick={() => setEditMode(!editMode)}
         >
           {editMode ? '取消编辑' : '编辑规格'}
         </button>
       </div>

       {/* Original vs Refined Comparison - Always Visible */}
       <div className="spec-comparison">
          <div className="comparison-column">
            <h3>📝 原始输入</h3>
            <div className="comparison-content">
              <p>{session.user_input?.text || '无'}</p>
            </div>
          </div>
          <div className="comparison-arrow">→</div>
          <div className="comparison-column">
            <h3>✨ 专业化改写</h3>
            <div className="comparison-content">
              <p><strong>目标：</strong> {spec.objective}</p>
              <p><strong>背景：</strong> {JSON.stringify(translatedContext)}</p>
            </div>
          </div>
       </div>

       {/* Editable Spec Display */}
      <div className={`spec-display ${editMode ? 'edit-mode' : ''}`}>
        <div className="spec-section">
          <h3>任务目标</h3>
          {editMode ? (
            <textarea
              value={editedSpec.objective}
              onChange={(e) => setEditedSpec({ ...editedSpec, objective: e.target.value })}
              className="spec-textarea"
            />
          ) : (
            <p>{spec.objective}</p>
          )}
        </div>
        <div className="spec-section">
          <h3>背景信息</h3>
          {editMode ? (
            <textarea
              value={JSON.stringify(editedSpec.context, null, 2)}
              onChange={(e) => {
                try {
                  setEditedSpec({ ...editedSpec, context: JSON.parse(e.target.value) });
                } catch (err) {
                  // 保持原值
                }
              }}
              className="spec-textarea"
            />
          ) : (
            <pre>{JSON.stringify(translatedContext, null, 2)}</pre>
          )}
        </div>
        <div className="spec-section">
          <h3>约束条件</h3>
          {editMode ? (
            <textarea
              value={JSON.stringify(editedSpec.constraints, null, 2)}
              onChange={(e) => {
                try {
                  setEditedSpec({ ...editedSpec, constraints: JSON.parse(e.target.value) });
                } catch (err) {
                  // 保持原值
                }
              }}
              className="spec-textarea"
            />
          ) : (
            <pre>{JSON.stringify(spec.constraints, null, 2)}</pre>
          )}
        </div>
        <div className="spec-section">
          <h3>验收标准</h3>
          {editMode ? (
            <textarea
              value={editedSpec.acceptance_criteria?.join('\n') || ''}
              onChange={(e) => setEditedSpec({ ...editedSpec, acceptance_criteria: e.target.value.split('\n').filter(Boolean) })}
              className="spec-textarea"
              placeholder="每行一个标准"
            />
          ) : (
            <ul>
              {translatedAcceptanceCriteria?.map((criterion, idx) => (
                <li key={idx}>{criterion}</li>
              ))}
            </ul>
          )}
        </div>
      </div>

      {/* Actions */}
      <div className="phase-actions">
        {editMode ? (
          <>
            <button
              className="btn-primary"
              onClick={handleSaveEdit}
              disabled={loading}
            >
              {loading ? '保存中...' : '保存更改'}
            </button>
            <button
              className="btn-secondary"
              onClick={() => {
                setEditMode(false);
                setEditedSpec(spec);
              }}
            >
              取消
            </button>
          </>
        ) : (
          <button
            className="btn-primary"
            onClick={onProceed}
            disabled={loading}
          >
            {loading ? '处理中...' : '继续到预检'}
          </button>
        )}
      </div>
    </div>
  );
}

function PreflightPhase({ session, onRun, loading }) {
  const validation = session.preflight_validation;

  return (
    <div className="phase-content">
      <h2>执行前逻辑校验</h2>
      {validation ? (
        <div className={`validation-result ${validation.passed ? 'passed' : 'failed'}`}>
          <h3>{validation.passed ? '✅ 预检通过' : '❌ 预检未通过'}</h3>
          {validation.issues.length > 0 && (
            <div className="issues-list">
              {validation.issues.map((issue, idx) => (
                <div key={idx} className={`issue issue-${issue.severity}`}>
                  <strong>{issue.message}</strong>
                  {issue.suggestion && <p>{issue.suggestion}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <button
          className="btn-primary"
          onClick={onRun}
          disabled={loading}
        >
          {loading ? '校验中...' : '运行预检'}
        </button>
      )}
    </div>
  );
}

function ExecutionPhase({ session, onExecute, loading, runtimeStatus }) {
   const spec = session.specification;
   const validation = session.preflight_validation;
   const llm = runtimeStatus?.llm;
   const providerLabel = llm?.provider === 'qwen' ? '千问' : llm?.provider === 'doubao' ? '豆包' : '本地降级';
   const executionMode = llm?.configured ? 'api_primary' : 'fallback_rule';

   // ⚠️ CRITICAL: Block execution if preflight failed
   if (!validation || !validation.passed) {
     return (
       <div className="phase-content">
         <div className={`validation-result failed`}>
           <h3>❌ 无法执行：预检未通过</h3>
           <p style={{ marginTop: '1rem', color: 'var(--color-text-secondary)' }}>
             执行前必须通过预检验证。请返回预检阶段查看问题并修复规格。
           </p>
           {validation?.issues && validation.issues.length > 0 && (
             <div className="issues-list" style={{ marginTop: '1rem' }}>
               {validation.issues.map((issue, idx) => (
                 <div key={idx} className={`issue issue-${issue.severity}`}>
                   <strong>{issue.message}</strong>
                   {issue.suggestion && <p>{issue.suggestion}</p>}
                 </div>
               ))}
             </div>
           )}
         </div>
       </div>
     );
   }

   return (
     <div className="phase-content">
       <h2>✅ 预检已通过 - 任务执行</h2>
      
      {/* Execution Configuration */}
      <div className="execution-config">
        <div className="config-section">
          <h3>运行时执行器</h3>
          <div className={`runtime-card ${llm?.configured ? 'configured' : 'fallback'}`}>
            <div className="runtime-card-main">
              <span className="runtime-status-dot" aria-hidden="true"></span>
              <div>
                <div className="runtime-title">
                  {llm?.configured ? `${providerLabel} API 已配置` : '本地 fallback 模式'}
                </div>
                <div className="runtime-description">
                  {llm?.configured
                    ? `将通过 ${providerLabel} 的 OpenAI-compatible 接口执行任务。`
                    : '未检测到完整的豆包/千问配置，系统会生成可验证的基础交付稿。'}
                </div>
              </div>
            </div>
            <div className="runtime-meta">
              <span>Provider: {llm?.provider || 'local'}</span>
              <span>Model: {llm?.model || 'deterministic-fallback'}</span>
              <span>Mode: {executionMode}</span>
            </div>
          </div>
        </div>

        {/* Execution Summary */}
        <div className="execution-summary">
          <h3>📋 执行摘要</h3>
          <div className="summary-item">
            <span className="label">任务目标：</span>
            <span className="value">{spec?.objective}</span>
          </div>
          <div className="summary-item">
            <span className="label">执行模型：</span>
            <span className="value">{llm?.configured ? `${providerLabel} / ${llm.model}` : 'deterministic-fallback'}</span>
          </div>
          <div className="summary-item">
            <span className="label">执行模式：</span>
            <span className="value">{executionMode}</span>
          </div>
        </div>
      </div>

      {/* Execute Button */}
      <div className="phase-actions">
        <button
          className="btn-primary"
          onClick={onExecute}
          disabled={loading}
        >
          {loading ? '执行中...' : '开始执行'}
        </button>
      </div>
    </div>
  );
}

function ValidationPhase({ session, onValidate, loading }) {
  const result = session.execution_result;
  const validation = session.output_validation;

  return (
    <div className="phase-content">
      <h2>结果验证</h2>
      {result && (
        <div className="execution-result">
          <h3>执行结果</h3>
          <div className="result-output">
            <pre>{result.output}</pre>
          </div>
          <p className="result-meta">
            执行时间: {result.execution_time_ms}ms | 模型: {result.model_used} | 模式: {result.inference_mode || 'fallback_rule'}
          </p>
        </div>
      )}
      {validation ? (
        <div className={`validation-result ${validation.passed ? 'passed' : 'failed'}`}>
          <h3>{validation.passed ? '✅ 验证通过' : '❌ 验证未通过'}</h3>
          {validation.issues.length > 0 && (
            <div className="issues-list">
              {validation.issues.map((issue, idx) => (
                <div key={idx} className={`issue issue-${issue.severity}`}>
                  <strong>{issue.message}</strong>
                  {issue.suggestion && <p>{issue.suggestion}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <button
          className="btn-primary"
          onClick={onValidate}
          disabled={loading}
        >
          {loading ? '验证中...' : '验证结果'}
        </button>
      )}
    </div>
  );
}

function WorkflowProgressSidebar({ currentPhase, session, loading, error }) {
  return (
    <aside className="workflow-sidebar">
      <div className="workflow-sidebar-card">
        <div className="workflow-sidebar-header">
          <h3>工作流进度</h3>
          <p>实时展示当前阶段、阻塞原因与整体状态。</p>
        </div>
        <div className="workflow-sidebar-list">
          {WORKFLOW_PHASES.map((phase) => {
            const status = getPhaseStatus({ phaseId: phase.id, currentPhase, session, loading, error });
            const meta = PHASE_STATUS_META[status];
            return (
              <div key={phase.id} className={`workflow-sidebar-item status-${meta.tone}`}>
                <div className="workflow-sidebar-item-main">
                  <div className="workflow-sidebar-icon">{phase.icon}</div>
                  <div>
                    <div className="workflow-sidebar-title-row">
                      <strong>{phase.label}</strong>
                      <span className={`workflow-status-badge badge-${meta.tone}`}>{meta.icon} {meta.label}</span>
                    </div>
                    <p>{phase.description}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </aside>
  );
}

function CompletionPhase({ session }) {
  return (
    <div className="phase-content completion">
      <h2>✅ 任务完成</h2>
      <p>您的任务已成功完成并通过验证。</p>
      <div className="completion-summary">
        <p>执行结果已保存，您可以随时查看历史记录。</p>
      </div>
    </div>
  );
}
