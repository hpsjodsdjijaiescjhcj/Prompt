import React, { useMemo } from 'react';
import { TASK_LABELS } from '../../constants';
import { useI18n } from '../../i18n/useI18n';

/* ── Task type display map ─────────────────────────────────── */
const TYPE_LABEL_MAP = Object.fromEntries(
  TASK_LABELS.map((l) => [l.id, l])
);

function getTypeLabel(taskType) {
  return TYPE_LABEL_MAP[taskType] || { icon: '•', label: taskType || 'generic' };
}

function formatTime(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  const now = new Date();
  const diff = now - d;
  if (diff < 60_000) return 'just now';
  if (diff < 3_600_000) return `${Math.floor(diff / 60_000)}m ago`;
  if (diff < 86_400_000) return `${Math.floor(diff / 3_600_000)}h ago`;
  return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export default function Sidebar({ history, collapsed, activeWorkflow, onNewTask, onSelect, onDelete }) {
  const { t, language, isZh } = useI18n();

  const handleDelete = (e, item) => {
    e.stopPropagation();
    if (onDelete && window.confirm(isZh ? '确定要删除这条记录吗？' : 'Delete this record?')) {
      onDelete(item);
    }
  };

  const dedupedHistory = useMemo(() => {
    const seen = new Set();
    return (history || []).filter((item) => {
      const stableKey = item.session_id || `${item.task_type}:${item.input || item.text || ''}:${item.created_at || item.timestamp || ''}`;
      if (seen.has(stableKey)) return false;
      seen.add(stableKey);
      return true;
    });
  }, [history]);

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <span className="sidebar-label">{t('historyTitle')}</span>
      </div>

      <button className="new-task-btn" onClick={onNewTask}>
        <span>＋</span> {t('newTask')}
      </button>

      <div className="sidebar-section-title">{t('recentConversations')}</div>

      <div className="sidebar-sessions">
        {dedupedHistory.length === 0 && (
          <div className="sidebar-empty">{isZh ? '暂无历史记录' : 'No history yet'}</div>
        )}

        {dedupedHistory.map((item, i) => {
          const typeInfo = getTypeLabel(item.task_type);
          const isActive = activeWorkflow?.session_id === item.session_id;
          const previewText = item.input || item.text || '(无内容)';

          return (
            <div
              key={item.session_id || item.id || i}
              className={`session-item ${isActive ? 'active' : ''}`}
              onClick={() => onSelect(item)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  onSelect(item);
                }
              }}
            >
              <div className="session-task-type">
                <span className={`type-badge ${item.task_type || 'generic'}`}>
                  {typeInfo.icon} {typeInfo.label}
                </span>
                {item.id && (
                  <button
                    type="button"
                    className="session-delete-btn"
                    onClick={(e) => handleDelete(e, item)}
                    title={isZh ? '删除记录' : 'Delete record'}
                    aria-label={isZh ? '删除记录' : 'Delete record'}
                  >
                    ×
                  </button>
                )}
              </div>
              <div className="session-text">{previewText}</div>
              <div className="session-meta">{isZh ? new Date(item.created_at || item.timestamp || Date.now()).toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' }) : formatTime(item.created_at || item.timestamp)}</div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}
