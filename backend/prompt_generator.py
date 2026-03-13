"""
提示词生成器 v2
优先使用 LLM 动态生成高质量提示词，不可用时使用增强模板
"""

import logging

import llm_client
from config import MODELS, TASK_TYPES

logger = logging.getLogger(__name__)

# ============================================================
# LLM 生成提示词的元提示（Meta-Prompt）
# ============================================================

GENERATOR_SYSTEM_PROMPT = """你是一位顶级的AI提示词工程师（Prompt Engineer），专门为不同的AI模型设计最优提示词。

你的任务是：根据用户需求和目标AI模型的特点，生成一段高质量的专属提示词。

生成的提示词必须包含以下5个部分：
1. 【角色设定】- 为AI设定一个最适合完成任务的专家角色
2. 【任务描述】- 清晰、具体地描述任务要求
3. 【输出格式】- 明确指定输出的结构和格式
4. 【约束条件】- 列出质量约束和注意事项
5. 【风格要求】- 指定语言风格和表达方式

关键要求：
- 提示词必须是可以直接复制粘贴到目标AI中使用的
- 角色设定要具体、有说服力，不要泛泛而谈
- 任务描述要精准理解用户意图，补充用户可能遗漏的细节
- 输出格式要实用，根据任务类型设计合理的结构
- 约束条件要针对性强，避免通用空话
- 风格要求要匹配目标平台/场景

直接输出提示词文本，不要加任何解释性说明。"""


def generate_prompt(
    user_input: str,
    model_info: dict,
    classification: dict,
) -> str:
    """
    为指定模型生成专属提示词。

    优先使用 LLM 动态生成，不可用时使用增强模板。
    """
    # 提示词始终用模板生成（瞬间完成，质量已经很好）
    # LLM 调用留给分类器，避免 3 次额外 LLM 调用导致整体太慢
    return _generate_with_template(user_input, model_info, classification)


def _generate_with_llm(
    user_input: str, model_info: dict, classification: dict
) -> str:
    """使用 LLM 动态生成提示词"""
    task_types = classification.get("task_types", [])
    primary_type = task_types[0]["type"] if task_types else "writing"
    type_name = TASK_TYPES.get(primary_type, {}).get("name", "综合")
    complexity = classification.get("complexity", "medium")
    intent = classification.get("intent", user_input)

    prompt = f"""请为以下需求生成一段专属于 {model_info['name']} 的高质量提示词。

【用户原始需求】
{user_input}

【需求分析】
- 任务类型：{type_name}
- 复杂度：{complexity}
- 核心意图：{intent}

【目标模型特点】
- 模型：{model_info['name']}（{model_info['provider']}）
- 核心优势：{', '.join(model_info['strengths'][:3])}
- 提示词偏好：{model_info['prompt_tips']}
- 提示风格：{model_info['prompt_style']}

请根据以上信息，生成一段针对 {model_info['name']} 优化的高质量提示词。
要充分利用该模型的优势，提示词风格要匹配该模型的偏好。"""

    return llm_client.chat(prompt, GENERATOR_SYSTEM_PROMPT)


# ============================================================
# 增强模板 Fallback
# ============================================================

