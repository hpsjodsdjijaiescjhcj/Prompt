"""
Task Taxonomy v2 - Semantic Classification & Domain Routing

Core principle: Classify user intent into domain + characteristics.
- Uses semantic understanding, not just keyword matching
- Provides fallback strategies for ambiguous cases
- Returns confidence scores for routing decisions
"""

from typing import Tuple, List, Dict, Optional
from orchestrator.domain_model import (
    TaskDomain, TaskCharacteristic, ClarificationSchema, ClarificationField
)


# ════════════════════════════════════════════════════════════════════════════
# SEMANTIC CLASSIFICATION
# ════════════════════════════════════════════════════════════════════════════

class SemanticClassifier:
    """Classify user input into domain and characteristics."""
    
    # Domain keywords - semantic markers
    DOMAIN_KEYWORDS = {
        TaskDomain.COMMUNICATION: {
            "keywords": ["邮件", "email", "消息", "message", "通知", "notification", 
                        "沟通", "communicate", "回复", "reply", "发送", "send",
                        "联系", "contact", "信函", "letter", "备忘", "memo"],
            "patterns": ["写.*邮件", "发.*邮件", "回复.*邮件", "给.*写"],
        },
        TaskDomain.CONTENT_CREATION: {
            "keywords": ["文章", "article", "博客", "blog", "内容", "content",
                        "文案", "copywriting", "创意", "creative", "写作", "writing",
                        "故事", "story", "脚本", "script", "标题", "title"],
            "patterns": ["写.*文章", "创作", "编写.*内容", "撰写"],
        },
        TaskDomain.TECHNICAL: {
            "keywords": ["代码", "code", "编程", "programming", "函数", "function",
                        "类", "class", "算法", "algorithm", "架构", "architecture",
                        "数据库", "database", "API", "接口", "interface", "调试", "debug"],
            "patterns": ["写.*代码", "实现", "编写.*程序", "设计.*架构"],
        },
        TaskDomain.ANALYSIS: {
            "keywords": ["分析", "analysis", "研究", "research", "数据", "data",
                        "报告", "report", "洞察", "insight", "趋势", "trend",
                        "评估", "evaluate", "对比", "compare", "统计", "statistics"],
            "patterns": ["分析.*", "研究.*", "对比.*", "评估.*"],
        },
        TaskDomain.OPERATIONS: {
            "keywords": ["流程", "process", "工作流", "workflow", "优化", "optimize",
                        "改进", "improve", "效率", "efficiency", "自动化", "automation",
                        "管理", "management", "计划", "planning"],
            "patterns": ["优化.*流程", "改进.*工作", "设计.*流程"],
        },
        TaskDomain.COMPLIANCE: {
            "keywords": ["法律", "legal", "合规", "compliance", "合同", "contract",
                        "政策", "policy", "条款", "terms", "风险", "risk",
                        "审核", "audit", "规范", "regulation"],
            "patterns": ["审查.*合规", "起草.*合同", "检查.*风险"],
        },
        TaskDomain.STRATEGY: {
            "keywords": ["战略", "strategy", "计划", "plan", "目标", "goal",
                        "决策", "decision", "建议", "recommendation", "方案", "solution",
                        "愿景", "vision", "路线图", "roadmap"],
            "patterns": ["制定.*战略", "规划.*方案", "提出.*建议"],
        },
    }
    
    # Characteristic indicators
    CHARACTERISTIC_KEYWORDS = {
        TaskCharacteristic.CREATIVE: {
            "keywords": ["创意", "creative", "原创", "original", "想象", "imagine",
                        "新颖", "novel", "独特", "unique", "头脑风暴", "brainstorm"],
        },
        TaskCharacteristic.ANALYTICAL: {
            "keywords": ["分析", "analyze", "逻辑", "logic", "推理", "reasoning",
                        "分解", "decompose", "对比", "compare", "评估", "evaluate"],
        },
        TaskCharacteristic.PROCEDURAL: {
            "keywords": ["步骤", "steps", "流程", "process", "按照", "follow",
                        "顺序", "sequence", "规则", "rules", "标准", "standard"],
        },
        TaskCharacteristic.TRANSFORMATIVE: {
            "keywords": ["转换", "convert", "翻译", "translate", "改写", "rewrite",
                        "格式化", "format", "提取", "extract", "总结", "summarize"],
        },
        TaskCharacteristic.GENERATIVE: {
            "keywords": ["生成", "generate", "创建", "create", "编写", "write",
                        "撰写", "compose", "制作", "produce", "生成", "generate"],
        },
    }
    
    @staticmethod
    def classify(text: str) -> Tuple[TaskDomain, List[TaskCharacteristic], float]:
        """
        Classify user input into domain and characteristics.
        
        Returns: (domain, characteristics, confidence)
        """
        text_lower = text.lower()
        
        # Score each domain
        domain_scores = {}
        for domain, markers in SemanticClassifier.DOMAIN_KEYWORDS.items():
            score = SemanticClassifier._score_domain(text_lower, markers)
            domain_scores[domain] = score
        
        # Find best domain
        best_domain = max(domain_scores, key=domain_scores.get)
        best_score = domain_scores[best_domain]
        
        # If confidence too low, use UNKNOWN
        if best_score < 0.3:
            best_domain = TaskDomain.UNKNOWN
            confidence = 0.0
        else:
            confidence = min(best_score, 1.0)
        
        # Classify characteristics
        characteristics = SemanticClassifier._classify_characteristics(text_lower)
        
        return best_domain, characteristics, confidence
    
    @staticmethod
    def _score_domain(text: str, markers: Dict) -> float:
        """Score how well text matches a domain."""
        score = 0.0
        
        # Keyword matching
        keywords = markers.get("keywords", [])
        keyword_matches = sum(1 for kw in keywords if kw in text)
        score += keyword_matches * 0.1
        
        # Pattern matching
        import re
        patterns = markers.get("patterns", [])
        for pattern in patterns:
            if re.search(pattern, text):
                score += 0.3
        
        return min(score, 1.0)
    
    @staticmethod
    def _classify_characteristics(text: str) -> List[TaskCharacteristic]:
        """Classify task characteristics."""
        characteristics = []
        
        for char, markers in SemanticClassifier.CHARACTERISTIC_KEYWORDS.items():
            keywords = markers.get("keywords", [])
            if any(kw in text for kw in keywords):
                characteristics.append(char)
        
        # If no characteristics detected, infer from common patterns
        if not characteristics:
            if any(word in text for word in ["写", "创作", "编写", "撰写"]):
                characteristics.append(TaskCharacteristic.GENERATIVE)
            elif any(word in text for word in ["分析", "研究", "对比"]):
                characteristics.append(TaskCharacteristic.ANALYTICAL)
            elif any(word in text for word in ["转换", "翻译", "改写"]):
                characteristics.append(TaskCharacteristic.TRANSFORMATIVE)
        
        return characteristics


