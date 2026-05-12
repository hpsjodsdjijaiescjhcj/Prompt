from __future__ import annotations

from copy import deepcopy

# label -> schema field packs (generic, enterprise-oriented)
LABEL_FIELD_PACKS = {
    "analysis": [
        {
            "key": "analysis_scope",
            "label": "分析范围（必填）",
            "type": "multiline_text",
            "required": True,
            "placeholder": "明确分析对象、时间范围、地域范围、对比基线。",
            "help_text": "例如：2024-2026 中国高校 CS 就业，重点对比 985/211。",
        },
        {
            "key": "evidence_preference",
            "label": "证据偏好",
            "type": "single_choice",
            "required": True,
            "default": "mixed",
            "options": [
                {"value": "data_first", "label": "数据优先"},
                {"value": "paper_first", "label": "论文/报告优先"},
                {"value": "mixed", "label": "综合"},
            ],
        },
    ],
    "research": [
        {
            "key": "source_requirements",
            "label": "来源要求（必填）",
            "type": "multiline_text",
            "required": True,
            "placeholder": "一行一条：允许来源、禁止来源、时间新鲜度。",
            "help_text": "例如：优先官方站点和顶会官网，近12个月优先。",
        },
        {
            "key": "citation_required",
            "label": "是否需要引用",
            "type": "boolean",
            "required": True,
            "default": True,
            "true_label": "需要",
            "false_label": "不需要",
        },
    ],
    "writing": [
        {
            "key": "voice_and_style",
            "label": "语言风格要求（必填）",
            "type": "multiline_text",
            "required": True,
            "placeholder": "例如：专业但通俗、避免AI腔、句长控制。",
        },
        {
            "key": "structure_expectation",
            "label": "结构要求",
            "type": "multiline_text",
            "required": False,
            "placeholder": "例如：先结论后论据、3段式、每段不超120字。",
        },
    ],
    "email": [
        {
            "key": "recipient_identity",
            "label": "收件人身份（必填）",
            "type": "short_text",
            "required": True,
            "placeholder": "例如：供应商财务经理 / 客户采购负责人",
        },
        {
            "key": "desired_action",
            "label": "希望对方执行的动作（必填）",
            "type": "multiline_text",
            "required": True,
            "placeholder": "明确动作、截止时间、回执方式。",
        },
    ],
    "code": [
        {
            "key": "delivery_artifact",
            "label": "交付形式（必填）",
            "type": "single_choice",
            "required": True,
            "default": "patch",
            "options": [
                {"value": "patch", "label": "统一 diff/patch"},
                {"value": "file_changes", "label": "文件级变更清单"},
                {"value": "plan_only", "label": "实施方案"},
            ],
        },
        {
            "key": "verification_plan",
            "label": "验证方案（必填）",
            "type": "multiline_text",
            "required": True,
            "placeholder": "列出测试、lint、回归检查。",
        },
    ],
}


def inject_label_field_packs(schema: dict, labels: list[str] | None) -> dict:
    labels = labels or []
    if not schema or not isinstance(schema, dict):
        return schema

    fields = list(schema.get("fields") or [])
    existing_keys = {f.get("key") for f in fields if f.get("key")}
    injected = []
    for label in labels:
        for field in LABEL_FIELD_PACKS.get(str(label).strip().lower(), []):
            key = field.get("key")
            if key and key not in existing_keys:
                injected.append(deepcopy(field))
                existing_keys.add(key)

    if not injected:
        return schema

    enriched = {
        **schema,
        "description": (schema.get("description", "") + "\n已启用标签驱动字段，请补全对应结构化要素。").strip(),
        "fields": fields + injected,
        "label_field_pack_enabled": True,
        "label_field_pack_count": len(injected),
    }
    return enriched


def build_execution_contract(task_type: str, labels: list[str] | None, schema: dict | None = None) -> dict:
    labels = [str(x).strip().lower() for x in (labels or []) if str(x).strip()]
    required_keys = []
    if schema:
        for f in schema.get("fields") or []:
            required_now = bool(f.get("required"))
            if required_now and f.get("key"):
                required_keys.append(f["key"])

    contract = {
        "contract_version": "1.0",
        "task_type": task_type,
        "labels": labels,
        "input_requirements": {
            "required_keys": sorted(set(required_keys)),
            "forbidden_empty_sections": ["objective", "constraints", "output_format"],
        },
        "execution_requirements": {
            "must_follow_acceptance_criteria": True,
            "must_preserve_hard_constraints": True,
            "must_return_structured_output": True,
        },
        "validation_requirements": {
            "schema_validation": True,
            "constraint_validation": True,
            "goal_validation": True,
        },
    }
    return contract


def render_contract_prefix(contract: dict) -> str:
    req_keys = contract.get("input_requirements", {}).get("required_keys") or []
    labels = contract.get("labels") or []
    return (
        "[EXECUTION CONTRACT]\n"
        f"contract_version: {contract.get('contract_version')}\n"
        f"task_type: {contract.get('task_type')}\n"
        f"labels: {labels}\n"
        f"required_input_keys: {req_keys}\n"
        "requirements:\n"
        "- must_follow_acceptance_criteria: true\n"
        "- must_preserve_hard_constraints: true\n"
        "- must_return_structured_output: true\n"
        "- validate(schema/constraints/goal): true\n"
        "[/EXECUTION CONTRACT]\n\n"
    )
