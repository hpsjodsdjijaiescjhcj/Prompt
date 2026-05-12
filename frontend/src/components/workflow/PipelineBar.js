import React from 'react';
import { STATE_TO_STAGE } from '../../constants';

const PIPELINE = [
  { id: 'input',    icon: '📥', label: '输入' },
  { id: 'clarify',  icon: '💬', label: '澄清' },
  { id: 'align',    icon: '📋', label: '对齐' },
  { id: 'execute',  icon: '⚡', label: '执行' },
  { id: 'validate', icon: '✅', label: '验收' },
  { id: 'done',     icon: '🎉', label: '完成' },
];

export default function PipelineBar({ state, taskType }) {
  const currentStage = STATE_TO_STAGE[state] || 'input';
  const currentIdx = PIPELINE.findIndex((s) => s.id === currentStage);

  return (
    <div className="pipeline-bar">
      {PIPELINE.map((step, idx) => {
        const isDone   = idx < currentIdx;
        const isActive = idx === currentIdx;
        return (
          <React.Fragment key={step.id}>
            {idx > 0 && <span className="pipeline-arrow">›</span>}
            <div className={`pipeline-step ${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`}>
              <span className="step-icon">{isDone ? '✓' : step.icon}</span>
              {step.label}
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
}
