"""
模型推荐引擎 v2
多维度评分：能力匹配 × 复杂度适配 × 成本效益
"""

from config import COMPLEXITY_WEIGHTS, MODELS, TASK_TYPES


def recommend_models(classification: dict, top_n: int = 3) -> list[dict]:
    """
    根据分类结果推荐最适合的模型。

    Args:
        classification: classifier.classify_task 的输出（新版统一 dict 格式）
        top_n: 推荐数量

    Returns:
        推荐模型列表，包含模型信息、匹配度和推荐理由
    """
    task_types = classification["task_types"]
    complexity = classification.get("complexity", "medium")
    intent = classification.get("intent", "")
    weights = COMPLEXITY_WEIGHTS.get(complexity, COMPLEXITY_WEIGHTS["medium"])

    scored_models = []

    for model_key, model in MODELS.items():
        # 1. 能力得分：按任务类型加权
        ability_score = _calc_ability_score(model, task_types)

        # 2. 成本得分：成本越低越好（反转）
        cost_score = (11 - model["cost"]) / 10.0  # 归一化到 0-1

        # 3. 速度得分
        speed_score = model["speed"] / 10.0

        # 4. 特色匹配加分
        bonus = _calc_bonus(model, task_types, complexity)

        # 综合得分
        final_score = (
            ability_score * weights["ability_weight"]
            + cost_score * weights["cost_weight"]
            + speed_score * weights["speed_weight"]
            + bonus
        )

        # 匹配度百分比（0-100）
        match_pct = min(round(final_score * 100), 99)

        scored_models.append({
            "model_key": model_key,
            "final_score": final_score,
            "ability_score": ability_score,
            "match_pct": match_pct,
        })

    # 按综合得分排序
    scored_models.sort(key=lambda x: x["final_score"], reverse=True)

    # 构建推荐结果
    recommendations = []
    for i, item in enumerate(scored_models[:top_n]):
        model = MODELS[item["model_key"]]
        reason = _generate_reason(model, task_types, complexity, intent, i)

        recommendations.append({
            "model_key": item["model_key"],
            "name": model["name"],
            "provider": model["provider"],
            "icon": model["icon"],
            "color": model["color"],
            "description": model["description"],
            "strengths": model["strengths"],
            "weaknesses": model["weaknesses"],
            "best_for": model["best_for"],
            "prompt_tips": model["prompt_tips"],
            "reason": reason,
            "match_pct": item["match_pct"],
            "scores": model["scores"],
            "cost": model["cost"],
            "speed": model["speed"],
            "context_window": model["context_window"],
            "prompt_style": model["prompt_style"],
        })

    return recommendations


def _calc_ability_score(model: dict, task_types: list[dict]) -> float:
    """计算能力匹配得分（0-1）"""
    if not task_types:
        return 0.5

    total_confidence = sum(t.get("confidence", 0.5) for t in task_types)
    if total_confidence == 0:
        total_confidence = 1

    weighted_sum = 0
    for t in task_types:
        task_type = t["type"]
        confidence = t.get("confidence", 0.5)
        ability = model["scores"].get(task_type, 5)
        weighted_sum += (ability / 10.0) * (confidence / total_confidence)

    return weighted_sum


def _calc_bonus(model: dict, task_types: list[dict], complexity: str) -> float:
    """计算特色匹配加分"""
    bonus = 0.0
    primary_type = task_types[0]["type"] if task_types else "writing"

    # 如果模型在主任务上有 10 分满分能力，额外加分
    if model["scores"].get(primary_type, 0) == 10:
        bonus += 0.05

    # 高复杂度任务中，推理能力强的模型加分
    if complexity == "high" and model["scores"].get("reasoning", 0) >= 9:
        bonus += 0.03

    # 如果任务涉及搜索且模型搜索能力强
    search_types = [t for t in task_types if t["type"] == "search"]
    if search_types and model["scores"].get("search", 0) >= 9:
        bonus += 0.04

    return bonus


def _generate_reason(
    model: dict, task_types: list[dict], complexity: str, intent: str, rank: int
) -> str:
    """生成自然语言推荐理由"""
    primary = task_types[0] if task_types else {"type": "writing", "confidence": 0.5}
    primary_type = primary["type"]
    type_name = TASK_TYPES.get(primary_type, {}).get("name", "综合")
    primary_score = model["scores"].get(primary_type, 5)

    parts = []

    # 主能力评价
    if primary_score >= 9:
        parts.append(f"在{type_name}领域表现顶尖（{primary_score}/10）")
    elif primary_score >= 7:
        parts.append(f"在{type_name}领域能力出色（{primary_score}/10）")
    else:
        parts.append(f"在{type_name}领域可胜任（{primary_score}/10）")

    # 核心优势
    top_strengths = model["strengths"][:2]
    parts.append(f"核心优势：{'、'.join(top_strengths)}")

    # 多类型适配
    if len(task_types) > 1:
        sec = task_types[1]
        sec_name = TASK_TYPES.get(sec["type"], {}).get("name", "")
        sec_score = model["scores"].get(sec["type"], 5)
        if sec_score >= 8:
            parts.append(f"同时擅长{sec_name}（{sec_score}/10）")

    # 复杂度适配
    if complexity == "high":
        reasoning = model["scores"].get("reasoning", 5)
        if reasoning >= 9:
            parts.append("深度推理能力强，适合复杂任务")

    # 成本提示
    if model["cost"] <= 3:
        parts.append("性价比极高")
    elif model["cost"] >= 8:
        parts.append("综合能力最强，适合高质量需求")

    return "；".join(parts)
