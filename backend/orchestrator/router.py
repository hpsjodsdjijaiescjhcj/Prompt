from __future__ import annotations

import llm_client
from classifier import classify_task

from .code_handler import CodeTaskHandler
from .email_handler import EmailTaskHandler
from .generic_handler import GenericTaskHandler
from .ml_extractor import predict_task_type
from .writing_handler import WritingTaskHandler


# ── Handler instances ──────────────────────────────────────────
EMAIL_HANDLER   = EmailTaskHandler()
CODE_HANDLER    = CodeTaskHandler()
WRITING_HANDLER = WritingTaskHandler()   # covers "content" type
GENERIC_HANDLER = GenericTaskHandler()  # covers research/analysis/document/planning/generic

HANDLERS = [EMAIL_HANDLER, CODE_HANDLER, WRITING_HANDLER, GENERIC_HANDLER]

# ── Canonical task types recognized by the orchestrator ───────
VALID_TASK_TYPES = {"email", "code", "content", "research", "analysis", "document", "planning", "generic", "other"}

# ── Types that map to a specialized handler ───────────────────
_TYPE_TO_HANDLER = {
    "email":    EMAIL_HANDLER,
    "code":     CODE_HANDLER,
    "content":  WRITING_HANDLER,  # content creation → writing handler
}

# ── Types that fall through to generic handler ─────────────────
_GENERIC_TYPES = {"research", "analysis", "document", "planning", "generic"}

# ── Old classifier type → new orchestrator type (for fallback) ─
_LEGACY_MAP = {
    "writing":   "content",
    "coding":    "code",
    "academic":  "research",
    "business":  "analysis",
    "search":    "research",
    "reasoning": "analysis",
}

ROUTER_SYSTEM_PROMPT = """你是任务路由器。将用户请求精确路由到以下类型之一：

- email:    商务邮件、通知、回复、催办、邀请函（必须有明确的"写邮件"意图）
- code:     代码编写、调试、重构、架构设计、代码审查
- content:  文章、文案、营销内容、创意写作（原创写作，非分析）
- research: 市场调研、竞品分析、信息检索、行业研究
- analysis: 数据解读、业务分析、财务分析、运营诊断
- document: 文档总结、内容提取、格式整理、会议纪要（加工已有内容）
- planning: 项目规划、战略制定、方案设计、决策分析
- generic:  其他无法明确归类的任务
- other:    明确不需要编排的简单问答（谨慎使用）

规则：
1. 信息不足或边界模糊时，选最接近的具体类型，不要选 generic 或 other。
2. 只有明确判断无需编排（如纯闲聊、单句问答）时才选 other。
3. "写邮件"≠content，必须路由到 email。
4. "总结这篇文章"≠content，路由到 document。

严格返回 JSON：
{
  "task_type": "email|code|content|research|analysis|document|planning|generic|other",
  "confidence": 0.0到1.0,
  "reason": "一句简短理由"
}
不要输出 JSON 以外的内容。"""


def route_task(text: str):
    """
    Route text to (task_type, handler, confidence).

    Priority:
    1. Local ML model (if confident enough)
    2. LLM semantic routing
    3. Keyword classifier fallback
    """
    # ── 1. Local ML model (fast, no network) ──────────────────
    ml_pred = predict_task_type(text)
    if ml_pred and ml_pred.confidence >= 0.65:
        normalized = _normalize_type(ml_pred.task_type)
        handler    = _pick_handler(normalized)
        if handler:
            return normalized, handler, ml_pred.confidence

    # ── 2. Get classifier context ──────────────────────────────
    cls = classify_task(text)

    # ── 3. LLM semantic routing (primary) ─────────────────────
    llm_route = _route_with_llm(text, cls)
    if llm_route:
        task_type, conf = llm_route
        handler = _pick_handler(task_type)
        if handler:
            return task_type, handler, conf
        return "other", None, conf

    # ── 4. Keyword classifier fallback ────────────────────────
    return _fallback_route(cls, text)


def get_handler(task_type: str):
    return _pick_handler(task_type)


# ── Internal helpers ───────────────────────────────────────────

def _normalize_type(raw: str) -> str:
    """Map legacy or invalid type names to canonical ones."""
    if raw in VALID_TASK_TYPES:
        return raw
    return _LEGACY_MAP.get(raw, "generic")


def _pick_handler(task_type: str):
    if task_type in _TYPE_TO_HANDLER:
        return _TYPE_TO_HANDLER[task_type]
    if task_type in _GENERIC_TYPES:
        return GENERIC_HANDLER
    return None


def _route_with_llm(text: str, classification: dict):
    if not llm_client.is_available():
        return None

    try:
        result = llm_client.chat_json(
            prompt=(
                f"请根据用户请求和分类上下文做路由。\n\n"
                f"用户请求：{text}\n\n"
                f"分类参考：{classification}"
            ),
            system_prompt=ROUTER_SYSTEM_PROMPT,
        )

        raw_type   = str(result.get("task_type", "")).strip().lower()
        confidence = float(result.get("confidence", 0.0) or 0.0)
        confidence = max(0.0, min(1.0, confidence))

        task_type = _normalize_type(raw_type)

        if task_type == "other" and confidence < 0.2:
            return "generic", 0.3

        if task_type not in VALID_TASK_TYPES:
            return "generic", 0.3

        if task_type not in ("other", "generic") and confidence < 0.2:
            return "generic", 0.3

        return task_type, max(confidence, 0.3)
    except Exception:
        return None


def _fallback_route(cls: dict, text: str) -> tuple:
    """Keyword-classifier-based fallback routing."""
    task_types = cls.get("task_types") or []
    if not task_types:
        return "generic", GENERIC_HANDLER, 0.25

    top  = task_types[0]
    raw  = top.get("type", "generic")
    conf = float(top.get("confidence", 0.0) or 0.0)

    task_type = _normalize_type(raw)

    if task_type == "email":
        email_conf = EMAIL_HANDLER.detect(text)
        if email_conf >= 0.35:
            return "email", EMAIL_HANDLER, max(conf, email_conf)
        task_type = "content" if conf >= 0.3 else "generic"

    if task_type == "code":
        if conf >= 0.25:
            return "code", CODE_HANDLER, conf
        task_type = "generic"

    if task_type == "content":
        writing_conf = WRITING_HANDLER.detect(text)
        if writing_conf >= 0.3 or conf >= 0.3:
            return "content", WRITING_HANDLER, max(conf, writing_conf)
        task_type = "generic"

    handler = _pick_handler(task_type) or GENERIC_HANDLER
    return task_type, handler, max(conf, 0.25)
