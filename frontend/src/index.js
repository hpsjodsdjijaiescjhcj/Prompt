import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { LanguageProvider } from './contexts/LanguageContext';

class AppErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('App render crashed:', error, errorInfo);
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 24, fontFamily: 'Inter, PingFang SC, sans-serif', color: '#111827' }}>
          <h1 style={{ fontSize: 20, marginBottom: 12 }}>前端运行时错误</h1>
          <p style={{ marginBottom: 12 }}>React 已捕获到页面挂载异常，白屏已被替换为错误信息。</p>
          <pre style={{ whiteSpace: 'pre-wrap', background: '#f3f4f6', padding: 16, borderRadius: 8 }}>
            {String(this.state.error?.stack || this.state.error?.message || this.state.error)}
          </pre>
        </div>
      );
    }

    return this.props.children;
  }
}

const container = document.getElementById('root');
const root = ReactDOM.createRoot(container);

try {
  root.render(
    <LanguageProvider>
      <AppErrorBoundary>
        <App />
      </AppErrorBoundary>
    </LanguageProvider>
  );
} catch (error) {
  console.error('Root render failed:', error);
  if (container) {
    container.innerHTML = `
      <div style="padding:24px;font-family:Inter,PingFang SC,sans-serif;color:#111827;">
        <h1 style="font-size:20px;margin-bottom:12px;">前端初始化失败</h1>
        <pre style="white-space:pre-wrap;background:#f3f4f6;padding:16px;border-radius:8px;">${String(error?.stack || error?.message || error)}</pre>
      </div>
    `;
  }
}
