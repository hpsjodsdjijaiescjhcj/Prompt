import React, { useState } from 'react';

export default function ModelCard({ recommendation, index }) {
  const [copied, setCopied] = useState(false);
  const [expanded, setExpanded] = useState(index === 0);

  const { model, reason, prompt } = recommendation;

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(prompt);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = prompt;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const rankLabels = ['最佳推荐', '次选推荐', '备选推荐'];
  const rankColors = [model.color || '#667eea', '#94a3b8', '#cbd5e1'];

  // 能力维度名称
  const scoreLabels = {
    writing: '写作', coding: '编程', academic: '学术',
    business: '商业', search: '搜索', reasoning: '推理',
  };

  return (
    <div
      className={`model-card ${index === 0 ? 'top-pick' : ''}`}
      style={{ '--card-accent': model.color || '#667eea' }}
    >
      {/* Header */}
      <div className="card-header" onClick={() => setExpanded(!expanded)}>
        <div className="card-title">
          <span className="model-icon">{model.icon}</span>
          <div>
            <h3>
              {model.name}
              <span className="provider">by {model.provider}</span>
            </h3>
            <span
              className="rank-badge"
              style={{ background: rankColors[index] || '#cbd5e1' }}
            >
              {rankLabels[index] || '推荐'}
            </span>
          </div>
        </div>
        <div className="match-badge" style={{ color: model.color }}>
          <span className="match-number">{model.match_pct}%</span>
          <span className="match-label">匹配度</span>
        </div>
      </div>

      {/* Reason */}
      <p className="reason">{reason}</p>

      {/* Capability bars */}
      <div className="capability-bars">
        {Object.entries(model.scores || {}).map(([key, val]) => (
          <div key={key} className="cap-row">
            <span className="cap-label">{scoreLabels[key] || key}</span>
            <div className="cap-bar-bg">
              <div
                className="cap-bar-fill"
                style={{
                  width: `${val * 10}%`,
                  background: val >= 9 ? model.color : '#94a3b8',
                }}
              />
            </div>
            <span className="cap-val">{val}</span>
          </div>
        ))}
      </div>

      {/* Tags */}
      <div className="tag-rows">
        <div className="strengths">
          {model.strengths?.slice(0, 4).map((s, i) => (
            <span key={i} className="strength-tag">{s}</span>
          ))}
        </div>
        {model.weaknesses?.length > 0 && (
          <div className="weaknesses">
            {model.weaknesses.slice(0, 2).map((w, i) => (
              <span key={i} className="weakness-tag">{w}</span>
            ))}
          </div>
        )}
      </div>

      {/* Meta info */}
      <div className="model-meta">
        <span title="相对成本">{'$'.repeat(Math.ceil(model.cost / 3))}</span>
        <span title="响应速度">{'⚡'.repeat(Math.ceil(model.speed / 4))}</span>
        <span title="上下文窗口">{(model.context_window / 1000).toFixed(0)}K ctx</span>
      </div>

      {/* Prompt section */}
      {expanded && (
        <div className="prompt-section">
          <div className="prompt-header">
            <span>专属提示词 — {model.name}</span>
            <button
              className={`copy-btn ${copied ? 'copied' : ''}`}
              onClick={handleCopy}
            >
              {copied ? '已复制 ✓' : '一键复制'}
            </button>
          </div>
          {model.prompt_tips && (
            <div className="prompt-tips">
              <strong>使用技巧：</strong>{model.prompt_tips}
            </div>
          )}
          <pre className="prompt-text">{prompt}</pre>
        </div>
      )}

      {!expanded && (
        <button className="expand-btn" onClick={() => setExpanded(true)}>
          展开查看专属提示词 ▾
        </button>
      )}
    </div>
  );
}
