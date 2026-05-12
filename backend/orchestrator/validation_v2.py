"""
Output Validation Layer v2 - Multi-Phase Verification & Auto-Repair

Core principle: Validate output against acceptance criteria.
- Format validation: output structure matches spec
- Constraint validation: output respects all constraints
- Acceptance validation: output meets all criteria
- Auto-repair: attempt single-round correction if validation fails
"""

from typing import Dict, List, Optional, Tuple
from orchestrator.domain_model import (
    TaskSession, TaskSpecification, ExecutionResult, ValidationResult,
    ValidationIssue, ValidationPhase, RiskLevel, WorkflowState
)


class OutputValidator:
    """Validate execution output against specification."""
    
    @staticmethod
    def validate_format(
        output: str,
        spec: TaskSpecification
    ) -> Tuple[bool, List[ValidationIssue]]:
        """Validate output format matches specification."""
        issues = []
        output_format = spec.output_format or {}
        
        if not output or not output.strip():
            issues.append(ValidationIssue(
                issue_type="format_error",
                severity="error",
                message="输出为空",
                suggestion="执行器未生成有效输出，请重试"
            ))
            return False, issues
        
        # Check minimum length
        min_length = 10
        if len(output.strip()) < min_length:
            issues.append(ValidationIssue(
                issue_type="format_error",
                severity="warning",
                message=f"输出过短（{len(output.strip())}字符）",
                suggestion="输出可能不够完整，建议检查"
            ))
        
        # Domain-specific format checks
        domain = spec.domain.value
        
        if domain == "communication":
            # Email should have greeting, body, closing
            if not any(greeting in output for greeting in ["尊敬的", "亲爱的", "您好", "Hi", "Dear"]):
                issues.append(ValidationIssue(
                    issue_type="format_error",
                    severity="warning",
                    message="邮件缺少问候语",
                    suggestion="邮件应以适当的问候开始"
                ))
        
        elif domain == "technical":
            # Code should have proper structure
            if "def " not in output and "class " not in output and "function " not in output:
                if not any(lang_marker in output for lang_marker in ["import", "require", "package", "use"]):
                    issues.append(ValidationIssue(
                        issue_type="format_error",
                        severity="warning",
                        message="代码结构可能不完整",
                        suggestion="确保代码包含必要的导入、定义或声明"
                    ))
        
        elif domain == "content_creation":
            # Content should have title and body
            lines = output.strip().split("\n")
            if len(lines) < 3:
                issues.append(ValidationIssue(
                    issue_type="format_error",
                    severity="warning",
                    message="内容结构过于简单",
                    suggestion="内容应包含标题、正文等多个部分"
                ))
        
        return len([i for i in issues if i.severity == "error"]) == 0, issues
    
    @staticmethod
    def validate_constraints(
        output: str,
        spec: TaskSpecification
    ) -> Tuple[bool, List[ValidationIssue]]:
        """Validate output respects all constraints."""
        issues = []
        constraints = spec.constraints or {}
        
        # Check length constraints
        length_pref = constraints.get("length")
        output_len = len(output.strip())
        
        if length_pref == "short" and output_len > 500:
            issues.append(ValidationIssue(
                issue_type="constraint_violation",
                severity="warning",
                message=f"输出超过短内容限制（{output_len}字符 > 500字符）",
                suggestion="考虑精简输出内容"
            ))
        
        elif length_pref == "long" and output_len < 200:
            issues.append(ValidationIssue(
                issue_type="constraint_violation",
                severity="warning",
                message=f"输出未达到详细内容要求（{output_len}字符 < 200字符）",
                suggestion="补充更多细节和说明"
            ))
        
        # Check tone constraints
        tone_prefs = constraints.get("tone", [])
        if isinstance(tone_prefs, str):
            tone_prefs = [tone_prefs]
        
        if "formal" in tone_prefs:
            informal_markers = ["哈哈", "呵呵", "嘿", "哇", "😂", "🤣"]
            if any(marker in output for marker in informal_markers):
                issues.append(ValidationIssue(
                    issue_type="constraint_violation",
                    severity="warning",
                    message="输出包含非正式表达",
                    suggestion="移除非正式的表情符号和语气词"
                ))
        
        # Check for required content
        key_points = constraints.get("key_points")
        if key_points:
            if isinstance(key_points, str):
                key_points = [p.strip() for p in key_points.split("\n") if p.strip()]
            
            missing_points = []
            for point in key_points:
                if point not in output:
                    missing_points.append(point)
            
            if missing_points:
                issues.append(ValidationIssue(
                    issue_type="constraint_violation",
                    severity="warning",
                    message=f"缺少关键点：{', '.join(missing_points[:2])}",
                    suggestion="确保输出包含所有指定的关键点"
                ))
        
        return len([i for i in issues if i.severity == "error"]) == 0, issues
    
    @staticmethod
    def validate_acceptance_criteria(
        output: str,
        spec: TaskSpecification
    ) -> Tuple[bool, List[ValidationIssue]]:
        """Validate output meets acceptance criteria."""
        issues = []
        criteria = spec.acceptance_criteria or []
        
        if not criteria:
            return True, []
        
        # For each criterion, try to verify
        for criterion in criteria:
            criterion_lower = criterion.lower()
            output_lower = output.lower()
            
            # Simple heuristic checks
            if "包含" in criterion_lower or "contains" in criterion_lower:
                # Extract what should be contained
                parts = criterion.split("：")
                if len(parts) > 1:
                    required_content = parts[1].strip()
                    if required_content not in output:
                        issues.append(ValidationIssue(
                            issue_type="acceptance_failure",
                            severity="warning",
                            message=f"未满足验收标准：{criterion}",
                            suggestion=f"确保输出包含：{required_content}"
                        ))
            
            elif "无" in criterion_lower or "error" in criterion_lower or "bug" in criterion_lower:
                # Check for common error patterns
                error_patterns = ["错误", "error", "exception", "fail", "bug", "undefined"]
                if any(pattern in output_lower for pattern in error_patterns):
                    issues.append(ValidationIssue(
                        issue_type="acceptance_failure",
                        severity="warning",
                        message=f"输出可能包含错误：{criterion}",
                        suggestion="检查输出中是否有错误信息或异常"
                    ))
        
        return len([i for i in issues if i.severity == "error"]) == 0, issues


