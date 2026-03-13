import React, { useMemo, useState } from 'react';

function toLines(val) {
  return Array.isArray(val) ? val.join('\n') : '';
}

function fromLines(val) {
  return String(val || '')
    .split('\n')
    .map((x) => x.trim())
    .filter(Boolean);
}

export default function SpecEditor({ spec, onSubmit, loading }) {
  const [draft, setDraft] = useState(() => JSON.parse(JSON.stringify(spec || {})));

  const lineValues = useMemo(
    () => ({
      mustInclude: toLines(draft.must_include),
      mustAvoid: toLines(draft.must_avoid),
      acceptance: toLines(draft.acceptance_criteria),
    }),
    [draft]
  );

  const update = (patch) => setDraft((prev) => ({ ...prev, ...patch }));

  const updateWordLimit = (next) => {
    setDraft((prev) => ({
      ...prev,
      constraints: {
        ...(prev.constraints || {}),
        word_limit: Number(next || 200),
      },
    }));
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(draft);
  };

  return (
    <form className="wf-card" onSubmit={handleSubmit}>
      <h3>Spec Confirm/Edit</h3>
      <p className="wf-desc">Review and edit core fields before prompt generation/execution.</p>

      <div className="wf-field">
        <label>Objective *</label>
        <textarea
          className="wf-textarea"
          rows={4}
          value={draft.objective || ''}
          onChange={(e) => update({ objective: e.target.value })}
        />
      </div>

      <div className="wf-grid-2">
        <div className="wf-field">
          <label>Tone</label>
          <select
            className="wf-input"
            value={draft.tone || 'professional'}
            onChange={(e) => update({ tone: e.target.value })}
          >
            <option value="professional">professional</option>
            <option value="firm">firm</option>
            <option value="friendly">friendly</option>
          </select>
        </div>
        <div className="wf-field">
          <label>Word Limit</label>
          <input
            className="wf-input"
            type="number"
            min={50}
            max={1000}
            value={draft.constraints?.word_limit || 200}
            onChange={(e) => updateWordLimit(e.target.value)}
          />
        </div>
      </div>

      <div className="wf-field">
        <label>Must Include (one per line)</label>
        <textarea
          className="wf-textarea"
          rows={3}
          value={lineValues.mustInclude}
          onChange={(e) => update({ must_include: fromLines(e.target.value) })}
        />
      </div>

      <div className="wf-field">
        <label>Must Avoid (one per line)</label>
        <textarea
          className="wf-textarea"
          rows={3}
          value={lineValues.mustAvoid}
          onChange={(e) => update({ must_avoid: fromLines(e.target.value) })}
        />
      </div>

      <div className="wf-field">
        <label>Acceptance Criteria (one per line)</label>
        <textarea
          className="wf-textarea"
          rows={4}
          value={lineValues.acceptance}
          onChange={(e) => update({ acceptance_criteria: fromLines(e.target.value) })}
        />
      </div>

      <div className="wf-summary">
        <strong>Audience:</strong>{' '}
        {draft.audience ? `${draft.audience.recipient_type || ''} / ${draft.audience.relationship || ''}` : 'N/A'}
        <br />
        <strong>Language:</strong> {draft.language || 'N/A'}
        <br />
        <strong>Output Sections:</strong>{' '}
        {(draft.output_format?.sections || []).join(', ') || 'N/A'}
      </div>

      <div className="wf-actions">
        <button type="submit" className="action-btn" disabled={loading || !draft.objective}>
          {loading ? 'Saving...' : 'Confirm Spec'}
        </button>
      </div>
    </form>
  );
}
