from __future__ import annotations

import re

from .base import TaskHandler


class GenericTaskHandler(TaskHandler):
    task_type = "generic"

    def detect(self, text: str) -> float:
        # Generic is fallback; detect score is not used for primary routing.
        return 0.1

    def clarify_schema(self, text: str) -> dict:
        fields = [
            {
                "key": "task_domain",
                "label": "任务大类",
                "type": "single_choice",
                "required": True,
                "default": "analysis",
                "options": [
                    {"value": "analysis", "label": "分析/决策"},
                    {"value": "research", "label": "调研/信息整合"},
                    {"value": "writing", "label": "写作/表达"},
                    {"value": "planning", "label": "规划/方案"},
                    {"value": "other", "label": "其他"},
                ],
            },
            {
                "key": "task_domain_other",
                "label": "请补充任务大类",
                "type": "short_text",
                "required": False,
                "required_when": {"task_domain": "other"},
                "show_when": {"task_domain": "other"},
                "placeholder": "例如：法律文书审阅、访谈提纲设计",
            },
            {
                "key": "target_audience",
                "label": "结果是给谁看的（可选）",
                "type": "short_text",
                "required": False,
                "placeholder": "例如：老板、客户、团队内部",
            },
            {
                "key": "expected_output_type",
                "label": "你希望的输出形式",
                "type": "single_choice",
                "required": True,
                "default": "structured",
                "options": [
                    {"value": "structured", "label": "结构化结论"},
                    {"value": "step_by_step", "label": "分步骤方案"},
                    {"value": "comparison", "label": "对比表格"},
                    {"value": "checklist", "label": "清单"},
                    {"value": "other", "label": "其他"},
                ],
            },
            {
                "key": "expected_output_type_other",
                "label": "请补充输出形式",
                "type": "short_text",
                "required": False,
                "required_when": {"expected_output_type": "other"},
                "show_when": {"expected_output_type": "other"},
                "placeholder": "例如：一页汇报稿、演讲提纲、流程图说明",
            },
            {
                "key": "background",
                "label": "补充信息（可选）",
                "type": "multiline_text",
                "required": False,
                "placeholder": "补充已知事实、现状、约束条件、可用资料。",
            },
        ]

        if _looks_like_weather_query(text):
            fields = [
                {
                    "key": "location",
                    "label": "地点（必填）",
                    "type": "short_text",
                    "required": True,
                    "placeholder": "例如：纽约、上海、San Francisco",
                    "help_text": "天气类任务必须有地点。",
                },
                {
                    "key": "time_range",
                    "label": "时间范围（必填）",
                    "type": "single_choice",
                    "required": True,
                    "default": "today",
                    "options": [
                        {"value": "today", "label": "今天"},
                        {"value": "tomorrow", "label": "明天"},
                        {"value": "next_3_days", "label": "最近三天"},
                        {"value": "next_7_days", "label": "最近七天"},
                        {"value": "custom", "label": "自定义"},
                    ],
                },
                {
                    "key": "time_range_custom",
                    "label": "自定义时间范围",
                    "type": "short_text",
                    "required": False,
                    "required_when": {"time_range": "custom"},
                    "show_when": {"time_range": "custom"},
                    "placeholder": "例如：下周一到下周五",
                },
                {
                    "key": "weather_focus",
                    "label": "重点关注（可选）",
                    "type": "multi_choice",
                    "required": False,
                    "options": [
                        {"value": "temperature", "label": "温度"},
                        {"value": "rain", "label": "降雨"},
                        {"value": "wind", "label": "风力"},
                        {"value": "air_quality", "label": "空气质量"},
                    ],
                },
                {
                    "key": "unit",
                    "label": "温度单位",
                    "type": "single_choice",
                    "required": True,
                    "default": "c",
                    "options": [
                        {"value": "c", "label": "摄氏度"},
                        {"value": "f", "label": "华氏度"},
                    ],
                },
            ] + fields

        return {
            "title": "通用任务澄清",
            "description": "你的需求目前还不够具体。先补齐目标、边界和输出形式，再进入执行。",
            "fields": fields,
        }

    def build_spec(self, text: str, answers: dict) -> dict:
        clarified_request = (answers.get("clarified_request") or "").strip()
        success_criteria = _lines_to_list(answers.get("success_criteria", ""))
        hard_constraints = _lines_to_list(answers.get("hard_constraints", ""))
        output_preference = answers.get("output_preference", "direct")
        intent_frame = _build_intent_frame(answers)

        domain = answers.get("task_domain", "analysis")
        domain_other = (answers.get("task_domain_other") or "").strip()
        output_type = answers.get("expected_output_type", "structured")
        output_type_other = (answers.get("expected_output_type_other") or "").strip()

        acceptance = _build_default_acceptance(
            output_type=output_type_other or output_type,
            audience=answers.get("target_audience", ""),
        )
        acceptance = _merge_list_unique(acceptance, success_criteria)

        objective = clarified_request or text
        domain_value = domain_other or domain
        weather_context = {}
        if answers.get("location"):
            weather_context = {
                "location": answers.get("location", ""),
                "time_range": answers.get("time_range_custom") or answers.get("time_range", ""),
                "weather_focus": answers.get("weather_focus", []),
                "unit": answers.get("unit", "c"),
            }
            objective = f"{text}（地点：{weather_context['location']}；时间：{weather_context['time_range']}）"
            domain_value = "weather_query"

        return {
            "task_type": "generic",
            "objective": objective,
            "original_request": text,
            "domain": domain_value,
            "audience": {"target": answers.get("target_audience", "")},
            "constraints": {
                "hard_constraints": hard_constraints,
                "output_preference": output_preference,
            },
            "must_include": [],
            "must_avoid": [],
            "context": {
                "background": answers.get("background", ""),
                "weather": weather_context,
                "intent_frame": intent_frame,
            },
            "output_format": {
                "type": output_type_other or output_type,
            },
            "acceptance_criteria": acceptance,
        }

    def prompts(self, spec: dict, route: dict) -> list[dict]:
        prompt = _render_generic_prompt(spec)
        rows = []
        for ex in route.get("recommended_executors", []):
            rows.append({
                "executor": ex,
                "prompt": prompt,
                "notes": "通用任务提示词。先保证目标对齐，再给最终结果。",
            })
        return rows

    def validate(self, spec: dict, output: str) -> dict:
        issues = []
        if not output.strip():
            issues.append({"type": "empty_output", "message": "没有返回内容。"})
        return {
            "pass": len(issues) == 0,
            "issues": issues,
            "suggested_fix_prompt": "请基于 spec 重新输出，确保覆盖目标与验收标准。" if issues else "",
        }


