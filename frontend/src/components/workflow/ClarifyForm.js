import React, { useMemo, useState } from 'react';

/* ── Helpers ──────────────────────────────────────────────── */
function getFieldType(field) {
  return field?.type || field?.field_type || 'short_text';
}

function buildInitial(schema, inferredAnswers = {}) {
  const values = {};
  (schema?.fields || []).forEach((f) => {
    const fieldType = getFieldType(f);
    // Pre-fill with inferred value if available
    if (inferredAnswers[f.key] !== undefined) {
      values[f.key] = inferredAnswers[f.key];
    } else if (f.default !== undefined) {
      values[f.key] = f.default;
    } else if (f.default_value !== undefined) {
      values[f.key] = f.default_value;
    } else if (fieldType === 'multi_choice') {
      values[f.key] = [];
    } else if (fieldType === 'boolean') {
      values[f.key] = false;
    } else {
      values[f.key] = '';
    }
  });
  return values;
}

function isFilled(field, val) {
  const fieldType = getFieldType(field);
  if (!field.required) return true;
  if (fieldType === 'multi_choice') return Array.isArray(val) && val.length > 0;
  if (fieldType === 'boolean') return typeof val === 'boolean';
  if (fieldType === 'number') return val !== '' && val !== null && !Number.isNaN(Number(val));
  return String(val || '').trim().length > 0;
}

function conditionMatch(condition, values) {
  if (!condition || typeof condition !== 'object') return false;
  return Object.entries(condition).every(([k, expected]) => values[k] === expected);
}

function isVisible(field, values) {
  if (field.show_when) {
    return conditionMatch(field.show_when, values);
  }
  if (field.depends_on) {
    return values[field.depends_on] === field.depends_on_value;
  }
  return true;
}

function isRequired(field, values) {
  if (field.required) return true;
  if (field.required_when) return conditionMatch(field.required_when, values);
  return false;
}

/* ── Field Renderer ───────────────────────────────────────── */
function FieldRenderer({ field, value, onChange, onMultiToggle }) {
  switch (getFieldType(field)) {
    case 'single_choice':
      return (
        <div className="chip-group">
          {(field.options || []).map((opt) => (
            <button
              type="button"
              key={opt.value}
              className={`chip-btn ${value === opt.value ? 'active' : ''}`}
              onClick={() => onChange(field.key, opt.value)}
            >
              {opt.icon && <span>{opt.icon} </span>}
              {opt.label}
            </button>
          ))}
        </div>
      );

    case 'multi_choice':
      return (
        <div className="chip-group">
          {(field.options || []).map((opt) => {
            const active = (value || []).includes(opt.value);
            return (
              <button
                type="button"
                key={opt.value}
                className={`chip-btn ${active ? 'active' : ''}`}
                onClick={() => onMultiToggle(field.key, opt.value)}
              >
                {opt.icon && <span>{opt.icon} </span>}
                {opt.label}
              </button>
            );
          })}
        </div>
      );

    case 'short_text':
      return (
        <input
          className="form-input"
          type="text"
          placeholder={field.placeholder || ''}
          value={value || ''}
          onChange={(e) => onChange(field.key, e.target.value)}
        />
      );

    case 'multiline_text':
      return (
        <textarea
          className="form-textarea"
          rows={4}
          placeholder={field.placeholder || ''}
          value={value || ''}
          onChange={(e) => onChange(field.key, e.target.value)}
        />
      );

    case 'number':
      return (
        <input
          className="form-input"
          type="number"
          min={field.min}
          max={field.max}
          style={{ maxWidth: 160 }}
          value={value}
          onChange={(e) => onChange(field.key, e.target.value)}
        />
      );

    case 'boolean':
      return (
        <label className="toggle-row">
          <div
            className={`toggle-switch ${value ? 'on' : ''}`}
            onClick={() => onChange(field.key, !value)}
          />
          <span className="text-sm" style={{ color: 'var(--text-secondary)' }}>
            {value ? (field.true_label || '是') : (field.false_label || '否')}
          </span>
        </label>
      );

    default:
      return null;
  }
}

