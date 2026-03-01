import React, { useState } from 'react';

export default function InputBox({ onSubmit, loading }) {
  const [text, setText] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (text.trim() && !loading) {
      onSubmit(text.trim());
      setText('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <form className="input-box" onSubmit={handleSubmit}>
      <div className="input-wrapper">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="描述你想让AI帮忙做的事... (Enter发送, Shift+Enter换行)"
          rows={2}
          disabled={loading}
        />
      </div>
      <button type="submit" disabled={!text.trim() || loading}>
        {loading ? (
          <span className="btn-loading">
            <span className="spinner" />
            分析中
          </span>
        ) : (
          <span>发送</span>
        )}
      </button>
    </form>
  );
}
