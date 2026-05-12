import React, { useState, useRef, useEffect, useCallback } from 'react';
import Sidebar from './components/layout/Sidebar';
import ContextPanel from './components/layout/ContextPanel';
import PipelineBar from './components/workflow/PipelineBar';
import TaskLabelPicker from './components/workflow/TaskLabelPicker';
import WorkflowContainer from './components/workflow/WorkflowContainer.jsx';
import APIClient from './api_v2';
import { fetchHistory, deleteHistory, checkHealth } from './api';
import { TASK_LABELS, EXAMPLES } from './constants';
import { useI18n } from './i18n/useI18n';
import './App.css';

/* ── Root App ─────────────────────────────────────────────── */
export default function App() {
  const { language, switchLanguage, t, isZh } = useI18n();

  /* layout */
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [darkMode, setDarkMode] = useState(
    () => localStorage.getItem('tf_dark') === 'true'
  );

  /* session / messages */
  const [history, setHistory] = useState([]);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  /* active workflow */
  const [activeWorkflow, setActiveWorkflow] = useState(null);

  /* input */
  const [input, setInput] = useState('');
  const [selectedLabels, setSelectedLabels] = useState([]);

  /* system */
  const [systemStatus, setSystemStatus] = useState(null);

  const chatEndRef = useRef(null);
  const textareaRef = useRef(null);

  /* ── Theme ─────────────────────────────────────────────── */
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', darkMode ? 'dark' : 'light');
    localStorage.setItem('tf_dark', darkMode);
  }, [darkMode]);

  /* ── Scroll ─────────────────────────────────────────────── */
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  /* ── Health ─────────────────────────────────────────────── */
  useEffect(() => {
    checkHealth().then(setSystemStatus).catch(() => {});
  }, []);

  /* ── History ────────────────────────────────────────────── */
  const loadHistory = useCallback(async () => {
    try {
      const data = await fetchHistory();
      setHistory(data.history || []);
    } catch {}
  }, []);

  useEffect(() => { loadHistory(); }, [loadHistory]);

  /* ── Submit ─────────────────────────────────────────────── */
  const handleSubmit = useCallback(async (text) => {
    const trimmed = (text || input).trim();
    if (!trimmed || loading) return;

    setInput('');
    setMessages((prev) => [...prev, { type: 'user', text: trimmed }]);
    setLoading(true);
    setActiveWorkflow(null);

    // Analyzing notice
    setMessages((prev) => [
      ...prev,
      { type: 'loading', text: '正在理解任务意图...' },
    ]);

    try {
      // Create session with v2 API, passing selected labels
      const session = await APIClient.createSession(trimmed, selectedLabels);

      // Immediately trigger clarification to get schema or skip
      const clarification = await APIClient.processClarification(session.session_id);

      if (clarification?.should_skip) {
        await APIClient.alignSpecification(session.session_id);
      }

      // Get full session data with clarification/specification attached
      const wf = await APIClient.getSession(session.session_id);
      const enrichedWorkflow = clarification?.schema
        ? { ...wf, clarification_schema: clarification.schema }
        : wf;

      // Remove loading message, add workflow
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.type !== 'loading');
        return [...filtered, { type: 'workflow', wf: enrichedWorkflow, sessionId: enrichedWorkflow.session_id }];
      });

      setActiveWorkflow(enrichedWorkflow);
      loadHistory();
    } catch (err) {
      setMessages((prev) => {
        const filtered = prev.filter((m) => m.type !== 'loading');
        return [...filtered, { type: 'error', text: err.message || '请求失败，请重试' }];
      });
    } finally {
      setLoading(false);
    }
  }, [input, loading, selectedLabels, loadHistory]);

  /* ── Keyboard ───────────────────────────────────────────── */
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

   /* ── Toggle label ───────────────────────────────────────── */
   const toggleLabel = (id) => {
     setSelectedLabels((prev) => {
       const label = TASK_LABELS.find((l) => l.id === id);
       if (!label) return prev;
       
       const isSelected = prev.some((l) => l.id === id);
       if (isSelected) {
         return prev.filter((l) => l.id !== id);
       } else {
         return [...prev, label];
       }
     });
   };

   /* ── New task ───────────────────────────────────────────── */
    const handleNewTask = () => {
      setMessages([]);
      setActiveWorkflow(null);
      setSelectedLabels([]);
      setInput('');
      textareaRef.current?.focus();
    };

    /* ── Load history item (with full session fetch) ──────────── */
  const handleLoadHistoryItem = useCallback(async (item) => {
    try {
      let fullSession = item?.session_id
        ? await APIClient.getSession(item.session_id)
        : item;

      if (
        item?.session_id &&
        fullSession?.state === 'clarifying' &&
        !fullSession?.clarification_schema
      ) {
        const clarification = await APIClient.processClarification(item.session_id);
        if (clarification?.schema) {
          fullSession = { ...fullSession, clarification_schema: clarification.schema };
        }
      }

      setMessages([
        { type: 'user', text: item.input || item.text },
        { type: 'workflow', wf: fullSession, sessionId: fullSession.session_id },
      ]);
      setActiveWorkflow(fullSession);
      setInput('');
    } catch (err) {
      setMessages([
        { type: 'user', text: item.input || item.text },
        { type: 'workflow', wf: item, sessionId: item.session_id },
      ]);
      setActiveWorkflow(item);
      setInput('');
    }
  }, []);

  /* ── Workflow update callback (from WorkflowContainer) ──── */
  const handleWorkflowUpdate = useCallback((updated) => {
    setActiveWorkflow(updated);
  }, []);

  const handleDeleteHistoryItem = useCallback(async (item) => {
    const historyId = item?.id;
    if (!historyId) return;

    try {
      await deleteHistory(historyId);
      setHistory((prev) => prev.filter((entry) => entry.id !== historyId));
      if ((activeWorkflow?.session_id && activeWorkflow.session_id === item.session_id) || (!item.session_id && (item.input || item.text) === messages.find((m) => m.type === 'user')?.text)) {
        setActiveWorkflow(null);
        setMessages([]);
      }
    } catch (err) {
      setMessages((prev) => ([
        ...prev,
        { type: 'error', text: err.message || '删除失败，请重试' },
      ]));
    }
  }, [activeWorkflow, messages]);

  /* ── Auto-resize textarea ───────────────────────────────── */
  const handleInputChange = (e) => {
    setInput(e.target.value);
    const el = e.target;
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  };

  const isEmpty = messages.length === 0;
  const hasWorkflow = !!activeWorkflow && activeWorkflow.state !== 'other';

  return (
    <div className="app">
      {/* ── Header ─────────────────────────────────────────── */}
      <header className="app-header">
        <div className="header-brand">
          <button
            className="icon-btn"
            onClick={() => setSidebarOpen((o) => !o)}
            title={sidebarOpen ? '收起侧栏' : '展开侧栏'}
          >
            ☰
          </button>
          <div className="header-logo">⚡</div>
          <span className="header-title">{t('appTitle')}</span>
          <span className="header-subtitle">{t('appSubtitle')}</span>
        </div>

        <div className="header-actions">
          {systemStatus && (
            <div className="header-status">
              <span className={`status-dot ${systemStatus.ollama_available ? 'online' : 'offline'}`} />
              {systemStatus.ollama_available ? 'LLM 智能模式' : '基础模式'}
            </div>
          )}
          <button
            className="icon-btn"
            onClick={() => switchLanguage(isZh ? 'en' : 'zh')}
            title={t('languageSwitch')}
          >
            {language === 'zh' ? 'EN' : '中'}
          </button>
          <button
            className="icon-btn"
            onClick={() => setDarkMode((d) => !d)}
            title={darkMode ? '浅色模式' : '深色模式'}
          >
            {darkMode ? '☀' : '☾'}
          </button>
        </div>
      </header>

      {/* ── Body ───────────────────────────────────────────── */}
      <div className="app-layout">
        {/* Left: History Sidebar */}
        <Sidebar
          history={history}
          collapsed={!sidebarOpen}
          activeWorkflow={activeWorkflow}
          onNewTask={handleNewTask}
          onSelect={handleLoadHistoryItem}
          onDelete={handleDeleteHistoryItem}
        />

        {/* Center: Chat */}
        <div className="main-area">
          {/* Pipeline bar (only during active workflow) */}
          {hasWorkflow && (
            <PipelineBar state={activeWorkflow?.state} taskType={activeWorkflow?.task_type} />
          )}

          {/* Scrollable chat */}
          <div className="chat-scroll">
            {isEmpty && (
              <WelcomeScreen
                selectedLabels={selectedLabels}
                onToggleLabel={toggleLabel}
                onExample={(t) => handleSubmit(t)}
                loading={loading}
              />
            )}

            {messages.map((msg, i) => (
              <div key={i} className="chat-message fade-in">
                {msg.type === 'user' && (
                  <div className="user-msg">
                    <div className="user-bubble">{msg.text}</div>
                  </div>
                )}

                {msg.type === 'loading' && (
                  <div className="system-notice loading">
                    <div className="loading-dots"><span /><span /><span /></div>
                    {msg.text}
                  </div>
                )}

                {msg.type === 'error' && (
                  <div className="error-notice">
                    <span>⚠️</span>
                    <span>{msg.text}</span>
                  </div>
                )}

                {msg.type === 'workflow' && (
                  <div className="workflow-wrap">
                    <WorkflowContainer
                      key={msg.sessionId}
                      initialData={msg.wf}
                      onWorkflowUpdate={handleWorkflowUpdate}
                    />
                  </div>
                )}

                {msg.type === 'other-start' && (
                  <OtherTaskResult wf={msg.wf} />
                )}
              </div>
            ))}

            <div ref={chatEndRef} />
          </div>

          {/* Input Area */}
          <div className="input-area">
            {messages.length > 0 && !isEmpty && (
              <div className="input-labels-row">
                <TaskLabelPicker
                  compact
                  selected={selectedLabels}
                  onToggle={toggleLabel}
                />
              </div>
            )}
            <div className="input-wrapper">
              <textarea
                ref={textareaRef}
                className="input-textarea"
                value={input}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={t('inputPlaceholder')}
                rows={1}
                disabled={loading}
              />
              <button
                className="input-send-btn"
                onClick={() => handleSubmit()}
                disabled={!input.trim() || loading}
                title="发送 (Enter)"
              >
                ↑
              </button>
            </div>
          </div>
        </div>

        {/* Right: Context Panel */}
        {!hasWorkflow && <ContextPanel workflow={activeWorkflow} />}
      </div>
    </div>
  );
}

