/**
 * WorkflowStagePanel - Collapsible stage history display
 * 
 * Shows all completed stages with user input and system responses
 * Allows users to review and understand the workflow progression
 */

import React, { useState } from 'react';
import { translateFieldLabel, translateFieldValue, translateAcceptanceCriteria } from '../../i18n/fieldTranslations';
import './WorkflowStagePanel.css';

export default function WorkflowStagePanel({ session, currentPhase }) {
  const [expandedStages, setExpandedStages] = useState({});

  const toggleStage = (stageId) => {
    setExpandedStages(prev => ({
      ...prev,
      [stageId]: !prev[stageId]
    }));
  };

  const stages = buildStages(session);

  return (
    <div className="workflow-stage-panel">
      <div className="stage-panel-header">
        <h3>📋 工作流阶段</h3>
        <p className="stage-panel-subtitle">点击展开查看每个阶段的详情</p>
      </div>

      <div className="stages-list">
        {stages.map(stage => (
          <div
            key={stage.id}
            className={`stage-item ${stage.status} ${expandedStages[stage.id] ? 'expanded' : ''}`}
          >
            {/* Stage Header */}
            <button
              className="stage-header"
              onClick={() => toggleStage(stage.id)}
            >
              <div className="stage-icon">{stage.icon}</div>
              <div className="stage-info">
                <div className="stage-title">{stage.title}</div>
                <div className="stage-status">{stage.statusLabel}</div>
              </div>
              <div className="stage-toggle">
                {expandedStages[stage.id] ? '▼' : '▶'}
              </div>
            </button>

            {/* Stage Content */}
            {expandedStages[stage.id] && (
              <div className="stage-content">
                {stage.userInput && (
                  <div className="stage-section">
                    <h4>👤 用户输入</h4>
                    <div className="stage-data">
                      {React.isValidElement(stage.userInput) ? (
                        stage.userInput
                      ) : typeof stage.userInput === 'object' ? (
                        <pre>{JSON.stringify(stage.userInput, null, 2)}</pre>
                      ) : (
                        <p>{stage.userInput}</p>
                      )}
                    </div>
                  </div>
                )}

                {stage.systemResponse && (
                  <div className="stage-section">
                    <h4>🤖 系统回复</h4>
                    <div className="stage-data">
                      {React.isValidElement(stage.systemResponse) ? (
                        stage.systemResponse
                      ) : typeof stage.systemResponse === 'object' ? (
                        <pre>{JSON.stringify(stage.systemResponse, null, 2)}</pre>
                      ) : (
                        <p>{stage.systemResponse}</p>
                      )}
                    </div>
                  </div>
                )}

                {stage.details && (
                  <div className="stage-section">
                    <h4>📊 详细信息</h4>
                    <div className="stage-details">
                      {Object.entries(stage.details).map(([key, value]) => (
                        <div key={key} className="detail-item">
                          <span className="detail-label">{key}:</span>
                          <span className="detail-value">
                            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Build stage list from session data
 */
function buildStages(session) {
  if (!session) return [];

  const stages = [];

  // Stage 1: Input
  if (session.user_input) {
    stages.push({
      id: 'input',
      icon: '📝',
      title: '输入',
      status: 'completed',
      statusLabel: '已完成',
      userInput: session.user_input.text,
      systemResponse: null,
      details: {
        '提交时间': new Date(session.user_input.timestamp || Date.now()).toLocaleString('zh-CN'),
      },
    });
  }

  // Stage 2: Clarification
  if (session.clarification_schema || session.clarification_answers) {
    const isCompleted = !!session.clarification_answers;
    stages.push({
      id: 'clarify',
      icon: '❓',
      title: '澄清',
      status: isCompleted ? 'completed' : 'pending',
      statusLabel: isCompleted ? '已完成' : '待处理',
      userInput: session.clarification_answers ? (
        <ClarificationAnswersDisplay answers={session.clarification_answers} schema={session.clarification_schema} />
      ) : null,
      systemResponse: session.clarification_schema ? (
        <ClarificationSchemaDisplay schema={session.clarification_schema} />
      ) : null,
    });
  }

  // Stage 3: Specification
  if (session.specification) {
    stages.push({
      id: 'spec',
      icon: '📋',
      title: '规格',
      status: 'completed',
      statusLabel: '已完成',
      userInput: null,
      systemResponse: (
        <SpecificationDisplay spec={session.specification} />
      ),
      details: {
        '目标': session.specification.objective,
        '约束数量': Object.keys(session.specification.constraints || {}).length,
        '验收标准数': (session.specification.acceptance_criteria || []).length,
      },
    });
  }

  // Stage 4: Preflight
  if (session.preflight_validation) {
    const validation = session.preflight_validation;
    stages.push({
      id: 'preflight',
      icon: '✓',
      title: '预检',
      status: validation.passed ? 'completed' : 'failed',
      statusLabel: validation.passed ? '通过' : '未通过',
      userInput: null,
      systemResponse: (
        <PreflightDisplay validation={validation} />
      ),
      details: {
        '问题数': validation.issues?.length || 0,
        '结果': validation.passed ? '✅ 通过' : '❌ 未通过',
      },
    });
  }

  // Stage 5: Execution
  if (session.execution_result) {
    stages.push({
      id: 'execute',
      icon: '⚙️',
      title: '执行',
      status: 'completed',
      statusLabel: '已完成',
      userInput: null,
      systemResponse: (
        <ExecutionDisplay result={session.execution_result} />
      ),
      details: {
        '模型': session.execution_result.model_used,
        '执行时间': `${session.execution_result.execution_time_ms}ms`,
      },
    });
  }

  // Stage 6: Validation
  if (session.output_validation) {
    const validation = session.output_validation;
    stages.push({
      id: 'validate',
      icon: '✅',
      title: '验证',
      status: validation.passed ? 'completed' : 'failed',
      statusLabel: validation.passed ? '通过' : '未通过',
      userInput: null,
      systemResponse: (
        <ValidationDisplay validation={validation} />
      ),
      details: {
        '问题数': validation.issues?.length || 0,
        '结果': validation.passed ? '✅ 通过' : '❌ 未通过',
      },
    });
  }

  return stages;
}

/**
 * Display clarification answers
 */
function ClarificationAnswersDisplay({ answers, schema }) {
   if (!answers || Object.keys(answers).length === 0) {
     return <p>无答案</p>;
   }

   // Handle nested structure: answers.answers or answers.inferred_answers
   const userAnswers = answers.answers || answers;
   const inferredAnswers = answers.inferred_answers || {};

   return (
     <div className="answers-display">
       {/* User-provided answers */}
       {Object.entries(userAnswers).map(([key, value]) => {
         const field = schema?.fields?.find(f => f.key === key);
         const label = translateFieldLabel(key, 'zh');
         const displayValue = Array.isArray(value)
           ? value.map(v => translateFieldValue(v, 'zh')).join(', ')
           : translateFieldValue(value, 'zh');

         return (
           <div key={key} className="answer-item">
             <strong>{label}:</strong>
             <span>{displayValue}</span>
           </div>
         );
       })}

       {/* Inferred answers (if any) */}
       {Object.keys(inferredAnswers).length > 0 && (
         <>
           <div className="answer-divider" style={{ margin: '12px 0', borderTop: '1px solid #e0e0e0' }} />
           <div style={{ fontSize: '12px', color: '#999', marginBottom: '8px' }}>🤖 系统推断</div>
           {Object.entries(inferredAnswers).map(([key, value]) => {
             const label = translateFieldLabel(key, 'zh');
             const displayValue = Array.isArray(value)
               ? value.map(v => translateFieldValue(v, 'zh')).join(', ')
               : translateFieldValue(value, 'zh');

             return (
               <div key={`inferred-${key}`} className="answer-item" style={{ opacity: 0.7 }}>
                 <strong>{label}:</strong>
                 <span>{displayValue}</span>
               </div>
             );
           })}
         </>
       )}
     </div>
   );
 }

/**
 * Display clarification schema
 */
function ClarificationSchemaDisplay({ schema }) {
  if (!schema || !schema.fields) {
    return <p>无澄清字段</p>;
  }

  return (
    <div className="schema-display">
      <p className="schema-title">{schema.title || '需要澄清的信息'}</p>
      <p className="schema-description">{schema.description}</p>
      <div className="schema-fields">
        {schema.fields.map(field => (
          <div key={field.key} className="schema-field">
            <span className="field-label">{translateFieldLabel(field.key, 'zh')}</span>
            <span className="field-type">{field.field_type}</span>
            {field.required && <span className="field-required">必填</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Display specification
 */
function SpecificationDisplay({ spec }) {
  const translatedContext = Object.fromEntries(
    Object.entries(spec.context || {}).map(([key, value]) => [
      translateFieldLabel(key, 'zh'),
      translateFieldValue(value, 'zh'),
    ])
  );
  const translatedCriteria = translateAcceptanceCriteria(spec.acceptance_criteria, 'zh');

  return (
    <div className="spec-display">
      <div className="spec-item">
        <strong>目标:</strong>
        <p>{spec.objective}</p>
      </div>
      <div className="spec-item">
        <strong>背景:</strong>
        <pre>{JSON.stringify(translatedContext, null, 2)}</pre>
      </div>
      <div className="spec-item">
        <strong>验收标准:</strong>
        <ul>
          {translatedCriteria.map((criterion, idx) => (
            <li key={idx}>{criterion}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}

/**
 * Display preflight validation
 */
function PreflightDisplay({ validation }) {
  return (
    <div className={`validation-display ${validation.passed ? 'passed' : 'failed'}`}>
      <div className="validation-status">
        {validation.passed ? '✅ 预检通过' : '❌ 预检未通过'}
      </div>
      {validation.issues && validation.issues.length > 0 && (
        <div className="issues-list">
          <strong>问题:</strong>
          <ul>
            {validation.issues.map((issue, idx) => (
              <li key={idx}>
                <span className={`severity-${issue.severity}`}>{issue.message}</span>
                {issue.suggestion && <p className="suggestion">{issue.suggestion}</p>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/**
 * Display execution result
 */
function ExecutionDisplay({ result }) {
  return (
    <div className="execution-display">
      <div className="execution-meta">
        <span>模型: {result.model_used}</span>
        <span>耗时: {result.execution_time_ms}ms</span>
      </div>
      <div className="execution-output">
        <strong>输出:</strong>
        <pre>{result.output}</pre>
      </div>
    </div>
  );
}

/**
 * Display validation result
 */
function ValidationDisplay({ validation }) {
  return (
    <div className={`validation-display ${validation.passed ? 'passed' : 'failed'}`}>
      <div className="validation-status">
        {validation.passed ? '✅ 验证通过' : '❌ 验证未通过'}
      </div>
      {validation.issues && validation.issues.length > 0 && (
        <div className="issues-list">
          <strong>问题:</strong>
          <ul>
            {validation.issues.map((issue, idx) => (
              <li key={idx}>
                <span className={`severity-${issue.severity}`}>{issue.message}</span>
                {issue.suggestion && <p className="suggestion">{issue.suggestion}</p>}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