class ValidationLayer:
    """Main output validation orchestrator."""
    
    def __init__(self):
        self.validator = OutputValidator()
    
    def validate(
        self,
        session: TaskSession,
        execution_result: ExecutionResult
    ) -> ValidationResult:
        """
        Run complete output validation.
        
        Returns: ValidationResult with all issues.
        """
        if not session.specification:
            return ValidationResult(
                phase=ValidationPhase.OUTPUT,
                passed=False,
                issues=[ValidationIssue(
                    issue_type="missing_input",
                    severity="error",
                    message="规格未定义",
                    suggestion="无法验证输出"
                )],
                risk_level=RiskLevel.CRITICAL
            )
        
        spec = session.specification
        output = execution_result.output
        all_issues = []
        
        # Run all validation checks
        _, format_issues = self.validator.validate_format(output, spec)
        all_issues.extend(format_issues)
        
        _, constraint_issues = self.validator.validate_constraints(output, spec)
        all_issues.extend(constraint_issues)
        
        _, acceptance_issues = self.validator.validate_acceptance_criteria(output, spec)
        all_issues.extend(acceptance_issues)
        
        # Assess risk
        error_count = len([i for i in all_issues if i.severity == "error"])
        warning_count = len([i for i in all_issues if i.severity == "warning"])
        
        if error_count > 0:
            risk_level = RiskLevel.HIGH
        elif warning_count >= 3:
            risk_level = RiskLevel.MEDIUM
        elif warning_count > 0:
            risk_level = RiskLevel.LOW
        else:
            risk_level = RiskLevel.LOW
        
        passed = error_count == 0
        
        result = ValidationResult(
            phase=ValidationPhase.OUTPUT,
            passed=passed,
            issues=all_issues,
            risk_level=risk_level
        )
        
        session.output_validation = result
        
        if passed:
            session.state = WorkflowState.COMPLETED
        else:
            session.state = WorkflowState.VALIDATING
        
        return result
    
    def should_attempt_repair(self, validation_result: ValidationResult) -> bool:
        """Decide if we should attempt auto-repair."""
        # Only attempt repair if there are warnings but no errors
        has_errors = any(i.severity == "error" for i in validation_result.issues)
        has_warnings = any(i.severity == "warning" for i in validation_result.issues)
        
        return has_warnings and not has_errors
