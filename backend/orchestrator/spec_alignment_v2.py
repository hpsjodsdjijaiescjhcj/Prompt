"""
Specification Alignment Layer v2 - Semantic Rewriting & Mapping

Core principle: Transform user intent into structured execution contract.
- Semantic rewriting: rephrase for clarity without changing meaning
- Complete mapping: all clarification fields → spec fields
- Professional standardization: consistent terminology
"""

from typing import Dict, Any, List
from orchestrator.domain_model import (
    TaskSession, TaskSpecification, ClarificationAnswers, WorkflowState
)


class SpecificationBuilder:
    """Build structured task specification from user input + clarifications."""
    
    @staticmethod
    def build_spec(session: TaskSession) -> TaskSpecification:
        """
        Build complete task specification.
        
        Maps all user input + clarification answers into structured spec.
        """
        user_input = session.user_input
        clarification = session.clarification_answers or ClarificationAnswers()
        all_answers = clarification.all_answers()
        
        # Extract core fields based on domain
        objective = SpecificationBuilder._build_objective(
            session.domain, user_input.text, all_answers
        )
        
        context = SpecificationBuilder._build_context(
            session.domain, user_input.text, all_answers
        )
        
        constraints = SpecificationBuilder._build_constraints(
            session.domain, user_input.text, all_answers
        )
        
        output_format = SpecificationBuilder._build_output_format(
            session.domain, user_input.text, all_answers
        )
        
        acceptance_criteria = SpecificationBuilder._build_acceptance_criteria(
            session.domain, user_input.text, all_answers
        )
        
        spec = TaskSpecification(
            domain=session.domain,
            objective=objective,
            context=context,
            constraints=constraints,
            output_format=output_format,
            acceptance_criteria=acceptance_criteria,
        )
        
        return spec
    
    @staticmethod
    def _build_objective(domain, user_text: str, answers: Dict[str, Any]) -> str:
        """
        Build objective statement.
        
        Semantic rewrite of user intent with professional phrasing.
        """
        explicit_objective = answers.get("objective")
        objective = (explicit_objective or user_text).strip()

        if answers.get("target_object"):
            objective = f"围绕“{answers['target_object']}”完成：{objective}"

        if "communication_goal" in answers:
            goal_map = {
                "inform": "通知并确保理解",
                "request": "请求并获得响应",
                "negotiate": "协商达成共识",
                "apologize": "道歉并修复关系",
                "persuade": "说服并获得同意",
            }
            goal = answers["communication_goal"]
            if goal in goal_map:
                objective = f"{objective}（沟通目标：{goal_map[goal]}）"

        elif "content_type" in answers:
            type_map = {
                "article": "撰写文章",
                "social": "创作社交媒体内容",
                "marketing": "编写营销文案",
                "technical": "编写技术文档",
                "creative": "创作创意内容",
            }
            ctype = answers["content_type"]
            if ctype in type_map:
                objective = f"{type_map[ctype]}：{objective}"

        elif "tech_category" in answers:
            tech_map = {
                "code": "编写代码",
                "architecture": "设计架构",
                "debugging": "排查问题",
                "optimization": "优化性能",
                "documentation": "编写文档",
            }
            tcat = answers["tech_category"]
            if tcat in tech_map:
                objective = f"{tech_map[tcat]}：{objective}"

        elif "optimization_goal" in answers:
            objective = f"优化“{answers['optimization_goal']}”：{objective}"

        elif "strategic_context" in answers:
            objective = f"基于战略背景“{answers['strategic_context']}”完成：{objective}"

        elif "compliance_type" in answers:
            objective = f"完成{answers['compliance_type']}相关任务：{objective}"

        return objective
    
    @staticmethod
    def _build_context(domain, user_text: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build context dictionary.
        
        Background, stakeholders, motivation, constraints.
        """
        context = {
            "original_input": user_text,
            "domain": domain.value,
        }

        generic_context_fields = [
            "objective",
            "background",
            "target_object",
            "recipient",
            "target_audience",
            "tech_stack",
            "analysis_scope",
            "stakeholders",
            "jurisdiction",
            "time_horizon",
            "strategic_context",
            "current_process",
            "optimization_goal",
            "compliance_type",
        ]
        for field in generic_context_fields:
            if field in answers and answers[field] not in (None, "", []):
                context[field] = answers[field]

        return context
    
    @staticmethod
    def _build_constraints(domain, user_text: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build constraints dictionary.
        
        Hard constraints, requirements, limitations, context boundaries.
        """
        constraints = {}

        if "constraints" in answers:
            constraints["explicit"] = answers["constraints"]
        if "tone_preference" in answers:
            constraints["tone"] = answers["tone_preference"]
        if "length_preference" in answers:
            constraints["length"] = answers["length_preference"]
        if "current_pain" in answers:
            constraints["pain_points"] = answers["current_pain"]
        if "specific_requirements" in answers:
            constraints["requirements"] = answers["specific_requirements"]
        if "style_keywords" in answers:
            constraints["style_keywords"] = answers["style_keywords"]
        if "compliance_type" in answers:
            constraints["compliance_type"] = answers["compliance_type"]
        if "jurisdiction" in answers:
            constraints["jurisdiction"] = answers["jurisdiction"]
        
        # Context boundaries - these constrain the execution scope
        if "time_horizon" in answers:
            constraints["time_horizon"] = answers["time_horizon"]
        if "current_process" in answers:
            constraints["current_process"] = answers["current_process"]
        if "tech_stack" in answers:
            constraints["tech_stack"] = answers["tech_stack"]
        if "stakeholders" in answers:
            constraints["stakeholders"] = answers["stakeholders"]
        if "analysis_scope" in answers:
            constraints["analysis_scope"] = answers["analysis_scope"]

        if domain.value == "communication":
            constraints.setdefault("must_be_professional", True)
            constraints.setdefault("must_be_clear", True)

        elif domain.value == "technical":
            constraints.setdefault("must_be_executable", True)
            constraints.setdefault("must_be_tested", True)

        elif domain.value == "compliance":
            constraints.setdefault("must_be_legally_sound", True)
            constraints.setdefault("must_be_auditable", True)

        return constraints
    
    @staticmethod
    def _build_output_format(domain, user_text: str, answers: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build output format specification.
        
        Expected structure, length, format of deliverable.
        """
        output_format = {
            "domain": domain.value,
        }

        if "output_format" in answers:
            output_format["format"] = answers["output_format"]
        if "length_preference" in answers:
            output_format["length"] = answers["length_preference"]
        if "style_keywords" in answers:
            output_format["style"] = answers["style_keywords"]
        if "expected_output" in answers:
            output_format["expected_output"] = answers["expected_output"]

        if domain.value == "communication":
            output_format.setdefault("format", "email")
            output_format.setdefault("structure", ["greeting", "body", "call_to_action", "closing"])

        elif domain.value == "content_creation":
            output_format.setdefault("format", "article")
            output_format.setdefault("structure", ["title", "introduction", "body", "conclusion"])

        elif domain.value == "technical":
            output_format.setdefault("format", "code_with_comments")
            output_format.setdefault("structure", ["imports", "main_logic", "tests", "documentation"])

        elif domain.value == "analysis":
            output_format.setdefault("format", "report")
            output_format.setdefault("structure", ["summary", "findings", "analysis", "recommendations"])

        elif domain.value == "operations":
            output_format.setdefault("format", "process_plan")
            output_format.setdefault("structure", ["current_state", "issues", "optimized_flow", "next_steps"])

        elif domain.value == "strategy":
            output_format.setdefault("format", "strategy_brief")
            output_format.setdefault("structure", ["context", "objectives", "options", "recommendation", "roadmap"])

        elif domain.value == "compliance":
            output_format.setdefault("format", "compliance_assessment")
            output_format.setdefault("structure", ["scope", "requirements", "risk_assessment", "gaps", "actions"])

        return output_format
    
    @staticmethod
    def _build_acceptance_criteria(domain, user_text: str, answers: Dict[str, Any]) -> List[str]:
        """
        Build acceptance criteria list.
        
        How to verify the task was completed successfully.
        """
        criteria = []
        
        # Add explicit criteria from answers
        if "acceptance_criteria" in answers:
            explicit = answers["acceptance_criteria"]
            if isinstance(explicit, str):
                criteria.extend([c.strip() for c in explicit.split("\n") if c.strip()])
            elif isinstance(explicit, list):
                criteria.extend(explicit)
        
        # Add key points as criteria
        if "key_points" in answers:
            points = answers["key_points"]
            if isinstance(points, str):
                criteria.append(f"包含所有关键点：{points}")
            elif isinstance(points, list):
                criteria.append(f"包含所有关键点：{', '.join(points)}")
        
        # Add key questions as criteria
        if "key_questions" in answers:
            questions = answers["key_questions"]
            if isinstance(questions, str):
                criteria.append(f"回答关键问题：{questions}")
            elif isinstance(questions, list):
                criteria.append(f"回答关键问题：{', '.join(questions)}")
        
        # Add expected output as criteria
        if "expected_output" in answers:
            criteria.append(f"输出符合预期：{answers['expected_output']}")

        if "specific_requirements" in answers:
            criteria.append(f"满足特定要求：{answers['specific_requirements']}")
        if "constraints" in answers:
            criteria.append(f"遵守约束条件：{answers['constraints']}")
        if "optimization_goal" in answers:
            criteria.append(f"实现优化目标：{answers['optimization_goal']}")
        if "compliance_type" in answers:
            criteria.append(f"覆盖{answers['compliance_type']}相关合规要求")

        # Add domain-specific defaults
        if domain.value == "communication":
            criteria.append("语言清晰、无歧义")
            criteria.append("符合预期的语气和风格")
            if "recipient" in answers:
                criteria.append(f"适合发送给{answers['recipient']}")
        
        elif domain.value == "content_creation":
            criteria.append("内容原创、无抄袭")
            criteria.append("符合目标受众的理解水平")
            if "target_audience" in answers:
                criteria.append(f"适合{answers['target_audience']}")
        
        elif domain.value == "technical":
            criteria.append("代码可执行、无语法错误")
            criteria.append("包含必要的注释和文档")
            criteria.append("遵循最佳实践")
        
        elif domain.value == "analysis":
            criteria.append("分析逻辑清晰、有据可查")
            criteria.append("结论有充分支撑")
            criteria.append("建议可行且有价值")
        
        elif domain.value == "compliance":
            criteria.append("符合所有适用法律法规")
            criteria.append("可通过法律审核")
            criteria.append("风险可控")
        
        # Ensure we have at least some criteria
        if not criteria:
            criteria = [
                "完成用户指定的任务",
                "输出格式符合预期",
                "质量达到专业水准",
            ]
        
        return criteria


class SpecificationValidator:
    """Validate that specification is complete and coherent."""
    
    @staticmethod
    def validate(spec: TaskSpecification) -> tuple[bool, List[str]]:
        """
        Validate specification completeness.
        
        Returns: (is_valid, error_messages)
        """
        errors = []
        
        if not spec.objective or not spec.objective.strip():
            errors.append("目标不能为空")
        
        if not spec.context:
            errors.append("上下文信息不完整")
        
        if not spec.constraints:
            errors.append("约束条件不完整")
        
        if not spec.output_format:
            errors.append("输出格式未定义")
        
        if not spec.acceptance_criteria or len(spec.acceptance_criteria) == 0:
            errors.append("验收标准不完整")
        
        return len(errors) == 0, errors


class SpecAlignmentLayer:
    """Main specification alignment orchestrator."""
    
    def __init__(self):
        self.builder = SpecificationBuilder()
        self.validator = SpecificationValidator()
    
    def process(self, session: TaskSession) -> bool:
        """
        Process specification alignment.
        
        Returns: True if spec is valid and ready for execution.
        """
        # Build spec from user input + clarifications
        spec = self.builder.build_spec(session)
        
        # Validate
        is_valid, errors = self.validator.validate(spec)
        
        if not is_valid:
            # Log errors but don't fail - spec is still usable
            print(f"Spec validation warnings: {errors}")
        
        session.specification = spec
        session.state = WorkflowState.PREFLIGHT_CHECK
        
        return is_valid
