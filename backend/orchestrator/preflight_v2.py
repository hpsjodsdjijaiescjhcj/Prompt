"""
Preflight Validation Layer v2 - Universal Logic Gate

Core principle: Validate execution readiness before running.
- Check dependency closure: all inputs available
- Check output reachability: can we deliver what's promised
- Check acceptance mapping: can we verify success
- Provide explicit failure reasons and recovery paths
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from orchestrator.domain_model import (
    TaskSession, TaskSpecification, ValidationResult, ValidationIssue,
    ValidationPhase, RiskLevel, WorkflowState
)


@dataclass
class PreflightCheckResult:
    """Result of a preflight check."""
    passed: bool
    issues: List[ValidationIssue]
    risk_level: RiskLevel
    recovery_suggestions: List[str]


class PreflightValidator:
    """Universal preflight validation logic."""
    
    @staticmethod
    def validate_spec_completeness(spec: TaskSpecification) -> Tuple[bool, List[ValidationIssue]]:
        """Check if specification has all required fields."""
        issues = []
        
        if not spec.objective or not spec.objective.strip():
            issues.append(ValidationIssue(
                issue_type="missing_input",
                severity="error",
                message="目标（objective）未定义",
                suggestion="请在规格中明确定义任务目标"
            ))
        
        if not spec.context or len(spec.context) == 0:
            issues.append(ValidationIssue(
                issue_type="missing_input",
                severity="warning",
                message="上下文信息缺失",
                suggestion="补充背景信息可以提高执行质量"
            ))
        
        if not spec.constraints or len(spec.constraints) == 0:
            issues.append(ValidationIssue(
                issue_type="missing_input",
                severity="warning",
                message="约束条件未定义",
                suggestion="明确约束条件可以避免不必要的返工"
            ))
        
        if not spec.output_format or len(spec.output_format) == 0:
            issues.append(ValidationIssue(
                issue_type="missing_input",
                severity="error",
                message="输出格式未定义",
                suggestion="明确输出格式（如：邮件、代码、报告等）"
            ))
        
        if not spec.acceptance_criteria or len(spec.acceptance_criteria) == 0:
            issues.append(ValidationIssue(
                issue_type="missing_input",
                severity="error",
                message="验收标准未定义",
                suggestion="定义至少3个可验证的验收标准"
            ))
        
        return len([i for i in issues if i.severity == "error"]) == 0, issues
    
    @staticmethod
    def validate_constraint_consistency(spec: TaskSpecification) -> Tuple[bool, List[ValidationIssue]]:
        """Check if constraints are internally consistent."""
        issues = []
        constraints = spec.constraints or {}
        
        # Check for conflicting constraints
        if constraints.get("length") == "short" and len(spec.acceptance_criteria) > 5:
            issues.append(ValidationIssue(
                issue_type="logic_error",
                severity="warning",
                message="短内容约束与多个验收标准可能冲突",
                suggestion="考虑增加长度限制或减少验收标准"
            ))
        
        # Check for impossible constraints
        if constraints.get("must_be_professional") and constraints.get("tone") == "casual":
            issues.append(ValidationIssue(
                issue_type="logic_error",
                severity="warning",
                message="专业性要求与随意语气可能冲突",
                suggestion="明确期望的语气风格"
            ))
        
        return len([i for i in issues if i.severity == "error"]) == 0, issues
    
    @staticmethod
    def validate_acceptance_mapping(spec: TaskSpecification) -> Tuple[bool, List[ValidationIssue]]:
        """Check if acceptance criteria can be verified against output."""
        issues = []
        
        if not spec.acceptance_criteria:
            return True, []
        
        # Check if criteria are measurable
        vague_keywords = ["好", "不错", "可以", "差不多", "大概", "应该"]
        for criterion in spec.acceptance_criteria:
            if any(kw in criterion for kw in vague_keywords):
                issues.append(ValidationIssue(
                    issue_type="constraint_violation",
                    severity="warning",
                    message=f"验收标准过于模糊：'{criterion}'",
                    suggestion="使用具体、可测量的标准，如：'包含X个要点'、'代码覆盖率>80%'"
                ))
        
        # Check if criteria align with output format
        output_format = spec.output_format.get("format", "")
        if output_format == "code" and any("文字" in c or "描述" in c for c in spec.acceptance_criteria):
            issues.append(ValidationIssue(
                issue_type="logic_error",
                severity="warning",
                message="代码输出格式与文字验收标准不匹配",
                suggestion="调整验收标准以匹配代码输出（如：'代码可执行'、'包含注释'）"
            ))
        
        return len([i for i in issues if i.severity == "error"]) == 0, issues
    
    @staticmethod
    def validate_domain_specific(spec: TaskSpecification) -> Tuple[bool, List[ValidationIssue]]:
        """Domain-specific validation rules."""
        issues = []
        domain = spec.domain.value
        context = spec.context or {}
        
        if domain == "communication":
            if "recipient" not in context:
                issues.append(ValidationIssue(
                    issue_type="missing_input",
                    severity="warning",
                    message="沟通对象未明确",
                    suggestion="明确收件人或目标受众"
                ))
        
        elif domain == "technical":
            if "tech_stack" not in context:
                issues.append(ValidationIssue(
                    issue_type="missing_input",
                    severity="warning",
                    message="技术栈未明确",
                    suggestion="指定编程语言、框架、版本等"
                ))
        
        elif domain == "compliance":
            if "jurisdiction" not in context:
                issues.append(ValidationIssue(
                    issue_type="missing_input",
                    severity="warning",
                    message="适用法律/地区未明确",
                    suggestion="明确适用的法律体系或地区"
                ))
        
        elif domain == "analysis":
            if "analysis_scope" not in context:
                issues.append(ValidationIssue(
                    issue_type="missing_input",
                    severity="warning",
                    message="分析范围未明确",
                    suggestion="明确分析的数据范围、时间段、对象等"
                ))
        
        return len([i for i in issues if i.severity == "error"]) == 0, issues
    
    @staticmethod
    def assess_risk_level(issues: List[ValidationIssue]) -> RiskLevel:
        """Assess overall risk level based on issues."""
        error_count = len([i for i in issues if i.severity == "error"])
        warning_count = len([i for i in issues if i.severity == "warning"])
        
        if error_count > 0:
            return RiskLevel.HIGH
        elif warning_count >= 3:
            return RiskLevel.MEDIUM
        elif warning_count > 0:
            return RiskLevel.LOW
        else:
            return RiskLevel.LOW


class PreflightLayer:
    """Main preflight orchestrator."""
    
    def __init__(self):
        self.validator = PreflightValidator()
    
    def validate(self, session: TaskSession) -> PreflightCheckResult:
        """
        Run complete preflight validation.
        
        Returns: PreflightCheckResult with all issues and suggestions.
        """
        if not session.specification:
            return PreflightCheckResult(
                passed=False,
                issues=[ValidationIssue(
                    issue_type="missing_input",
                    severity="error",
                    message="规格未生成",
                    suggestion="请先完成规格对齐步骤"
                )],
                risk_level=RiskLevel.CRITICAL,
                recovery_suggestions=["返回规格对齐步骤，确保所有必要信息已填写"]
            )
        
        spec = session.specification
        all_issues = []
        
        # Run all validation checks
        _, completeness_issues = self.validator.validate_spec_completeness(spec)
        all_issues.extend(completeness_issues)
        
        _, consistency_issues = self.validator.validate_constraint_consistency(spec)
        all_issues.extend(consistency_issues)
        
        _, mapping_issues = self.validator.validate_acceptance_mapping(spec)
        all_issues.extend(mapping_issues)
        
        _, domain_issues = self.validator.validate_domain_specific(spec)
        all_issues.extend(domain_issues)
        
        # Assess risk
        risk_level = self.validator.assess_risk_level(all_issues)
        
        # Determine if we can proceed
        has_errors = any(i.severity == "error" for i in all_issues)
        passed = not has_errors
        
        # Generate recovery suggestions
        recovery_suggestions = []
        if not passed:
            error_issues = [i for i in all_issues if i.severity == "error"]
            for issue in error_issues:
                if issue.suggestion:
                    recovery_suggestions.append(issue.suggestion)
        
        result = PreflightCheckResult(
            passed=passed,
            issues=all_issues,
            risk_level=risk_level,
            recovery_suggestions=recovery_suggestions
        )
        
        # Update session
        session.preflight_validation = ValidationResult(
            phase=ValidationPhase.PREFLIGHT,
            passed=passed,
            issues=all_issues,
            risk_level=risk_level
        )
        
        if passed:
            session.state = WorkflowState.READY_FOR_EXECUTION
        else:
            session.state = WorkflowState.PREFLIGHT_CHECK
        
        return result
    
    def can_proceed(self, session: TaskSession) -> bool:
        """Check if session can proceed to execution."""
        if not session.preflight_validation:
            return False
        
        return session.preflight_validation.passed