/* ── ClarifyForm ──────────────────────────────────────────── */
export default function ClarifyForm({
  schema,
  missingSlots = [],
  missingSlotHints = {},
  inferredAnswers = {},
  onSubmit,
  loading,
}) {
  const [values, setValues] = useState(() => buildInitial(schema, inferredAnswers));

  const update = (key, val) => setValues((prev) => ({ ...prev, [key]: val }));
  const toggleMulti = (key, val) => {
    setValues((prev) => {
      const curr = Array.isArray(prev[key]) ? prev[key] : [];
      const next = curr.includes(val)
        ? curr.filter((x) => x !== val)
        : [...curr, val];
      return { ...prev, [key]: next };
    });
  };

  const visibleFields = useMemo(
    () => (schema?.fields || []).filter((f) => isVisible(f, values)),
    [schema, values]
  );

  const canSubmit = useMemo(() => {
    return visibleFields.every((f) => {
      const req = isRequired(f, values);
      if (!req) return true;
      return isFilled({ ...f, required: true }, values[f.key]);
    });
  }, [visibleFields, values]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!canSubmit || loading) return;
    onSubmit(values);
  };

  /* missing slots banner */
  const slotLabelMap = useMemo(() => {
    const map = {};
    (schema?.fields || []).forEach((f) => {
      if (f?.key) map[f.key] = f.label || f.key;
    });
    return map;
  }, [schema]);

  const missingLabels = missingSlots
    .map((k) => slotLabelMap[k] || k)
    .filter(Boolean);

  /* inferred fields (pre-filled) */
  const inferredKeys = Object.keys(inferredAnswers).filter(
    (k) => inferredAnswers[k] !== undefined && inferredAnswers[k] !== ''
  );

  return (
    <form onSubmit={handleSubmit}>
      {/* Missing slots banner */}
      {missingLabels.length > 0 && (
        <div style={{ marginBottom: 16 }}>
          <p className="text-sm" style={{ color: 'var(--warning)', fontWeight: 600, marginBottom: 8 }}>
            ⚠ 以下信息是执行任务的必要条件，请确认填写：
          </p>
          <div className="missing-slots">
            {missingLabels.map((label) => (
              <span key={label} className="missing-slot-tag">
                <span>!</span> {label}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Inferred fields notice */}
      {inferredKeys.length > 0 && (
        <div style={{
          marginBottom: 16,
          padding: '8px 12px',
          background: 'var(--success-bg)',
          border: '1px solid var(--green-500)',
          borderRadius: 'var(--r-md)',
          fontSize: 12,
          color: 'var(--success)',
        }}>
          ✓ 系统已从你的描述中推断出 {inferredKeys.length} 项信息，已为你预填写。请确认后可直接提交。
        </div>
      )}

      {/* Fields */}
      {visibleFields.map((f) => {
        const req = isRequired(f, values);
        const isInferred = inferredAnswers[f.key] !== undefined;
        return (
          <div className="form-field" key={f.key}>
            <div className="form-label">
              {f.label}
              {req && <span className="required"> *</span>}
              {isInferred && (
                <span style={{
                  marginLeft: 6,
                  fontSize: 11,
                  fontWeight: 500,
                  color: 'var(--success)',
                  background: 'var(--success-bg)',
                  padding: '1px 6px',
                  borderRadius: 'var(--r-full)',
                }}>
                  已推断
                </span>
              )}
            </div>
            {f.help_text && <div className="form-help">{f.help_text}</div>}
            <FieldRenderer
              field={f}
              value={values[f.key]}
              onChange={update}
              onMultiToggle={toggleMulti}
            />
          </div>
        );
      })}

      <div style={{ marginTop: 20, display: 'flex', gap: 10 }}>
        <button
          type="submit"
          className="btn btn-primary"
          disabled={!canSubmit || loading}
        >
          {loading ? '提交中...' : '确认并继续 →'}
        </button>
        <span className="text-xs text-muted" style={{ alignSelf: 'center' }}>
          所有填写内容将完整保存并用于生成任务规格
        </span>
      </div>
    </form>
  );
}
