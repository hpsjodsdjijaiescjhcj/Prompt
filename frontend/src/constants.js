/**
 * Shared constants for the entire app
 * Extracted to avoid circular dependencies
 */

/**
 * TASK_LABELS - Frontend UI labels with semantic mapping to backend domains
 * 
 * Each label maps to:
 * - type: 'domain' (primary classification) or 'characteristic' (secondary)
 * - value: backend enum value (e.g., 'communication', 'technical')
 * - characteristics: optional list of inferred characteristics
 */
export const TASK_LABELS = [
  {
    id: 'email',
    icon: '📧',
    label: '邮件起草',
    desc: '商务邮件、通知、回复、跟进',
    type: 'domain',
    value: 'communication',
    characteristics: ['generative', 'procedural'],
  },
  {
    id: 'code',
    icon: '💻',
    label: '代码工程',
    desc: '编写、调试、重构、代码审查',
    type: 'domain',
    value: 'technical',
    characteristics: ['generative', 'analytical'],
  },
  {
    id: 'content',
    icon: '✍️',
    label: '内容创作',
    desc: '文章、文案、营销内容、创意写作',
    type: 'domain',
    value: 'content_creation',
    characteristics: ['creative', 'generative'],
  },
  {
    id: 'research',
    icon: '🔍',
    label: '调研分析',
    desc: '市场调研、竞品分析、信息检索',
    type: 'domain',
    value: 'analysis',
    characteristics: ['analytical', 'procedural'],
  },
  {
    id: 'analysis',
    icon: '📊',
    label: '数据分析',
    desc: '数据解读、业务洞察、报表分析',
    type: 'domain',
    value: 'analysis',
    characteristics: ['analytical', 'transformative'],
  },
  {
    id: 'document',
    icon: '📄',
    label: '文档处理',
    desc: '总结提炼、内容提取、文档整理',
    type: 'domain',
    value: 'operations',
    characteristics: ['transformative', 'procedural'],
  },
  {
    id: 'planning',
    icon: '🎯',
    label: '规划决策',
    desc: '战略规划、项目计划、决策支持',
    type: 'domain',
    value: 'strategy',
    characteristics: ['analytical', 'procedural'],
  },
];

export const EXAMPLES = [
  { text: '帮我写一封催款邮件给供应商', type: 'email' },
  { text: '用 Python 写一个异步爬虫框架', type: 'code' },
  { text: '给我们新品写一篇小红书种草文案', type: 'content' },
  { text: '分析特斯拉和比亚迪的竞争格局', type: 'research' },
  { text: '解读我们 Q3 用户留存率下降的原因', type: 'analysis' },
  { text: '把这份 30 页的合同整理成摘要', type: 'document' },
];

export const STATE_TO_STAGE = {
  input_received: 'input',
  clarifying:     'clarify',
  spec_ready:     'spec',
  preflight_check: 'preflight',
  preflight_failed: 'preflight',
  preflight_passed: 'execute',
  ready_for_execution: 'execute',
  executing:      'execute',
  executed:       'validate',
  validating:     'validate',
  validation_failed: 'validate',
  completed:      'validate',
  failed:         'validate',
  done:           'validate',
};

export const STAGES = [
  { id: 'input',     icon: '📥', label: '输入接收' },
  { id: 'clarify',   icon: '💬', label: '澄清确认' },
  { id: 'spec',      icon: '📋', label: '规格对齐' },
  { id: 'preflight', icon: '🛡️', label: '执行前预检' },
  { id: 'execute',   icon: '⚡', label: '任务执行' },
  { id: 'validate',  icon: '✅', label: '结果验收' },
];