ROLE_TEMPLATES = {
    "writing": {
        "structured": "你是一位资深内容策划专家，精通社交媒体传播学和消费者心理学，擅长创作有传播力的爆款内容。请以清晰的结构组织你的创作。",
        "detailed": "你是一位资深内容创作者和叙事专家，拥有丰富的跨平台内容运营经验。你善于深入理解目标受众的心理需求，创作出既有深度、又有感染力的内容。请进行充分的分析和构思后再开始创作。",
        "concise": "你是一位高效的内容创作专家，擅长用精炼的语言传达核心信息，创作直击人心的内容。",
        "step_by_step": "你是一位系统性内容创作专家。请先分析创作目标和受众特征，然后逐步构建内容结构，最后完成创作。",
        "research": "你是一位善于基于真实数据和案例进行内容创作的专家，确保每个观点都有事实支撑。",
    },
    "coding": {
        "structured": "你是一位资深全栈工程师，精通软件架构设计和代码质量管控。请用清晰的结构组织你的代码和说明。",
        "detailed": "你是一位顶级软件工程师，具备深厚的计算机科学功底和丰富的工程实践经验。请对问题进行全面分析，考虑边界情况、性能优化和可维护性，给出生产级别的代码方案。",
        "concise": "你是一位高效的程序员，擅长用简洁优雅的代码解决问题。直接给出可运行的代码方案。",
        "step_by_step": "你是一位注重方法论的软件工程师。请先分析问题本质，然后拆解实现步骤，逐步给出完整的代码方案。每一步都要解释设计考量。",
        "research": "你是一位技术研究型工程师，善于对比不同技术方案的优劣，基于最佳实践给出推荐。",
    },
    "academic": {
        "structured": "你是一位学术研究顾问，精通多个学科的研究方法论，善于以严谨的学术框架组织分析和论述。",
        "detailed": "你是一位资深学术研究者，拥有博士学位和丰富的跨学科研究经历。你熟悉学术规范、研究方法论和批判性思维方法，能够进行全面、深入、严谨的学术分析和写作。请不遗漏任何关键细节。",
        "concise": "你是一位善于提炼核心观点的学术分析师，能用精练的语言传达复杂的学术思想。",
        "step_by_step": "你是一位注重逻辑推导的学术研究者。请从问题定义开始，逐步展开文献回顾、方法选择、分析论证，最终得出结论。",
        "research": "你是一位擅长文献检索和综述的学术研究员，注重引用来源的可靠性和学术论证的严谨性。",
    },
    "business": {
        "structured": "你是一位资深商业分析师和战略顾问，精通商业模型分析、市场研究和战略规划。请以清晰的商业分析框架组织你的输出。",
        "detailed": "你是一位拥有MBA背景的资深战略咨询顾问，有多年的行业咨询经验。请对商业问题进行全面、多维度的深入分析，涵盖市场环境、竞争格局、财务模型等方面，给出具有可操作性的建议。",
        "concise": "你是一位高效的商业分析师，擅长快速抓住商业本质，用数据和事实支撑结论。",
        "step_by_step": "你是一位系统性商业分析专家。请按照「市场分析→竞争分析→商业模型→财务评估→战略建议」的步骤逐层深入分析。",
        "research": "你是一位善于数据驱动决策的商业研究员，注重基于最新市场数据和行业报告得出结论，确保引用来源可靠。",
    },
    "search": {
        "structured": "你是一位专业的信息研究员和事实核查专家，擅长高效检索和整理信息。",
        "detailed": "你是一位资深信息分析师，具备新闻学和数据科学的双重背景。请全面检索相关信息，交叉验证多个来源，提供准确、深入、有层次的信息报告。",
        "concise": "你是一位高效的信息检索专家，擅长快速定位关键信息并给出精准回答。",
        "step_by_step": "你是一位系统性信息研究员。请先明确信息需求，然后逐步检索、验证、整理，最终给出完整的信息报告。",
        "research": "你是一位专注于深度信息挖掘的研究专家，确保每个事实都有可靠来源支撑，提供全面的引用和参考链接。",
    },
    "reasoning": {
        "structured": "你是一位逻辑推理和分析专家，拥有深厚的数学和逻辑学功底，善于以清晰的框架展示推理过程。",
        "detailed": "你是一位顶级的分析推理专家，精通形式逻辑、数学建模和系统性思维。请对问题进行全面的多角度分析，展示完整的推理链条，考虑所有可能的情况和反例。",
        "concise": "你是一位精于逻辑的推理专家，擅长以最简洁的方式展示核心推理过程和结论。",
        "step_by_step": "你是一位严谨的逻辑推理大师。请一步一步地思考这个问题，每一步都要给出清晰的推理依据，最终得出确定的结论。请展示完整的思维过程。",
        "research": "你是一位善于基于已有研究和数据进行推理分析的专家，注重论证的可验证性。",
    },
}

OUTPUT_FORMATS = {
    "writing": """请按以下结构输出：
1. **标题**：引人注目、适合传播的标题
2. **正文**：完整的内容创作，注意段落节奏和可读性
3. **亮点说明**：简要说明创作思路、目标受众和传播策略""",
    "coding": """请按以下结构输出：
1. **思路分析**：简要说明技术选型和实现思路
2. **完整代码**：可直接运行的代码，包含关键注释
3. **使用说明**：如何安装依赖、运行和测试
4. **优化建议**：可能的性能优化或架构改进方向""",
    "academic": """请按以下结构输出：
1. **研究背景**：相关领域的现状和研究意义
2. **核心分析**：详细的分析论证，注意学术严谨性
3. **关键发现**：主要结论和创新点
4. **参考方向**：推荐的相关文献和后续研究方向""",
    "business": """请按以下结构输出：
1. **核心观点**：一句话总结最重要的发现
2. **详细分析**：分维度的深入分析（使用数据和案例支撑）
3. **关键洞察**：3-5个核心发现，每个配简要论证
4. **行动建议**：可直接落地执行的具体建议""",
    "search": """请按以下结构输出：
1. **直接回答**：简明扼要的核心答案
2. **详细说明**：补充背景信息和关键细节
3. **来源说明**：信息的可靠来源（如适用）
4. **延伸阅读**：相关的主题或问题""",
    "reasoning": """请按以下结构输出：
1. **问题理解**：对问题的精确理解和关键条件提取
2. **推理过程**：逐步推理，每步都有明确的逻辑依据
3. **结论**：明确、简洁的最终答案
4. **验证**：对结论进行反向验证或反思""",
}