# ════════════════════════════════════════════════════════════════════════════
# CLARIFICATION SCHEMAS - Domain-Specific Questions
# ════════════════════════════════════════════════════════════════════════════

def get_clarification_schema(domain: TaskDomain) -> ClarificationSchema:
    """Get domain-specific clarification schema."""
    
    if domain == TaskDomain.COMMUNICATION:
        return _communication_schema()
    elif domain == TaskDomain.CONTENT_CREATION:
        return _content_creation_schema()
    elif domain == TaskDomain.TECHNICAL:
        return _technical_schema()
    elif domain == TaskDomain.ANALYSIS:
        return _analysis_schema()
    elif domain == TaskDomain.OPERATIONS:
        return _operations_schema()
    elif domain == TaskDomain.COMPLIANCE:
        return _compliance_schema()
    elif domain == TaskDomain.STRATEGY:
        return _strategy_schema()
    else:
        return _generic_schema()


def _communication_schema() -> ClarificationSchema:
    """Clarification schema for communication tasks."""
    return ClarificationSchema(
        domain=TaskDomain.COMMUNICATION,
        title="沟通任务澄清",
        description="为了更好地帮助您，请补充以下信息",
        fields=[
            ClarificationField(
                key="recipient",
                label="收件人/对象",
                field_type="short_text",
                required=True,
                placeholder="例如：我的经理、客户、团队成员",
                help_text="明确沟通的对象有助于调整语气和内容"
            ),
            ClarificationField(
                key="communication_goal",
                label="沟通目标",
                field_type="single_choice",
                required=True,
                options=[
                    {"value": "inform", "label": "通知/告知"},
                    {"value": "request", "label": "请求/询问"},
                    {"value": "negotiate", "label": "协商/讨论"},
                    {"value": "apologize", "label": "道歉/解释"},
                    {"value": "persuade", "label": "说服/建议"},
                ]
            ),
            ClarificationField(
                key="tone_preference",
                label="语气风格",
                field_type="single_choice",
                required=False,
                options=[
                    {"value": "formal", "label": "正式专业"},
                    {"value": "friendly", "label": "友好亲切"},
                    {"value": "neutral", "label": "中立客观"},
                    {"value": "urgent", "label": "紧急强调"},
                ]
            ),
            ClarificationField(
                key="constraints",
                label="特殊要求或限制",
                field_type="multiline_text",
                required=False,
                placeholder="例如：不超过200字、必须包含X内容、避免提及Y",
                help_text="任何特殊的格式或内容要求"
            ),
        ]
    )