def _render_generic_prompt(spec: dict) -> str:
    weather = (spec.get("context") or {}).get("weather") or {}
    criteria = "\n".join(f"- {x}" for x in (spec.get("acceptance_criteria") or [])) or "- (无)"
    hard_constraints = "\n".join(
        f"- {x}" for x in ((spec.get("constraints") or {}).get("hard_constraints") or [])
    ) or "- (无)"
    output_pref = (spec.get("constraints") or {}).get("output_preference", "direct")
    output_type = (spec.get("output_format") or {}).get("type", "structured")
    intent = ((spec.get("context") or {}).get("intent_frame") or {})
    intent_lines = []
    if intent.get("motivation"):
        intent_lines.append(f"- 前因/目的：{intent.get('motivation')}")
    if intent.get("primary_target"):
        intent_lines.append(f"- 主要作用对象：{intent.get('primary_target')}")
    if intent.get("stakeholders"):
        intent_lines.append(f"- 相关对象：{intent.get('stakeholders')}")
    if intent.get("style_modifiers"):
        intent_lines.append(f"- 风格修饰词：{', '.join(intent.get('style_modifiers') or [])}")
    intent_block = "\n".join(intent_lines) or "- (未提供)"

    workflow_hint = {
        "direct": "直接给最终结果，不先写分析过程。",
        "outline_then_final": "先给简短提纲，再给最终结果。",
        "options_then_pick": "先给 2-3 个方案，再展开你认为最优的一个。",
    }.get(output_pref, "直接给最终结果。")

    normalized_goal = _rewrite_goal(
        objective=(spec.get("objective") or "").strip(),
        domain=(spec.get("domain") or "").strip(),
        audience=((spec.get("audience") or {}).get("target") or "").strip(),
        output_type=(spec.get("output_format") or {}).get("type", "structured"),
    )
    output_contract = _build_output_contract(
        domain=(spec.get("domain") or "").strip(),
        output_type=(spec.get("output_format") or {}).get("type", "structured"),
        weather=weather,
    )
    context_lines = [f"- 背景：{(spec.get('context') or {}).get('background', '') or '未提供'}"]
    if weather:
        focus = weather.get("weather_focus") or []
        focus_text = ", ".join(focus) if focus else "默认关键指标"
        context_lines.extend(
            [
                f"- 地点：{weather.get('location', '') or '未提供'}",
                f"- 时间范围：{weather.get('time_range', '') or '未提供'}",
                f"- 重点指标：{focus_text}",
                f"- 单位偏好：{weather.get('unit', 'c')}",
            ]
        )
    context_block = "\n".join(context_lines)

    return (
        "你是资深任务执行顾问。请基于下述规范，输出高质量、可直接使用的结果。\n\n"
        "【任务目标】\n"
        f"- 原始请求：{spec.get('original_request', '')}\n"
        f"- 规范化目标：{normalized_goal}\n"
        f"- 任务大类：{spec.get('domain', '')}\n"
        f"- 受众：{(spec.get('audience') or {}).get('target', '') or '通用读者'}\n\n"
        "【上下文】\n"
        f"{intent_block}\n"
        f"{context_block}\n\n"
        "【执行约束】\n"
        f"{hard_constraints}\n"
        "【输出结构】\n"
        f"{output_contract}\n\n"
        "【输出要求】\n"
        f"- 输出形式：{output_type}\n"
        f"- 输出策略：{workflow_hint}\n"
        f"- 验收标准：\n{criteria}\n\n"
        "请严格按要求作答，避免空话，确保信息完整且可执行。"
    )


