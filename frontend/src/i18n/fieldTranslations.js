/**
 * Field Translations & Mappings
 * 
 * Maps backend field keys to user-friendly Chinese labels and translates values
 */

export const FIELD_LABEL_MAP = {
  zh: {
    // Communication domain
    'recipient': '收件人',
    'communication_goal': '沟通目标',
    'tone_preference': '语气风格',
    'length_preference': '字数上限',
    'constraints': '内容约束',
    'key_points': '关键要点',
    'acceptance_criteria': '验收标准',
    
    // Content creation domain
    'content_type': '内容类型',
    'target_audience': '目标受众',
    'style_keywords': '风格关键词',
    'output_format': '输出格式',
    
    // Technical domain
    'tech_category': '技术类别',
    'tech_stack': '技术栈',
    'specific_requirements': '具体需求',
    
    // Analysis domain
    'analysis_scope': '分析范围',
    'stakeholders': '利益相关者',
    
    // Compliance domain
    'jurisdiction': '管辖权',
    'time_horizon': '时间范围',
  },
  en: {
    'recipient': 'Recipient',
    'communication_goal': 'Communication Goal',
    'tone_preference': 'Tone',
    'length_preference': 'Length Limit',
    'constraints': 'Constraints',
    'key_points': 'Key Points',
    'acceptance_criteria': 'Acceptance Criteria',
    'content_type': 'Content Type',
    'target_audience': 'Target Audience',
    'style_keywords': 'Style Keywords',
    'output_format': 'Output Format',
    'tech_category': 'Tech Category',
    'tech_stack': 'Tech Stack',
    'specific_requirements': 'Requirements',
    'analysis_scope': 'Analysis Scope',
    'stakeholders': 'Stakeholders',
    'jurisdiction': 'Jurisdiction',
    'time_horizon': 'Time Horizon',
  },
};

export const FIELD_VALUE_MAP = {
  zh: {
    // Communication goals
    'inform': '通知',
    'request': '请求',
    'negotiate': '协商',
    'apologize': '道歉',
    'persuade': '说服',
    
    // Tone preferences
    'formal': '正式',
    'casual': '随意',
    'professional': '专业',
    'friendly': '友好',
    'urgent': '紧急',
    'diplomatic': '外交',
    
    // Content types
    'article': '文章',
    'social': '社交媒体',
    'marketing': '营销文案',
    'technical': '技术文档',
    'creative': '创意内容',
    'blog': '博客',
    'email': '邮件',
    
    // Target audiences
    'vendor': '供应商',
    'customer': '客户',
    'internal': '内部员工',
    'executive': '高管',
    'technical': '技术人员',
    'general': '普通大众',
    'expert': '专家',
    
    // Tech categories
    'code': '编写代码',
    'architecture': '设计架构',
    'debugging': '排查问题',
    'optimization': '优化性能',
    'documentation': '编写文档',
    'testing': '编写测试',
    
    // Output formats
    'structured': '结构化',
    'narrative': '叙述性',
    'bullet_points': '要点列表',
    'step_by_step': '分步骤',
    'comparison': '对比',
    'summary': '摘要',
  },
  en: {
    'inform': 'Inform',
    'request': 'Request',
    'negotiate': 'Negotiate',
    'apologize': 'Apologize',
    'persuade': 'Persuade',
    'formal': 'Formal',
    'casual': 'Casual',
    'professional': 'Professional',
    'friendly': 'Friendly',
    'urgent': 'Urgent',
    'diplomatic': 'Diplomatic',
    'article': 'Article',
    'social': 'Social Media',
    'marketing': 'Marketing Copy',
    'technical': 'Technical Doc',
    'creative': 'Creative',
    'blog': 'Blog',
    'email': 'Email',
    'vendor': 'Vendor',
    'customer': 'Customer',
    'internal': 'Internal',
    'executive': 'Executive',
    'technical': 'Technical',
    'general': 'General Public',
    'expert': 'Expert',
    'code': 'Write Code',
    'architecture': 'Design Architecture',
    'debugging': 'Debug',
    'optimization': 'Optimize',
    'documentation': 'Document',
    'testing': 'Test',
    'structured': 'Structured',
    'narrative': 'Narrative',
    'bullet_points': 'Bullet Points',
    'step_by_step': 'Step-by-Step',
    'comparison': 'Comparison',
    'summary': 'Summary',
  },
};

/**
 * Translate a field label
 */
export function translateFieldLabel(key, language = 'zh') {
  return FIELD_LABEL_MAP[language]?.[key] || key;
}

/**
 * Translate a field value
 */
export function translateFieldValue(value, language = 'zh') {
  if (!value) return value;
  
  // If it's an array, translate each item
  if (Array.isArray(value)) {
    return value.map(v => FIELD_VALUE_MAP[language]?.[v] || v);
  }
  
  // If it's a string, try to translate
  if (typeof value === 'string') {
    return FIELD_VALUE_MAP[language]?.[value] || value;
  }
  
  return value;
}

/**
 * Translate acceptance criteria list
 */
export function translateAcceptanceCriteria(criteria, language = 'zh') {
  if (!criteria) return [];
  
  if (typeof criteria === 'string') {
    criteria = criteria.split('\n').filter(c => c.trim());
  }
  
  if (!Array.isArray(criteria)) {
    return [];
  }
  
  // Map common English criteria to Chinese
  const criteriaMap = {
    zh: {
      'Keep the response within 200 words/tokens.': '保持回复在 200 字以内',
      'Match the requested tone and language.': '符合要求的语气和语言',
      'Address the recipient and include a clear action request.': '指明收件人并包含明确的行动请求',
      'Include at least one bullet list for action items.': '至少包含一个行动项目的要点列表',
      'Be clear and unambiguous.': '表达清晰、无歧义',
      'Match the target audience understanding level.': '符合目标受众的理解水平',
      'Include all key points.': '包含所有关键要点',
      'Be original and plagiarism-free.': '内容原创、无抄袭',
      'Follow the specified format.': '遵循指定的格式',
      'Be executable and tested.': '可执行且经过测试',
      'Include proper documentation.': '包含适当的文档',
      'Be logically sound.': '逻辑清晰',
    },
    en: {
      'Keep the response within 200 words/tokens.': 'Keep the response within 200 words/tokens.',
      'Match the requested tone and language.': 'Match the requested tone and language.',
      'Address the recipient and include a clear action request.': 'Address the recipient and include a clear action request.',
      'Include at least one bullet list for action items.': 'Include at least one bullet list for action items.',
      'Be clear and unambiguous.': 'Be clear and unambiguous.',
      'Match the target audience understanding level.': 'Match the target audience understanding level.',
      'Include all key points.': 'Include all key points.',
      'Be original and plagiarism-free.': 'Be original and plagiarism-free.',
      'Follow the specified format.': 'Follow the specified format.',
      'Be executable and tested.': 'Be executable and tested.',
      'Include proper documentation.': 'Include proper documentation.',
      'Be logically sound.': 'Be logically sound.',
    },
  };
  
  const map = criteriaMap[language] || criteriaMap.en;
  
  return criteria.map(c => {
    const trimmed = c.trim();
    return map[trimmed] || trimmed;
  });
}
