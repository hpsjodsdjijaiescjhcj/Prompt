import React, { useMemo, useState } from 'react';

function buildInitialValues(schema) {
  const values = {};
  (schema?.fields || []).forEach((f) => {
    if (f.default !== undefined) {
      values[f.key] = f.default;
    } else if (f.type === 'multi_choice') {
      values[f.key] = [];
    } else if (f.type === 'boolean') {
      values[f.key] = false;
    } else {
      values[f.key] = '';
    }
  });
  return values;
}

function isFilled(field, val) {
  if (!field.required) return true;
  if (field.type === 'multi_choice') return Array.isArray(val) && val.length > 0;
  if (field.type === 'boolean') return typeof val === 'boolean';
  if (field.type === 'number') return val !== '' && val !== null && !Number.isNaN(Number(val));
  return String(val || '').trim().length > 0;
}

function conditionMatch(condition, values) {
  if (!condition || typeof condition !== 'object') return false;
  return Object.entries(condition).every(([k, expected]) => values[k] === expected);
}

function isActive(field, values) {
  if (!field.show_when) return true;
  return conditionMatch(field.show_when, values);
}

function isRequired(field, values) {
  if (field.required) return true;
  if (field.required_when) return conditionMatch(field.required_when, values);
  return false;
}

export default function ClarifyForm({ schema, onSubmit, loading }) {
  const [values, setValues] = useState(() => buildInitialValues(schema));

  const canSubmit = useMemo(() => {
    return (schema?.fields || []).every((f) => {
      if (!isActive(f, values)) return true;
      const requiredNow = isRequired(f, values);
      return isFilled({ ...f, required: requiredNow }, values[f.key]);
    });
  }, [schema, values]);

  const update = (key, val) => {
    setValues((prev) => ({ ...prev, [key]: val }));
  };

  const toggleMulti = (key, val) => {
    setValues((prev) => {
      const curr = Array.isArray(prev[key]) ? prev[key] : [];
      const next = curr.includes(val) ? curr.filter((x) => x !== val) : [...curr, val];
      return { ...prev, [key]: next };
    });
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!canSubmit || loading) return;
    onSubmit(values);
  };

  return (
    <form className="wf-card" onSubmit={handleSubmit}>
      <h3>{schema?.title || 'Clarify'}</h3>
      <p className="wf-desc">{schema?.description}</p>

      {(schema?.fields || []).map((f) => {
        if (!isActive(f, values)) return null;
        const requiredNow = isRequired(f, values);
        return (
        <div className="wf-field" key={f.key}>
          <label>
            {f.label}
            {requiredNow ? ' *' : ''}
          </label>
          {f.help_text && <div className="wf-help">{f.help_text}</div>}

          {f.type === 'single_choice' && (
            <div className="wf-chip-row">
              {(f.options || []).map((opt) => (
                <button
                  type="button"
                  key={opt.value}
                  className={`wf-chip ${values[f.key] === opt.value ? 'active' : ''}`}
                  onClick={() => update(f.key, opt.value)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          )}

          {f.type === 'multi_choice' && (
            <div className="wf-chip-row">
              {(f.options || []).map((opt) => {
                const active = (values[f.key] || []).includes(opt.value);
                return (
                  <button
                    type="button"
                    key={opt.value}
                    className={`wf-chip ${active ? 'active' : ''}`}
                    onClick={() => toggleMulti(f.key, opt.value)}
                  >
                    {opt.label}
                  </button>
                );
              })}
            </div>
          )}

          {f.type === 'short_text' && (
            <input
              className="wf-input"
              type="text"
              placeholder={f.placeholder || ''}
              value={values[f.key] || ''}
              onChange={(e) => update(f.key, e.target.value)}
            />
          )}

          {f.type === 'multiline_text' && (
            <textarea
              className="wf-textarea"
              rows={4}
              placeholder={f.placeholder || ''}
              value={values[f.key] || ''}
              onChange={(e) => update(f.key, e.target.value)}
            />
          )}

          {f.type === 'number' && (
            <input
              className="wf-input"
              type="number"
              min={f.min}
              max={f.max}
              value={values[f.key]}
              onChange={(e) => update(f.key, e.target.value)}
            />
          )}

          {f.type === 'boolean' && (
            <label className="wf-toggle">
              <input
                type="checkbox"
                checked={Boolean(values[f.key])}
                onChange={(e) => update(f.key, e.target.checked)}
              />
              <span>{Boolean(values[f.key]) ? (f.true_label || 'Yes') : (f.false_label || 'No')}</span>
            </label>
          )}
        </div>
      )})}

      <div className="wf-actions">
        <button type="submit" className="action-btn" disabled={!canSubmit || loading}>
          {loading ? 'Processing...' : 'Continue'}
        </button>
      </div>
    </form>
  );
}
