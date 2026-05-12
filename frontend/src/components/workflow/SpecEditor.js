import React, { useState, useMemo } from 'react';

const TONES = [
  { value: 'professional', label: '专业正式' },
  { value: 'friendly',     label: '亲切友好' },
  { value: 'firm',         label: '强硬坚定' },
  { value: 'concise',      label: '简洁直接' },
  { value: 'academic',     label: '学术严谨' },
  { value: 'creative',     label: '创意活泼' },
];

const LANGUAGES = [
  { value: 'zh', label: '中文' },
  { value: 'en', label: 'English' },
  { value: 'zh-en', label: '中英混合' },
];

function toLines(val) {
  return Array.isArray(val) ? val.join('\n') : (val || '');
}

function fromLines(val) {
  return String(val || '').split('\n').map((x) => x.trim()).filter(Boolean);
}

export default function SpecEditor({ spec, taskType, onSubmit, loading }) {
  const [draft, setDraft] = useState(() => JSON.parse(JSON.stringify(spec || {})));

  const update = (patch) => setDraft((prev) => ({ ...prev, ...patch }));

  const setConstraint = (key, val) =>
    setDraft((prev) => ({
      ...prev,
      constraints: { ...(prev.constraints || {}), [key]: val },
    }));

  const setContext = (key, val) =>
    setDraft((prev) => ({
      ...prev,
      context: { ...(prev.context || {}), [key]: val },
    }));

  const lineVals = useMemo(() => ({
    mustInclude:  toLines(draft.must_include),
    mustAvoid:    toLines(draft.must_avoid),
    acceptance:   toLines(draft.acceptance_criteria),
  }), [draft]);

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(draft);
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* ── Core Objective ─────────────────────────────── */}
      <div className="spec-section">
        <div className="spec-section-title">任务目标</div>
        <div className="form-field">
          <div className="form-label">
            核心目标 <span className="required">*</span>
          </div>
          <div className="form-help">
            系统已根据你的输入生成此目标描述，请确认或修改至准确无歧义。
          </div>
          <textarea
            className="form-textarea"
            rows={3}
            value={draft.objective || ''}
            onChange={(e) => update({ objective: e.target.value })}
            placeholder="描述本次任务要达成的具体目标..."
          />
        </div>

        {draft.context?.background !== undefined && (
          <div className="form-field">
            <div className="form-label">背景信息</div>
            <textarea
              className="form-textarea"
              rows={2}
              value={draft.context?.background || ''}
              onChange={(e) => setContext('background', e.target.value)}
              placeholder="任务相关的背景、前因..."
            />
          </div>
        )}
      </div>

      {/* ── Style & Format ─────────────────────────────── */}
      <div className="spec-section">
        <div className="spec-section-title">风格与格式</div>
        <div className="form-grid-2">
          <div className="form-field">
            <div className="form-label">语气风格</div>
            <div className="chip-group">
              {TONES.map((t) => (
                <button
                  type="button"
                  key={t.value}
                  className={`chip-btn ${draft.tone === t.value ? 'active' : ''}`}
                  onClick={() => update({ tone: t.value })}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <div className="form-field">
            <div className="form-label">输出语言</div>
            <div className="chip-group">
              {LANGUAGES.map((l) => (
                <button
                  type="button"
                  key={l.value}
                  className={`chip-btn ${draft.language === l.value ? 'active' : ''}`}
                  onClick={() => update({ language: l.value })}
                >
                  {l.label}
                </button>
              ))}
            </div>
          </div>

          <div className="form-field">
            <div className="form-label">字数上限</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input
                className="form-input"
                type="number"
                min={50}
                max={5000}
                step={50}
                style={{ maxWidth: 120 }}
                value={draft.constraints?.word_limit || 300}
                onChange={(e) => setConstraint('word_limit', Number(e.target.value))}
              />
              <span className="text-sm text-muted">字</span>
            </div>
          </div>

          {draft.audience?.recipient_type !== undefined && (
            <div className="form-field">
              <div className="form-label">目标受众</div>
              <input
                className="form-input"
                type="text"
                value={draft.audience?.recipient_type || ''}
                onChange={(e) =>
                  setDraft((prev) => ({
                    ...prev,
                    audience: { ...(prev.audience || {}), recipient_type: e.target.value },
                  }))
                }
                placeholder="例：客户、领导、技术团队..."
              />
            </div>
          )}
        </div>
      </div>

      {/* ── Constraints ───────────────────────────────── */}
      <div className="spec-section">
        <div className="spec-section-title">内容约束</div>
        <div className="form-grid-2">
          <div className="form-field">
            <div className="form-label">必须包含</div>
            <div className="form-help">每行一项</div>
            <textarea
              className="form-textarea"
              rows={3}
              value={lineVals.mustInclude}
              onChange={(e) => update({ must_include: fromLines(e.target.value) })}
              placeholder="关键词、要点、必须提到的内容..."
            />
          </div>

          <div className="form-field">
            <div className="form-label">必须避免</div>
            <div className="form-help">每行一项</div>
            <textarea
              className="form-textarea"
              rows={3}
              value={lineVals.mustAvoid}
              onChange={(e) => update({ must_avoid: fromLines(e.target.value) })}
              placeholder="不能出现的词汇、话题、表达方式..."
            />
          </div>
        </div>
      </div>

      {/* ── Acceptance Criteria ───────────────────────── */}
      <div className="spec-section">
        <div className="spec-section-title">验收标准</div>
        <div className="form-field">
          <div className="form-help">
            这些标准将用于验收阶段自动检查输出质量。每行一条，尽量可量化。
          </div>
          <textarea
            className="form-textarea"
            rows={4}
            value={lineVals.acceptance}
            onChange={(e) => update({ acceptance_criteria: fromLines(e.target.value) })}
            placeholder="例：字数在 300 字以内&#10;包含具体的截止日期&#10;语气符合商务场景..."
          />
        </div>
      </div>

      {/* ── Actions ───────────────────────────────────── */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading || !draft.objective}
        >
          {loading ? '处理中...' : '确认规格，进入执行 →'}
        </button>
        <span className="text-xs text-muted">
          确认后系统将进行执行前门控校验
        </span>
      </div>
    </form>
  );
}
