import React, { useState } from 'react';

export default function CompareView({ recommendations }) {
  const [copiedAll, setCopiedAll] = useState(false);

  if (!recommendations || recommendations.length < 2) return null;

  const handleCopyAll = async () => {
    const allText = recommendations
      .map((r) => `=== ${r.model.name} 专属提示词 ===\n\n${r.prompt}`)
      .join('\n\n\n');

    try {
      await navigator.clipboard.writeText(allText);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = allText;
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      document.body.removeChild(ta);
    }
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  const scoreLabels = {
    writing: '写作', coding: '编程', academic: '学术',
    business: '商业', search: '搜索', reasoning: '推理',
  };

  return (
    <div className="compare-view">
      <div className="compare-header">
        <h3>模型对比</h3>
        <button
          className={`copy-btn ${copiedAll ? 'copied' : ''}`}
          onClick={handleCopyAll}
        >
          {copiedAll ? '全部已复制 ✓' : '复制全部提示词'}
        </button>
      </div>

      <div className="compare-grid">
        {recommendations.map((rec, i) => (
          <div
            key={i}
            className="compare-col"
            style={{ '--col-accent': rec.model.color }}
          >
            <div className="compare-model-header">
              <span className="model-icon">{rec.model.icon}</span>
              <span className="model-name">{rec.model.name}</span>
              <span className="match-pct" style={{ color: rec.model.color }}>
                {rec.model.match_pct}%
              </span>
            </div>

            {/* Ability comparison bars */}
            <div className="compare-bars">
              {Object.entries(rec.model.scores || {}).map(([key, val]) => (
                <div key={key} className="compare-bar-row">
                  <span className="compare-bar-label">
                    {scoreLabels[key] || key}
                  </span>
                  <div className="compare-bar-bg">
                    <div
                      className="compare-bar-fill"
                      style={{
                        width: `${val * 10}%`,
                        background: val >= 9 ? rec.model.color : '#d1d5db',
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>

            {/* Best for */}
            <div className="compare-best-for">
              {rec.model.best_for?.slice(0, 3).map((b, j) => (
                <span key={j} className="best-for-tag">{b}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