def _content_creation_schema() -> ClarificationSchema:
    """Clarification schema for content creation tasks."""
    return ClarificationSchema(
        domain=TaskDomain.CONTENT_CREATION,
        title="内容创作澄清",
        description="为了创作更符合您需求的内容，请补充以下信息",
        fields=[
            ClarificationField(
                key="content_type",
                label="内容类型",
                field_type="single_choice",
                required=True,
                options=[
                    {"value": "article", "label": "文章/博客"},
                    {"value": "social", "label": "社交媒体"},
                    {"value": "marketing", "label": "营销文案"},
                    {"value": "technical", "label": "技术文档"},
                    {"value": "creative", "label": "创意内容"},
                ]
            ),
            ClarificationField(
                key="target_audience",
                label="目标受众",
                field_type="short_text",
                required=True,
                placeholder="例如：初学者、专业人士、普通大众",
                help_text="了解受众有助于调整内容深度和风格"
            ),
            ClarificationField(
                key="length_preference",
                label="内容长度",
                field_type="single_choice",
                required=False,
                options=[
                    {"value": "short", "label": "简短（<300字）"},
                    {"value": "medium", "label": "中等（300-1000字）"},
                    {"value": "long", "label": "详细（>1000字）"},
                ]
            ),
            ClarificationField(
                key="style_keywords",
                label="风格关键词",
                field_type="multiline_text",
                required=False,
                placeholder="例如：幽默、严肃、鼓舞人心、数据驱动",
                help_text="用逗号分隔多个风格关键词"
            ),
        ]
    )


def _technical_schema() -> ClarificationSchema:
    """Clarification schema for technical tasks."""
    return ClarificationSchema(
        domain=TaskDomain.TECHNICAL,
        title="技术任务澄清",
        description="为了编写更合适的代码或架构，请补充以下信息",
        fields=[
            ClarificationField(
                key="tech_category",
                label="技术类别",
                field_type="single_choice",
                required=True,
                options=[
                    {"value": "code", "label": "代码编写"},
                    {"value": "architecture", "label": "架构设计"},
                    {"value": "debugging", "label": "问题排查"},
                    {"value": "optimization", "label": "性能优化"},
                    {"value": "documentation", "label": "文档编写"},
                ]
            ),
            ClarificationField(
                key="tech_stack",
                label="技术栈/环境",
                field_type="short_text",
                required=True,
                placeholder="例如：Python 3.9, Django, PostgreSQL",
                help_text="指定编程语言、框架、版本等"
            ),
            ClarificationField(
                key="specific_requirements",
                label="具体需求",
                field_type="multiline_text",
                required=False,
                placeholder="例如：必须支持并发、需要错误处理、要求可测试",
                help_text="任何特殊的功能或非功能需求"
            ),
        ]
    )


def _analysis_schema() -> ClarificationSchema:
    """Clarification schema for analysis tasks."""
    return ClarificationSchema(
        domain=TaskDomain.ANALYSIS,
        title="分析任务澄清",
        description="为了进行更有针对性的分析，请补充以下信息",
        fields=[
            ClarificationField(
                key="analysis_scope",
                label="分析范围",
                field_type="multiline_text",
                required=True,
                placeholder="例如：2024年Q1-Q3、北美市场、18-35岁用户",
                help_text="明确分析的时间、地域、人群等范围"
            ),
            ClarificationField(
                key="key_questions",
                label="核心问题",
                field_type="multiline_text",
                required=False,
                placeholder="例如：为什么销售下降？哪个市场表现最好？",
                help_text="您最想回答的具体问题"
            ),
            ClarificationField(
                key="expected_output",
                label="期望输出",
                field_type="single_choice",
                required=False,
                options=[
                    {"value": "summary", "label": "简要总结"},
                    {"value": "detailed", "label": "详细报告"},
                    {"value": "recommendations", "label": "建议方案"},
                    {"value": "all", "label": "完整分析"},
                ]
            ),
        ]
    )


