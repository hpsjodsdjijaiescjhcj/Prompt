import React from 'react';
import { STATE_TO_STAGE, STAGES } from '../../constants';
import { useI18n } from '../../i18n/useI18n';

function stageIndex(stageId) {
  return STAGES.findIndex((s) => s.id === stageId);
}

export default function ContextPanel({ workflow }) {
  const { t, isZh } = useI18n();
  const visible = !!workflow;

   const currentStage = STATE_TO_STAGE[workflow?.state] || 'input';
   const currentIdx = stageIndex(currentStage);
 
   const spec = workflow?.spec_draft || workflow?.specification || workflow?.spec;
   const preflight = workflow?.preflight_validation;
   const preflightStatus = preflight
     ? (preflight.passed ? 'pass' : 'fail')
     : (workflow?.state === 'spec_ready' || workflow?.state === 'preflight_check' || workflow?.state === 'executing' ? 'pending' : null);

  return (
    <aside className={`context-panel ${!visible ? 'hidden' : ''}`}>
      {visible && (
        <>
          <div className="context-panel-header">
            <span className="context-panel-title">{isZh ? '任务上下文' : 'Task Context'}</span>
            <span className={`type-badge ${workflow?.task_type || 'generic'}`}>
              {workflow?.task_type || 'generic'}
            </span>
          </div>

          <div className="context-panel-body">
            {/* Stage progress */}
            <div className="context-section">
                <div className="context-section-title">{isZh ? '执行阶段' : 'Workflow Stage'}</div>
              <div className="context-stage-list">
                {STAGES.map((stage, idx) => {
                  const isDone   = idx < currentIdx;
                  const isActive = idx === currentIdx;
                  return (
                    <div
                      key={stage.id}
                      className={`context-stage-item ${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`}
                    >
                      <div className="context-stage-dot" />
                      <span>{stage.icon}</span>
                      <span>{stage.label}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Spec summary */}
            {spec && (
              <div className="context-section">
                <div className="context-section-title">{t('specTitle')}</div>

                {spec.objective && (
                  <div className="context-spec-field">
                    <div className="context-spec-key">目标</div>
                    <div className="context-spec-val">{spec.objective}</div>
                  </div>
                )}

                {(spec.tone || spec.language) && (
                  <div className="context-spec-field">
                    <div className="context-spec-key">风格 / 语言</div>
                    <div className="context-spec-val">
                      {[spec.tone, spec.language].filter(Boolean).join(' · ')}
                    </div>
                  </div>
                )}

                {spec.constraints?.word_limit && (
                  <div className="context-spec-field">
                    <div className="context-spec-key">字数限制</div>
                    <div className="context-spec-val">{spec.constraints.word_limit} 字</div>
                  </div>
                )}

                {spec.acceptance_criteria?.length > 0 && (
                  <div className="context-spec-field">
                    <div className="context-spec-key">验收标准</div>
                    <div className="context-spec-val">
                      {spec.acceptance_criteria.slice(0, 2).map((c, i) => (
                        <div key={i} style={{ marginBottom: 2 }}>• {c}</div>
                      ))}
                      {spec.acceptance_criteria.length > 2 && (
                        <span className="text-muted text-xs">
                          +{spec.acceptance_criteria.length - 2} 条
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Preflight status */}
            {preflightStatus && (
              <div className="context-section">
                <div className="context-section-title">{t('preflightTitle')}</div>
                <div className={`context-preflight-badge ${preflightStatus}`}>
                  {preflightStatus === 'pass' && '✅ 预检通过，可执行'}
                  {preflightStatus === 'fail' && '❌ 预检不通过'}
                  {preflightStatus === 'pending' && '⏳ 等待预检'}
                </div>

                 {preflight && !preflight.passed && (
                   <div style={{ marginTop: 8 }}>
                     {[
                       ...(preflight.issues || []),
                       ...(preflight.precondition_issues || []),
                       ...(preflight.graph_findings || []),
                       ...(preflight.broken_dependencies || []),
                     ].slice(0, 3).map((issue, i) => (
                       <div key={i} className="text-sm text-muted" style={{ marginBottom: 4 }}>
                         • {typeof issue === 'string' ? issue : (issue.message || issue.type || issue)}
                       </div>
                     ))}
                   </div>
                 )}
              </div>
            )}

            {/* Route / model info */}
            {workflow?.route?.recommended_models?.length > 0 && (
              <div className="context-section">
                <div className="context-section-title">{t('recommendedModel')}</div>
                {workflow.route.recommended_models.slice(0, 2).map((m, i) => (
                  <div key={i} className="context-spec-field">
                    <div className="context-spec-key">{m.name}</div>
                    <div className="context-spec-val">{m.match_pct}% 匹配</div>
                  </div>
                ))}
              </div>
            )}

            {/* Task spec shell */}
            {workflow?.task_spec_shell?.normalized_goal && (
              <div className="context-section">
                <div className="context-section-title">标准化目标</div>
                <div className="context-spec-val text-sm">
                  {workflow.task_spec_shell.normalized_goal}
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </aside>
  );
}
