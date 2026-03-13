import React from 'react';

const TASK_TYPE_ICONS = {
  writing: '✍️', coding: '💻', academic: '📚',
  business: '📊', search: '🔎', reasoning: '🧩',
};

export default function HistoryPanel({ history, onSelect, onClose }) {
  if (!history || history.length === 0) {
    return (
      <div className="history-panel">
        <div className="history-header">
          <h3>历史记录</h3>
          <button className="history-close" onClick={onClose}>&#x2715;</button>
        </div>
        <div className="history-empty">暂无历史记录</div>
      </div>
    );
  }

  const formatTime = (ts) => {
    const d = new Date(ts * 1000);
    const now = new Date();
    if (d.toDateString() === now.toDateString()) {
      return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
    }
    return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="history-panel">
      <div className="history-header">
        <h3>历史记录</h3>
        <button className="history-close" onClick={onClose}>&#x2715;</button>
      </div>
      <div className="history-list">
        {history.map((item) => (
          <button
            key={item.id}
            className="history-item"
            onClick={() => onSelect(item.input)}
          >
            <div className="history-item-top">
              <span className="history-types">
                {item.classification?.task_types?.slice(0, 2).map((t, i) => (
                  <span key={i}>{TASK_TYPE_ICONS[t.type] || '?'}</span>
                ))}
              </span>
              <span className="history-time">{formatTime(item.timestamp)}</span>
            </div>
            <div className="history-text">{item.input}</div>
            <div className="history-models">
              {item.model_names?.join(' / ')}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