def _operations_schema() -> ClarificationSchema:
    """Clarification schema for operations tasks."""
    return ClarificationSchema(
        domain=TaskDomain.OPERATIONS,
        title="运营任务澄清",
        description="为了优化您的流程，请补充以下信息",
        fields=[
            ClarificationField(
                key="current_process",
                label="当前流程描述",
                field_type="multiline_text",
                required=True,
                placeholder="描述现有的工作流程、步骤、参与者等",
                help_text="详细描述现状有助于找到改进点"
            ),
            ClarificationField(
                key="current_pain",
                label="主要痛点",
                field_type="multiline_text",
                required=False,
                placeholder="例如：耗时长、容易出错、成本高",
                help_text="您最想解决的问题"
            ),
            ClarificationField(
                key="optimization_goal",
                label="优化目标",
                field_type="short_text",
                required=False,
                placeholder="例如：提高效率30%、降低成本、减少错误",
                help_text="具体的改进目标"
            ),
        ]
    )


def _compliance_schema() -> ClarificationSchema:
    """Clarification schema for compliance tasks."""
    return ClarificationSchema(
        domain=TaskDomain.COMPLIANCE,
        title="合规任务澄清",
        description="为了确保合规性，请补充以下信息",
        fields=[
            ClarificationField(
                key="jurisdiction",
                label="适用法律/地区",
                field_type="short_text",
                required=True,
                placeholder="例如：中国、美国加州、欧盟",
                help_text="明确适用的法律体系"
            ),
            ClarificationField(
                key="compliance_type",
                label="合规类型",
                field_type="single_choice",
                required=True,
                options=[
                    {"value": "contract", "label": "合同审查"},
                    {"value": "policy", "label": "政策制定"},
                    {"value": "risk", "label": "风险评估"},
                    {"value": "audit", "label": "审计准备"},
                ]
            ),
            ClarificationField(
                key="specific_requirements",
                label="特定要求",
                field_type="multiline_text",
                required=False,
                placeholder="例如：必须包含X条款、避免Y风险",
                help_text="任何特定的法律或业务要求"
            ),
        ]
    )


def _strategy_schema() -> ClarificationSchema:
    """Clarification schema for strategy tasks."""
    return ClarificationSchema(
        domain=TaskDomain.STRATEGY,
        title="战略任务澄清",
        description="为了制定更好的战略，请补充以下信息",
        fields=[
            ClarificationField(
                key="strategic_context",
                label="战略背景",
                field_type="multiline_text",
                required=True,
                placeholder="描述您的业务、市场、竞争环境等",
                help_text="背景信息有助于制定更合适的战略"
            ),
            ClarificationField(
                key="time_horizon",
                label="时间范围",
                field_type="single_choice",
                required=False,
                options=[
                    {"value": "short", "label": "短期（3-6个月）"},
                    {"value": "medium", "label": "中期（6-18个月）"},
                    {"value": "long", "label": "长期（18个月+）"},
                ]
            ),
            ClarificationField(
                key="stakeholders",
                label="主要利益相关者",
                field_type="multiline_text",
                required=False,
                placeholder="例如：董事会、员工、客户、投资者",
                help_text="需要考虑的关键利益相关者"
            ),
        ]
    )


def _generic_schema() -> ClarificationSchema:
    """Generic clarification schema for unknown domains."""
    return ClarificationSchema(
        domain=TaskDomain.UNKNOWN,
        title="任务澄清",
        description="为了更好地理解您的需求，请补充以下信息",
        fields=[
            ClarificationField(
                key="objective",
                label="具体目标",
                field_type="multiline_text",
                required=True,
                placeholder="您想要达成什么目标？",
                help_text="清晰的目标定义"
            ),
            ClarificationField(
                key="constraints",
                label="约束条件",
                field_type="multiline_text",
                required=False,
                placeholder="有什么限制或要求吗？",
                help_text="任何限制条件"
            ),
        ]
    )


# ════════════════════════════════════════════════════════════════════════════
# PUBLIC API
# ════════════════════════════════════════════════════════════════════════════

def infer_domain_and_characteristics(text: str) -> Tuple[TaskDomain, List[TaskCharacteristic], float]:
    """
    Infer domain and characteristics from user input.
    
    Returns: (domain, characteristics, confidence)
    """
    return SemanticClassifier.classify(text)