def _lines_to_list(text: str) -> list[str]:
    lines = []
    for raw in (text or "").splitlines():
        s = raw.strip().lstrip("-*0123456789. ")
        if s:
            lines.append(s)
    return lines


def _merge_list_unique(base: list[str], extra: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in (base or []) + (extra or []):
        s = (item or "").strip()
        if s and s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _build_intent_frame(answers: dict) -> dict:
    return {
        "motivation": (answers.get("motivation") or "").strip(),
        "primary_target": (answers.get("primary_target") or "").strip(),
        "stakeholders": (answers.get("stakeholders") or "").strip(),
        "style_modifiers": _lines_to_list(answers.get("style_modifiers", "")),
    }


def _looks_like_weather_query(text: str) -> bool:
    t = (text or "").lower()
    weather_words = ["天气", "气温", "降雨", "wind", "temperature", "forecast", "weather"]
    return any(w in t for w in weather_words)


def _rewrite_goal(objective: str, domain: str, audience: str, output_type: str) -> str:
    obj = (objective or "").strip()
    if not obj:
        obj = "围绕用户请求完成可执行交付"
    domain_label = domain or "analysis"
    audience_label = audience or "通用读者"
    style_label = {
        "structured": "结构化结论",
        "step_by_step": "分步骤方案",
        "comparison": "对比结论",
        "checklist": "执行清单",
    }.get(output_type, output_type or "结构化输出")
    return f"围绕「{obj}」，输出面向「{audience_label}」的「{domain_label}」结果，并以「{style_label}」交付。"


def _build_output_contract(domain: str, output_type: str, weather: dict) -> str:
    # 通用合同，不绑定某个具体任务，按输出类型与上下文动态构建。
    sections = []
    if output_type == "step_by_step":
        sections = ["1) 目标定义", "2) 关键步骤", "3) 每步产出", "4) 风险与替代方案", "5) 下一步行动"]
    elif output_type == "comparison":
        sections = ["1) 比较维度", "2) 方案A/B要点", "3) 差异总结", "4) 选择建议"]
    elif output_type == "checklist":
        sections = ["1) 执行清单", "2) 验收点", "3) 常见风险与规避"]
    else:
        sections = ["1) 核心结论", "2) 关键依据", "3) 可执行建议", "4) 风险与边界"]

    if weather:
        sections.insert(1, "2) 时空参数说明（地点/时间范围/指标）")

    if domain and domain not in {"analysis", "research", "writing", "planning", "weather_query"}:
        sections.append(f"补充：结合任务域「{domain}」给出专属建议")

    return "\n".join(f"- {row}" for row in sections)


def _build_default_acceptance(output_type: str, audience: str) -> list[str]:
    base = [
        "结果应准确回应用户目标。",
        "结构清晰，可直接使用。",
        "符合硬性约束。",
    ]
    audience_text = (audience or "").strip()
    if audience_text:
        base.append(f"表达应匹配目标受众（{audience_text}）的理解成本。")
    if output_type == "comparison":
        base.append("比较维度需一致，结论需可追溯。")
    elif output_type == "step_by_step":
        base.append("步骤之间应有前后依赖关系，且每步可执行。")
    elif output_type == "checklist":
        base.append("清单项需可核对、可勾选。")
    return base
