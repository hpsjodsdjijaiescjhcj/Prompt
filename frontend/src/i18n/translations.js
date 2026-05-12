export const translations = {
  zh: {
    // Header
    appTitle: 'TaskForge',
    appSubtitle: 'AI 任务编排系统',
    languageSwitch: '中英文',
    analysisMode: '分析模式',

    // Sidebar
    historyTitle: '历史记录',
    newTask: '新建任务',
    recentConversations: '最近会话',
    clearHistory: '清空历史',

    // Main workflow
    inputPlaceholder: '一句话，例如：\n不能提及竞品名\n应用中文\n不能编造数据\n不能提及政治',
    outputFormat: '输出方式',
    directOutput: '直接给最终结果',
    stepByStepGuide: '先给方案再给结果',
    taskCategory: '任务大类',
    outputStyle: '你希望的输出形式',
    structuredDiscussion: '结构化讨论',
    stepByStepApproach: '分步骤方案',
    comparativeFormat: '对比格式',
    simpleFormat: '简单',
    supplementInfo: '补充信息（可选）',
    submitAndContinue: '确认并继续 →',
    processingHint: '所有填写内容将完整保存并用于生成任务规格',

    // Pipeline stages
    stageInput: '输入',
    stageClarify: '澄清',
    stageAlign: '对齐',
    stagePreflight: '预检',
    stageExecute: '执行',
    stageValidate: '验收',
    stageReview: '回顾',

    // Clarify stage
    clarifyTitle: '澄清阶段',
    clarifyDescription: '系统识别缺口，最少必要提问',
    targetQuestion: '目标是什么？',
    objectQuestion: '对象是什么？',
    contextQuestion: '上下文是什么？',
    constraintQuestion: '约束条件是什么？',
    acceptanceQuestion: '验收标准是什么？',

    // Spec alignment
    specTitle: '任务规格',
    specDescription: '结构化合同，用户可随时编辑',
    originalSpec: '原始输入',
    refinedSpec: '润色版本',
    specBackground: '背景',
    specObjective: '目标',
    specAction: '动作',
    specConstraints: '约束',
    specStyle: '风格',
    specAcceptance: '验收标准',
    editSpec: '编辑规格',
    saveSpec: '保存规格',

    // Preflight
    preflightTitle: '执行前逻辑门',
    preflightDescription: '检查依赖闭包、输入完备性、出口可达性',
    planGraph: '计划图',
    dependencyCheck: '依赖检查',
    inputCompleteness: '输入完备性',
    outputReachability: '出口可达性',
    acceptanceMapping: '验收映射',
    preflightPass: '预检通过',
    preflightFail: '预检失败',
    fixAndRetry: '修复并重试',

    // Execute
    executeTitle: '执行阶段',
    executeDescription: '异步任务队列，支持查询状态',
    selectModel: '选择 AI 模型',
    recommendedModel: '推荐模型',
    modelGPT4: 'GPT-4 (最强)',
    modelClaude: 'Claude (均衡)',
    modelGrok: 'Grok (快速)',
    modelKimi: 'Kimi (长文本)',
    executing: '执行中...',
    executionComplete: '执行完成',
    retryExecution: '重新执行',

    // Validate
    validateTitle: '验收阶段',
    validateDescription: '多层验证：格式/约束/目标对齐',
    formatValidation: '格式验证',
    constraintValidation: '约束验证',
    alignmentValidation: '目标对齐',
    autoRevise: '自动修复',
    validatePass: '验收通过',
    validateFail: '验收失败',

    // Review
    reviewTitle: '回顾阶段',
    reviewDescription: '查看完整执行历史与可观测数据',
    executionHistory: '执行历史',
    metrics: '指标',
    requestId: '请求 ID',
    duration: '耗时',
    status: '状态',

    // Common
    loading: '加载中...',
    error: '错误',
    success: '成功',
    cancel: '取消',
    confirm: '确认',
    delete: '删除',
    edit: '编辑',
    save: '保存',
    close: '关闭',
    back: '返回',
    next: '下一步',
    previous: '上一步',
  },

  en: {
    // Header
    appTitle: 'TaskForge',
    appSubtitle: 'AI Task Orchestration System',
    languageSwitch: 'Language',
    analysisMode: 'Analysis Mode',

    // Sidebar
    historyTitle: 'History',
    newTask: 'New Task',
    recentConversations: 'Recent Conversations',
    clearHistory: 'Clear History',

    // Main workflow
    inputPlaceholder: 'One sentence, e.g.:\nCannot mention competitors\nUse English\nNo fabricated data\nNo political references',
    outputFormat: 'Output Format',
    directOutput: 'Direct final result',
    stepByStepGuide: 'Plan first, then result',
    taskCategory: 'Task Category',
    outputStyle: 'Your preferred output style',
    structuredDiscussion: 'Structured discussion',
    stepByStepApproach: 'Step-by-step approach',
    comparativeFormat: 'Comparative format',
    simpleFormat: 'Simple',
    supplementInfo: 'Supplementary info (optional)',
    submitAndContinue: 'Confirm and Continue →',
    processingHint: 'All filled content will be saved and used to generate task spec',

    // Pipeline stages
    stageInput: 'Input',
    stageClarify: 'Clarify',
    stageAlign: 'Align',
    stagePreflight: 'Preflight',
    stageExecute: 'Execute',
    stageValidate: 'Validate',
    stageReview: 'Review',

    // Clarify stage
    clarifyTitle: 'Clarification Stage',
    clarifyDescription: 'System identifies gaps with minimal necessary questions',
    targetQuestion: 'What is the target?',
    objectQuestion: 'What is the object?',
    contextQuestion: 'What is the context?',
    constraintQuestion: 'What are the constraints?',
    acceptanceQuestion: 'What are the acceptance criteria?',

    // Spec alignment
    specTitle: 'Task Specification',
    specDescription: 'Structured contract, editable anytime',
    originalSpec: 'Original Input',
    refinedSpec: 'Refined Version',
    specBackground: 'Background',
    specObjective: 'Objective',
    specAction: 'Action',
    specConstraints: 'Constraints',
    specStyle: 'Style',
    specAcceptance: 'Acceptance Criteria',
    editSpec: 'Edit Spec',
    saveSpec: 'Save Spec',

    // Preflight
    preflightTitle: 'Preflight Logic Gate',
    preflightDescription: 'Check dependency closure, input completeness, output reachability',
    planGraph: 'Plan Graph',
    dependencyCheck: 'Dependency Check',
    inputCompleteness: 'Input Completeness',
    outputReachability: 'Output Reachability',
    acceptanceMapping: 'Acceptance Mapping',
    preflightPass: 'Preflight Passed',
    preflightFail: 'Preflight Failed',
    fixAndRetry: 'Fix and Retry',

    // Execute
    executeTitle: 'Execution Stage',
    executeDescription: 'Async task queue with status tracking',
    selectModel: 'Select AI Model',
    recommendedModel: 'Recommended Model',
    modelGPT4: 'GPT-4 (Most Powerful)',
    modelClaude: 'Claude (Balanced)',
    modelGrok: 'Grok (Fast)',
    modelKimi: 'Kimi (Long Context)',
    executing: 'Executing...',
    executionComplete: 'Execution Complete',
    retryExecution: 'Retry Execution',

    // Validate
    validateTitle: 'Validation Stage',
    validateDescription: 'Multi-layer validation: format/constraints/alignment',
    formatValidation: 'Format Validation',
    constraintValidation: 'Constraint Validation',
    alignmentValidation: 'Alignment Validation',
    autoRevise: 'Auto Revise',
    validatePass: 'Validation Passed',
    validateFail: 'Validation Failed',

    // Review
    reviewTitle: 'Review Stage',
    reviewDescription: 'View complete execution history and observability data',
    executionHistory: 'Execution History',
    metrics: 'Metrics',
    requestId: 'Request ID',
    duration: 'Duration',
    status: 'Status',

    // Common
    loading: 'Loading...',
    error: 'Error',
    success: 'Success',
    cancel: 'Cancel',
    confirm: 'Confirm',
    delete: 'Delete',
    edit: 'Edit',
    save: 'Save',
    close: 'Close',
    back: 'Back',
    next: 'Next',
    previous: 'Previous',
  },
};

export function t(key, language = 'zh') {
  const keys = key.split('.');
  let value = translations[language];
  for (const k of keys) {
    value = value?.[k];
  }
  return value || key;
}
