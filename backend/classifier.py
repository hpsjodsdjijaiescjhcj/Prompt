"""
任务分类器 v3 — 统一任务类型体系
优先使用 LLM 语义分类，不可用时降级到关键词匹配
"""

import logging

import llm_client
from config import TASK_TYPES

logger = logging.getLogger(__name__)

# ============================================================
# 关键词匹配 Fallback（每类独立，无跨类混淆）
# ============================================================

KEYWORDS = {
    "email": [
        "邮件", "邮箱", "email", "e-mail", "mail",
        "写信", "发信", "回复", "催款", "催办", "跟进",
        "通知", "告知", "提醒", "邀请函", "确认函",
        "谢谢邮件", "拒绝邮件", "道歉邮件", "投诉邮件",
        "商务信函", "商务邮件", "内部邮件",
        "follow up", "reply", "draft email", "write email",
    ],
    "code": [
        "代码", "编程", "程序", "函数", "bug", "调试", "开发",
        "python", "java", "javascript", "typescript", "react", "vue", "golang",
        "数据库", "sql", "html", "css", "算法", "数据结构",
        "部署", "docker", "git", "kubernetes", "前端", "后端", "全栈",
        "code", "debug", "deploy", "script", "自动化", "爬虫",
        "接口", "api", "框架", "library", "sdk", "微服务",
        "重构", "refactor", "review", "代码审查", "单元测试", "测试",
    ],
    "content": [
        "文案", "文章", "故事", "小说", "诗", "剧本", "广告",
        "营销", "推广", "宣传", "标题", "slogan", "创作",
        "小红书", "公众号", "微博", "朋友圈", "抖音", "短视频",
        "write", "article", "blog", "copy", "content", "essay",
        "文笔", "段落", "描述", "产品介绍", "品牌故事",
        "SEO", "软文", "种草", "带货", "转化率",
        "翻译", "改写", "润色", "创意", "文风",
    ],
    "research": [
        "调研", "调查", "研究", "竞品", "对比", "比较", "区别",
        "市场", "行业", "趋势", "报告", "综述", "review",
        "是什么", "是谁", "在哪", "怎么样", "多少",
        "推荐", "哪个好", "评测", "评价", "排名", "排行",
        "search", "find", "latest", "news", "what is",
        "百科", "定义", "概念", "解释", "来源",
        "信息收集", "数据收集", "事实核查",
    ],
    "analysis": [
        "分析", "解读", "诊断", "洞察", "评估", "判断",
        "数据", "指标", "指数", "率", "占比", "趋势图",
        "原因", "为什么", "因果", "影响", "关联",
        "SWOT", "PEST", "波特五力", "财务分析", "运营分析",
        "用户分析", "留存", "转化", "漏斗", "归因",
        "A/B测试", "增长分析", "商业智能", "BI", "dashboard",
    ],
    "document": [
        "总结", "摘要", "提取", "整理", "归纳", "梳理",
        "文档", "合同", "协议", "报告", "纪要", "会议",
        "压缩", "精简", "要点", "关键信息",
        "summarize", "extract", "summarization",
        "这篇文章", "这份报告", "这个文件", "以下内容",
        "读", "理解", "分析这段", "归纳以下",
    ],
    "planning": [
        "计划", "规划", "方案", "策略", "路线图", "roadmap",
        "OKR", "KPI", "目标", "里程碑", "排期",
        "项目", "任务分解", "WBS", "甘特图",
        "决策", "选择", "建议", "方向", "优先级",
        "流程", "SOP", "操作手册", "规范",
        "战略", "布局", "年度计划", "季度计划",
    ],
}

CLASSIFIER_SYSTEM_PROMPT = """你是任务分类专家。分析用户需求，返回最准确的任务类型分类。

可用类型（必须精确使用以下标识）：
- email:    商务邮件、通知、回复、催办、邀请函等沟通类任务
- code:     代码编写、调试、重构、架构设计、代码审查等工程类任务
- content:  文章、文案、营销内容、创意写作、脚本等创作类任务
- research: 市场调研、竞品分析、信息检索、行业研究等调研类任务
- analysis: 数据解读、业务指标分析、财务分析、运营诊断等分析类任务
- document: 文档总结、内容提取、格式整理、会议纪要等文档加工任务
- planning: 项目规划、战略制定、方案设计、决策分析等规划类任务
- generic:  无法明确归类的综合性任务

分类规则：
1. email 仅限于有明确"写邮件/发邮件/回复邮件"意图的任务
2. code 仅限于有明确编程、调试、部署意图的任务
3. content 是写作创作，不是分析或文档处理
4. research 侧重信息收集和调查，analysis 侧重数据/业务分析
5. document 是对已有内容的加工处理，不是原创写作
6. planning 是制定计划/方案/决策，不是执行层面的写作
7. 置信度 < 0.5 时选 generic

只返回 JSON，不含任何其他文字：
{
  "task_types": [
    {"type": "标识", "confidence": 0.0到1.0}
  ],
  "complexity": "low|medium|high",
  "intent": "一句话描述核心意图",
  "key_entities": ["关键实体"],
  "language": "zh|en"
}"""


def classify_task(user_input: str) -> dict:
    """对用户输入进行智能分类。"""
    if llm_client.is_available():
        try:
            result = _classify_with_llm(user_input)
            result["source"] = "llm"
            return result
        except Exception as e:
            logger.warning("LLM 分类失败，降级到关键词匹配: %s", e)
    return _classify_with_keywords(user_input)


def _classify_with_llm(user_input: str) -> dict:
    result = llm_client.chat_json(
        prompt=f"分析以下用户需求：\n\n{user_input}",
        system_prompt=CLASSIFIER_SYSTEM_PROMPT,
    )

    valid_types = set(TASK_TYPES.keys())

    if "task_types" not in result or not result["task_types"]:
        raise ValueError("LLM 未返回 task_types")

    # Filter invalid types, keep only known ones
    result["task_types"] = [
        t for t in result["task_types"]
        if t.get("type") in valid_types
    ]

    if not result["task_types"]:
        raise ValueError("LLM 返回的类型全部无效")

    for t in result["task_types"]:
        t["confidence"] = max(0.0, min(1.0, float(t.get("confidence", 0.5))))

    if result.get("complexity") not in ("low", "medium", "high"):
        result["complexity"] = "medium"

    result.setdefault("intent", user_input)
    result.setdefault("key_entities", [])
    result.setdefault("language", "zh")
    return result


def _classify_with_keywords(user_input: str) -> dict:
    text = user_input.lower()
    results = []

    for task_type, keywords in KEYWORDS.items():
        score = 0
        matched = []
        for kw in keywords:
            if kw.lower() in text:
                # Longer keywords = stronger signal
                score += max(len(kw), 2)
                matched.append(kw)

        if score > 0:
            # Normalize: cap at 40 chars of matched keyword length
            confidence = min(score / 40.0, 1.0)
            results.append({
                "type": task_type,
                "confidence": confidence,
                "matched_keywords": matched,
            })

    results.sort(key=lambda x: x["confidence"], reverse=True)

    if not results:
        results = [{"type": "generic", "confidence": 0.3}]

    text_len = len(user_input)
    complexity = "high" if text_len > 80 or len(results) > 3 else "medium" if text_len > 25 else "low"

    is_chinese = any('一' <= c <= '鿿' for c in user_input)

    return {
        "task_types": results,
        "complexity": complexity,
        "intent": user_input[:120],
        "key_entities": [],
        "language": "zh" if is_chinese else "en",
        "source": "fallback",
    }
