"""
AI提示词管家 — 模型能力配置库 v2
包含5个主流AI模型的多维度能力评估
"""

import os

# Gemini 配置（Google AI Studio）
GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

# 兼容旧命名，避免其他模块改动过大
LLM_MODEL = GEMINI_MODEL

# ============================================================
# 模型能力数据库
# scores: 1-10 分制
# cost: 1=最便宜 10=最贵 (相对成本)
# speed: 1=最慢 10=最快 (响应速度)
# context_window: 最大上下文窗口 (tokens)
# ============================================================

MODELS = {
    "GPT-4o": {
        "name": "GPT-4o",
        "provider": "OpenAI",
        "icon": "🤖",
        "color": "#10a37f",
        "description": "OpenAI旗舰多模态模型，综合能力最强，尤其擅长创意写作、复杂指令遵循和多模态理解",
        "scores": {
            "email": 9,
            "code": 9,
            "content": 9,
            "research": 8,
            "analysis": 8,
            "document": 8,
            "planning": 9,
            "generic": 8,
        },
        "cost": 7,
        "speed": 8,
        "context_window": 128000,
        "strengths": ["创意写作", "多轮对话", "指令遵循", "多模态理解", "插件生态"],
        "weaknesses": ["成本较高", "偶有幻觉", "中文能力略逊于国产模型"],
        "best_for": ["创意内容生成", "产品文案", "多轮复杂对话", "图文理解"],
        "prompt_tips": "GPT-4o偏好清晰的角色设定和结构化输出要求。用Markdown格式组织提示效果最佳，明确告知输出格式和风格。",
        "prompt_style": "structured",
    },
    "Claude": {
        "name": "Claude",
        "provider": "Anthropic",
        "icon": "🧠",
        "color": "#d97706",
        "description": "Anthropic旗舰模型，在长文本分析、严谨推理、代码生成和学术写作方面表现卓越",
        "scores": {
            "email": 9,
            "code": 10,
            "content": 9,
            "research": 8,
            "analysis": 9,
            "document": 10,
            "planning": 9,
            "generic": 9,
        },
        "cost": 8,
        "speed": 7,
        "context_window": 200000,
        "strengths": ["超长文本处理", "代码生成", "严谨推理", "学术分析", "安全性"],
        "weaknesses": ["无实时搜索", "图像能力有限", "有时过于谨慎"],
        "best_for": ["长文档分析", "复杂编程任务", "学术论文", "逻辑推理", "法律文本"],
        "prompt_tips": "Claude偏好详细的上下文和背景说明。给予充分背景信息效果更好，支持XML标签来组织复杂提示，擅长处理超长输入。",
        "prompt_style": "detailed",
    },
    "Gemini": {
        "name": "Gemini",
        "provider": "Google",
        "icon": "💎",
        "color": "#4285f4",
        "description": "Google旗舰模型，原生支持实时搜索和多模态，擅长信息整合和跨语言任务",
        "scores": {
            "email": 7,
            "code": 8,
            "content": 8,
            "research": 10,
            "analysis": 8,
            "document": 9,
            "planning": 8,
            "generic": 8,
        },
        "cost": 5,
        "speed": 9,
        "context_window": 1000000,
        "strengths": ["实时搜索", "多模态", "超大上下文", "多语言", "Google生态集成"],
        "weaknesses": ["创意写作略弱", "中文风格偏翻译腔", "输出稳定性有波动"],
        "best_for": ["实时信息查询", "多语言翻译", "视频/图片理解", "大量文档处理"],
        "prompt_tips": "Gemini偏好简洁直接的提示。善用其搜索能力获取最新信息，适合需要事实核查和实时数据的任务。",
        "prompt_style": "concise",
    },
    "DeepSeek": {
        "name": "DeepSeek",
        "provider": "DeepSeek",
        "icon": "🔍",
        "color": "#6366f1",
        "description": "国产高性能开源模型，在深度推理、数学和编程方面表现出色，性价比极高",
        "scores": {
            "email": 6,
            "code": 10,
            "content": 7,
            "research": 7,
            "analysis": 8,
            "document": 7,
            "planning": 7,
            "generic": 7,
        },
        "cost": 2,
        "speed": 8,
        "context_window": 128000,
        "strengths": ["深度推理", "数学计算", "代码生成", "性价比极高", "开源可部署"],
        "weaknesses": ["创意写作风格较朴素", "英文优于中文", "多模态能力有限"],
        "best_for": ["数学证明", "算法设计", "代码重构", "逻辑分析", "科学计算"],
        "prompt_tips": "DeepSeek偏好分步骤推理。明确要求'请一步一步思考'效果最佳，适合复杂逻辑和数学推导任务。",
        "prompt_style": "step_by_step",
    },
    "Perplexity": {
        "name": "Perplexity",
        "provider": "Perplexity AI",
        "icon": "🌐",
        "color": "#20b2aa",
        "description": "专注搜索增强的AI引擎，每个回答都附带实时来源引用，适合需要最新信息和事实核查的任务",
        "scores": {
            "email": 6,
            "code": 5,
            "content": 6,
            "research": 10,
            "analysis": 8,
            "document": 7,
            "planning": 7,
            "generic": 6,
        },
        "cost": 4,
        "speed": 7,
        "context_window": 32000,
        "strengths": ["实时搜索引用", "来源透明", "事实核查", "新闻追踪", "市场数据"],
        "weaknesses": ["创作能力弱", "编程能力有限", "长文本生成不足"],
        "best_for": ["实时资讯查询", "竞品调研", "行业报告数据", "学术文献搜索", "事实验证"],
        "prompt_tips": "Perplexity擅长检索式任务。明确告知需要最新数据、来源引用，效果最好。适合需要引用和出处的研究类任务。",
        "prompt_style": "research",
    },
}

