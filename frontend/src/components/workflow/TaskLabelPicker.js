import React from 'react';
import { TASK_LABELS } from '../../constants';

export default function TaskLabelPicker({ selected = [], onToggle, compact = false }) {
  const isSelected = (labelId) => selected.some((item) => (typeof item === 'string' ? item === labelId : item?.id === labelId));

  if (compact) {
    return (
      <div className="task-label-picker-compact">
        {TASK_LABELS.map((label) => {
          const isActive = isSelected(label.id);
          return (
            <button
              key={label.id}
              type="button"
              className={`task-label-chip ${isActive ? `active ${label.id}` : ''}`}
              onClick={() => onToggle(label.id)}
              title={label.desc}
            >
              <span>{label.icon}</span>
              {label.label}
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <div className="task-label-picker">
      {TASK_LABELS.map((label) => {
        const isActive = isSelected(label.id);
        return (
          <button
            key={label.id}
            type="button"
            className={`task-label-btn ${isActive ? `active ${label.id}` : ''}`}
            onClick={() => onToggle(label.id)}
            title={label.desc}
          >
            <span className="task-label-icon">{label.icon}</span>
            {label.label}
          </button>
        );
      })}
    </div>
  );
}