/* ── Welcome Screen ──────────────────────────────────────── */
function WelcomeScreen({ selectedLabels, onToggleLabel, onExample, loading }) {
  return (
    <div className="welcome-screen">
      <div className="welcome-icon">⚡</div>
      <h1 className="welcome-title">AI 任务编排系统</h1>
      <p className="welcome-subtitle">
        把你的需求转化为可执行、可验证的任务流程。<br />
        选择任务类型，或直接描述你想完成的事。
      </p>

      <TaskLabelPicker
        selected={selectedLabels}
        onToggle={onToggleLabel}
      />

      <div className="examples-section">
        <p className="examples-label">快速开始 — 点击试试：</p>
        <div className="example-chips">
          {EXAMPLES.map((ex) => {
            const label = TASK_LABELS.find((l) => l.id === ex.type);
            return (
              <button
                key={ex.text}
                className="example-chip"
                onClick={() => onExample(ex.text)}
                disabled={loading}
              >
                <span>{label?.icon}</span>
                {ex.text}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}

/* ── Other Task (no orchestration) ──────────────────────── */
function OtherTaskResult({ wf }) {
  return (
    <div className="card fade-in" style={{ maxWidth: 680 }}>
      <div className="card-header">
        <div className="card-title">
          <span className="card-title-icon">📝</span>
          任务分析结果
        </div>
        <span className={`type-badge ${wf.task_type || 'generic'}`}>
          {wf.task_type || 'generic'}
        </span>
      </div>
      <div className="card-body">
        <p className="text-muted text-sm" style={{ marginBottom: 12 }}>
          该任务已完成快速分析，可直接使用以下规格作为提示词。
        </p>
        {wf.spec_draft && (
          <div className="spec-snapshot">
            {wf.spec_draft.objective && (
              <div className="spec-snapshot-row">
                <span className="spec-snapshot-key">目标</span>
                <span className="spec-snapshot-val">{wf.spec_draft.objective}</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