# ============================================================
# 任务类型定义
# ============================================================

TASK_TYPES = {
    "email": {
        "name": "邮件起草",
        "icon": "📧",
        "description": "商务邮件、通知、回复、催办、邀请函等沟通类任务",
        "examples": ["催款邮件", "会议通知", "合作邀请", "项目跟进"],
    },
    "code": {
        "name": "代码工程",
        "icon": "💻",
        "description": "代码编写、调试、重构、架构设计、代码审查等工程类任务",
        "examples": ["Python爬虫", "API接口开发", "bug修复", "性能优化"],
    },
    "content": {
        "name": "内容创作",
        "icon": "✍️",
        "description": "文章、文案、营销内容、创意写作、脚本等创作类任务",
        "examples": ["小红书文案", "公众号文章", "广告标题", "产品介绍"],
    },
    "research": {
        "name": "调研分析",
        "icon": "🔍",
        "description": "市场调研、竞品分析、行业研究、信息整合等调研类任务",
        "examples": ["竞品对比", "行业趋势报告", "用户调研分析", "市场机会评估"],
    },
    "analysis": {
        "name": "数据分析",
        "icon": "📊",
        "description": "数据解读、业务指标分析、财务分析、运营诊断等分析类任务",
        "examples": ["用户留存分析", "销售数据解读", "A/B测试报告", "财务指标诊断"],
    },
    "document": {
        "name": "文档处理",
        "icon": "📄",
        "description": "文档总结、内容提取、格式整理、会议纪要等文档加工任务",
        "examples": ["合同摘要", "会议纪要", "报告整理", "关键信息提取"],
    },
    "planning": {
        "name": "规划决策",
        "icon": "🎯",
        "description": "项目规划、战略制定、方案设计、决策分析等规划类任务",
        "examples": ["产品路线图", "季度OKR", "风险评估", "项目方案"],
    },
    "generic": {
        "name": "通用任务",
        "icon": "⚡",
        "description": "其他无法明确分类但需要AI协助完成的任务",
        "examples": ["复杂问题分析", "综合建议", "自定义任务"],
    },
}

# ============================================================
# 复杂度定义（用于推荐算法加权）
# ============================================================

COMPLEXITY_WEIGHTS = {
    "low": {"cost_weight": 0.3, "ability_weight": 0.5, "speed_weight": 0.2},
    "medium": {"cost_weight": 0.2, "ability_weight": 0.6, "speed_weight": 0.2},
    "high": {"cost_weight": 0.1, "ability_weight": 0.8, "speed_weight": 0.1},
}
