"""
Clarify Layer - Minimal Necessary Questions

Implements the clarify phase with:
- Domain-aware field generation
- Minimal required questions (no bloat)
- Smart field ordering and dependencies
- Context-aware defaults
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from .task_taxonomy import TaskTaxonomy, BusinessDomain


@dataclass
class ClarifyField:
    """Represents a single clarification field."""
    key: str
    label: str
    type: str  # short_text, multiline_text, single_choice, multi_choice
    required: bool
    placeholder: str = ""
    help_text: str = ""
    options: List[Dict[str, str]] = None
    default: Any = None
    depends_on: Optional[str] = None  # Field this depends on
    depends_on_value: Optional[str] = None  # Value that triggers this field


class ClarifyLayerBuilder:
    """Builds minimal clarification schemas per domain."""

    # Universal fields that apply to all domains
    UNIVERSAL_FIELDS = [
        ClarifyField(
            key="clarified_request",
            label="你最终想交付的结果（必填）",
            type="multiline_text",
            required=True,
            placeholder="用 1-3 句话写清楚最终要产出什么（例如：一封可直接发送的催发票邮件）。",
            help_text="先明确'做什么'，避免后续执行跑偏。",
        ),
        ClarifyField(
            key="output_preference",
            label="输出方式偏好",
            type="single_choice",
            required=True,
            default="direct",
            options=[
                {"value": "direct", "label": "直接给最终结果"},
                {"value": "outline_then_final", "label": "先大纲再最终结果"},
                {"value": "options_then_pick", "label": "先给多个方案再细化"},
            ],
        ),
    ]

    # Optional context fields
    OPTIONAL_CONTEXT_FIELDS = [
        ClarifyField(
            key="motivation",
            label="做这件事的前因/目的（可选）",
            type="multiline_text",
            required=False,
            placeholder="例如：月底对账要完成，发票未到导致财务无法入账。",
            help_text="说明'为什么现在做'，有助于系统判断优先级和语气。",
        ),
        ClarifyField(
            key="primary_target",
            label="主要作用对象（可选）",
            type="short_text",
            required=False,
            placeholder="例如：供应商A、特斯拉商业模式、纽约天气",
            help_text="说明'对谁/对什么做'，避免内容太空泛。",
        ),
        ClarifyField(
            key="stakeholders",
            label="还涉及哪些对象（可选）",
            type="short_text",
            required=False,
            placeholder="例如：财务、法务、老板、客户",
            help_text="如果有次要相关方，写出来便于平衡表达。",
        ),
        ClarifyField(
            key="success_criteria",
            label="你怎么判断结果'够好'（可选）",
            type="multiline_text",
            required=False,
            placeholder="一行一条，例如：\n结论要有依据\n语气不能太强硬\n控制在200字",
            help_text="这是验收标准，不填也可以。",
        ),
        ClarifyField(
            key="hard_constraints",
            label="硬性约束（可选）",
            type="multiline_text",
            required=False,
            placeholder="一行一条，例如：\n不能提竞品名\n必须用中文\n不能编造数据",
            help_text="任何不能违反的限制都写这里。",
        ),
    ]

    # Domain-specific required fields
    DOMAIN_REQUIRED_FIELDS: Dict[BusinessDomain, List[ClarifyField]] = {
        BusinessDomain.MARKETING: [
            ClarifyField(
                key="target_audience",
                label="目标受众（必填）",
                type="short_text",
                required=True,
                placeholder="例如：25-35岁的女性上班族",
                help_text="明确你要说服或吸引谁。",
            ),
            ClarifyField(
                key="campaign_type",
                label="活动类型（必填）",
                type="single_choice",
                required=True,
                options=[
                    {"value": "email", "label": "邮件营销"},
                    {"value": "social", "label": "社交媒体"},
                    {"value": "content", "label": "内容营销"},
                    {"value": "ad", "label": "广告文案"},
                    {"value": "other", "label": "其他"},
                ],
            ),
            ClarifyField(
                key="tone",
                label="语气风格（必填）",
                type="single_choice",
                required=True,
                options=[
                    {"value": "professional", "label": "专业正式"},
                    {"value": "friendly", "label": "友好亲切"},
                    {"value": "urgent", "label": "紧急催促"},
                    {"value": "creative", "label": "创意新颖"},
                ],
            ),
        ],
        BusinessDomain.TECHNOLOGY: [
            ClarifyField(
                key="language",
                label="编程语言（必填）",
                type="single_choice",
                required=True,
                options=[
                    {"value": "python", "label": "Python"},
                    {"value": "javascript", "label": "JavaScript"},
                    {"value": "typescript", "label": "TypeScript"},
                    {"value": "java", "label": "Java"},
                    {"value": "go", "label": "Go"},
                    {"value": "rust", "label": "Rust"},
                    {"value": "other", "label": "其他"},
                ],
            ),
            ClarifyField(
                key="framework",
                label="框架/库（必填）",
                type="short_text",
                required=True,
                placeholder="例如：FastAPI, React, Django",
                help_text="指定你要使用的框架或库。",
            ),
            ClarifyField(
                key="requirements",
                label="功能需求（必填）",
                type="multiline_text",
                required=True,
                placeholder="一行一条，例如：\n支持用户认证\n数据库持久化\n错误处理",
                help_text="列出核心功能需求。",
            ),
        ],
        BusinessDomain.OPERATIONS: [
            ClarifyField(
                key="process_name",
                label="流程名称（必填）",
                type="short_text",
                required=True,
                placeholder="例如：客户投诉处理流程",
                help_text="简洁地命名这个流程。",
            ),
            ClarifyField(
                key="current_state",
                label="当前状态（必填）",
                type="multiline_text",
                required=True,
                placeholder="描述现在是怎么做的，有什么问题。",
                help_text="说明现状和痛点。",
            ),
            ClarifyField(
                key="desired_outcome",
                label="期望结果（必填）",
                type="multiline_text",
                required=True,
                placeholder="优化后应该是什么样的。",
                help_text="明确目标状态。",
            ),
        ],
        BusinessDomain.LEGAL: [
            ClarifyField(
                key="document_type",
                label="文件类型（必填）",
                type="single_choice",
                required=True,
                options=[
                    {"value": "contract", "label": "合同"},
                    {"value": "agreement", "label": "协议"},
                    {"value": "policy", "label": "政策/条款"},
                    {"value": "memo", "label": "备忘录"},
                    {"value": "other", "label": "其他"},
                ],
            ),
            ClarifyField(
                key="jurisdiction",
                label="适用司法管辖区（必填）",
                type="short_text",
                required=True,
                placeholder="例如：中国、美国加州、英国",
                help_text="指定适用的法律管辖区。",
            ),
            ClarifyField(
                key="parties_involved",
                label="涉及方（必填）",
                type="short_text",
                required=True,
                placeholder="例如：公司A、个人B、第三方C",
                help_text="列出所有相关方。",
            ),
        ],
        BusinessDomain.HR: [
            ClarifyField(
                key="hr_function",
                label="HR 职能（必填）",
                type="single_choice",
                required=True,
                options=[
                    {"value": "recruitment", "label": "招聘"},
                    {"value": "onboarding", "label": "入职"},
                    {"value": "performance", "label": "绩效"},
                    {"value": "compensation", "label": "薪酬福利"},
                    {"value": "compliance", "label": "合规"},
                    {"value": "other", "label": "其他"},
                ],
            ),
            ClarifyField(
                key="employee_count",
                label="涉及员工数（必填）",
                type="short_text",
                required=True,
                placeholder="例如：1人、10人、全公司",
                help_text="说明影响范围。",
            ),
            ClarifyField(
                key="scope",
                label="范围/部门（必填）",
                type="short_text",
                required=True,
                placeholder="例如：工程部、全公司、特定地区",
                help_text="明确适用范围。",
            ),
        ],
        BusinessDomain.FINANCE: [
            ClarifyField(
                key="financial_metric",
                label="财务指标（必填）",
                type="short_text",
                required=True,
                placeholder="例如：收入、成本、利润率、现金流",
                help_text="指定要分析的指标。",
            ),
            ClarifyField(
                key="time_period",
                label="时间周期（必填）",
                type="single_choice",
                required=True,
                options=[
                    {"value": "monthly", "label": "月度"},
                    {"value": "quarterly", "label": "季度"},
                    {"value": "annual", "label": "年度"},
                    {"value": "custom", "label": "自定义"},
                ],
            ),
            ClarifyField(
                key="scope",
                label="分析范围（必填）",
                type="short_text",
                required=True,
                placeholder="例如：整个公司、特定产品线、地区",
                help_text="明确分析的范围。",
            ),
        ],
    }

    @classmethod
    def build_schema(
        cls,
        domain: BusinessDomain,
        include_optional: bool = True,
    ) -> Dict[str, Any]:
        """Build a clarify schema for a domain."""
        fields = []

        # Add universal required fields
        fields.extend([f.to_dict() for f in cls.UNIVERSAL_FIELDS])

        # Add domain-specific required fields
        domain_required = cls.DOMAIN_REQUIRED_FIELDS.get(domain, [])
        fields.extend([f.to_dict() for f in domain_required])

        # Add optional context fields if requested
        if include_optional:
            fields.extend([f.to_dict() for f in cls.OPTIONAL_CONTEXT_FIELDS])

        return {
            "title": f"澄清 - {TaskTaxonomy.get_domain_profile(domain).display_name}",
            "description": "请回答以下问题，帮助系统更准确地理解你的需求。",
            "fields": fields,
        }

    @classmethod
    def get_required_field_keys(cls, domain: BusinessDomain) -> List[str]:
        """Get keys of all required fields for a domain."""
        keys = [f.key for f in cls.UNIVERSAL_FIELDS if f.required]
        domain_required = cls.DOMAIN_REQUIRED_FIELDS.get(domain, [])
        keys.extend([f.key for f in domain_required if f.required])
        return keys

    @classmethod
    def get_optional_field_keys(cls, domain: BusinessDomain) -> List[str]:
        """Get keys of all optional fields for a domain."""
        keys = [f.key for f in cls.OPTIONAL_CONTEXT_FIELDS]
        return keys


# Helper to convert ClarifyField to dict
def _clarify_field_to_dict(field: ClarifyField) -> Dict[str, Any]:
    """Convert ClarifyField to dictionary for JSON serialization."""
    result = {
        "key": field.key,
        "label": field.label,
        "type": field.type,
        "required": field.required,
    }
    if field.placeholder:
        result["placeholder"] = field.placeholder
    if field.help_text:
        result["help_text"] = field.help_text
    if field.options:
        result["options"] = field.options
    if field.default is not None:
        result["default"] = field.default
    if field.depends_on:
        result["depends_on"] = field.depends_on
    if field.depends_on_value:
        result["depends_on_value"] = field.depends_on_value
    return result


# Monkey-patch to_dict method
ClarifyField.to_dict = lambda self: _clarify_field_to_dict(self)