def _generate_with_template(
    user_input: str, model_info: dict, classification: dict
) -> str:
    """使用增强模板生成提示词"""
    task_types = classification.get("task_types", [])
    primary_type = task_types[0]["type"] if task_types else "writing"
    prompt_style = model_info.get("prompt_style", "structured")

    parts = []

    # 1. 分步骤前缀（DeepSeek风格）
    if prompt_style == "step_by_step":
        parts.append("请你一步一步地思考这个问题。\n")

    # 2. 角色设定（按模型风格 + 任务类型选择）
    role_group = ROLE_TEMPLATES.get(primary_type, ROLE_TEMPLATES["writing"])
    role = role_group.get(prompt_style, role_group["structured"])
    parts.append(f"【角色设定】\n{role}")

    # 3. 任务描述
    type_names = []
    for t in task_types[:2]:
        info = TASK_TYPES.get(t["type"])
        if info:
            type_names.append(info["name"])
    type_str = "和".join(type_names) if type_names else "综合"

    intent = classification.get("intent", user_input)
    entities = classification.get("key_entities", [])
    entity_str = f"\n关键要素：{', '.join(entities)}" if entities else ""

    parts.append(
        f"\n【任务描述】\n"
        f"请完成以下{type_str}相关任务：\n\n"
        f"{user_input}\n"
        f"{entity_str}\n\n"
        f"核心意图：{intent}\n"
        f"请充分理解上述需求的核心意图，提供高质量、可直接使用的输出。"
    )

    # 4. 输出格式
    output_fmt = OUTPUT_FORMATS.get(primary_type, OUTPUT_FORMATS["writing"])
    parts.append(f"\n【输出格式】\n{output_fmt}")

    # 5. 约束条件
    constraints = _build_constraints(primary_type, prompt_style)
    parts.append(f"\n【约束条件】\n{constraints}")

    # 6. 风格要求
    style = _get_style_text(prompt_style)
    parts.append(f"\n【风格要求】\n{style}")

    return "\n".join(parts)


def _build_constraints(primary_type: str, prompt_style: str) -> str:
    """构建约束条件"""
    base = [
        "内容必须原创，确保信息准确性",
        "如有不确定之处，请明确指出而非杜撰",
    ]

    style_constraints = {
        "structured": "请确保回答结构清晰、条理分明，使用标题和列表组织内容",
        "detailed": "请进行全面深入的分析，不遗漏关键细节，论述要完整",
        "concise": "请直奔主题，高效输出，避免冗余信息",
        "step_by_step": "请展示完整的思考过程，每一步都要有清晰的推理依据",
        "research": "请注重信息来源的可靠性，尽量提供引用和参考",
    }
    base.append(style_constraints.get(prompt_style, style_constraints["structured"]))

    type_constraints = {
        "writing": ["注意目标受众的阅读习惯和平台调性", "内容要有传播价值和情感共鸣"],
        "coding": ["代码需要有良好的错误处理和边界检查", "遵循行业最佳实践和编码规范"],
        "academic": ["严格遵循学术规范和引用格式", "区分事实陈述和主观观点"],
        "business": ["用数据和案例支撑分析", "建议需具备可操作性和商业可行性"],
        "search": ["优先提供最新、最权威的信息", "标注信息来源和时效性"],
        "reasoning": ["每一步推理都要有明确的逻辑依据", "注意检验结论的合理性和完备性"],
    }
    base.extend(type_constraints.get(primary_type, []))

    return "\n".join(f"- {c}" for c in base)


def _get_style_text(prompt_style: str) -> str:
    """获取风格描述"""
    styles = {
        "structured": "使用专业但易懂的语言，平衡深度与可读性。善用 Markdown 格式、标题和列表来组织内容。",
        "detailed": "使用严谨、专业的语言，注重逻辑连贯性和论述完整性。给出充分的背景信息和详尽的分析。",
        "concise": "使用简洁明了的语言，重点突出，层次分明。避免废话，每句话都有信息量。",
        "step_by_step": "使用逻辑清晰、层层递进的方式组织回答。明确标注每个步骤，展示推理链条。",
        "research": "使用客观、中立的研究性语言。注重事实和数据，标注来源和引用。",
    }
    return styles.get(prompt_style, styles["structured"])
