"""
Spec Alignment Layer - Mapping Clarifications to Execution Spec

Implements the spec alignment phase with:
- Automatic mapping from clarify answers to execution spec
- Domain-aware spec generation
- Constraint validation
- Preflight checks before execution
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from .task_taxonomy import TaskTaxonomy, BusinessDomain
from .clarify_layer import ClarifyLayerBuilder


@dataclass
class ExecutionSpec:
    """Represents the execution specification for a task."""
    domain: str
    clarified_request: str
    output_preference: str
    domain_specific_params: Dict[str, Any]
    context: Dict[str, Any]  # motivation, target, stakeholders, etc.
    constraints: Dict[str, Any]  # hard_constraints, success_criteria
    handlers: List[str]  # Which handlers to use
    metadata: Dict[str, Any]  # timestamps, version, etc.


class SpecAlignmentEngine:
    """Maps clarify answers to execution specs."""

    @staticmethod
    def align_clarifications_to_spec(
        domain: BusinessDomain,
        clarify_answers: Dict[str, Any],
    ) -> ExecutionSpec:
        """
        Convert clarification answers into an execution spec.
        
        Args:
            domain: Business domain
            clarify_answers: Answers from clarify form
            
        Returns:
            ExecutionSpec ready for execution
        """
        # Extract universal fields
        clarified_request = clarify_answers.get("clarified_request", "")
        output_preference = clarify_answers.get("output_preference", "direct")

        # Extract context fields
        context = {
            "motivation": clarify_answers.get("motivation", ""),
            "primary_target": clarify_answers.get("primary_target", ""),
            "stakeholders": clarify_answers.get("stakeholders", ""),
        }

        # Extract constraints
        constraints = {
            "success_criteria": clarify_answers.get("success_criteria", ""),
            "hard_constraints": clarify_answers.get("hard_constraints", ""),
        }

        # Extract domain-specific parameters
        domain_profile = TaskTaxonomy.get_domain_profile(domain)
        domain_specific_params = {}
        
        for field_key in domain_profile.required_fields + domain_profile.optional_fields:
            if field_key in clarify_answers:
                domain_specific_params[field_key] = clarify_answers[field_key]

        # Get handlers for this domain
        handlers = domain_profile.handlers

        # Build spec
        spec = ExecutionSpec(
            domain=domain.value,
            clarified_request=clarified_request,
            output_preference=output_preference,
            domain_specific_params=domain_specific_params,
            context=context,
            constraints=constraints,
            handlers=handlers,
            metadata={
                "version": "1.0",
                "created_at": None,  # Will be set by caller
            },
        )

        return spec

    @staticmethod
    def validate_spec(spec: ExecutionSpec) -> tuple[bool, List[str]]:
        """
        Validate a spec before execution.
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []

        # Check required fields
        if not spec.clarified_request or not spec.clarified_request.strip():
            errors.append("clarified_request is required and cannot be empty")

        if not spec.output_preference:
            errors.append("output_preference is required")

        # Validate output preference
        valid_preferences = ["direct", "outline_then_final", "options_then_pick"]
        if spec.output_preference not in valid_preferences:
            errors.append(f"output_preference must be one of {valid_preferences}")

        # Check domain-specific parameters
        try:
            domain = BusinessDomain(spec.domain)
            domain_profile = TaskTaxonomy.get_domain_profile(domain)
            
            for required_field in domain_profile.required_fields:
                if required_field not in spec.domain_specific_params:
                    errors.append(f"Required field '{required_field}' is missing")
                elif not spec.domain_specific_params[required_field]:
                    errors.append(f"Required field '{required_field}' cannot be empty")
        except ValueError:
            errors.append(f"Invalid domain: {spec.domain}")

        return len(errors) == 0, errors

    @staticmethod
    def generate_system_prompt(spec: ExecutionSpec) -> str:
        """
        Generate a system prompt for the LLM based on the spec.
        
        This is the core instruction that guides execution.
        """
        domain = BusinessDomain(spec.domain)
        domain_profile = TaskTaxonomy.get_domain_profile(domain)

        # Build the system prompt
        lines = [
            f"# Task: {domain_profile.display_name}",
            "",
            "## Clarified Request",
            spec.clarified_request,
            "",
        ]

        # Add context if available
        if spec.context.get("motivation"):
            lines.extend([
                "## Context & Motivation",
                spec.context["motivation"],
                "",
            ])

        if spec.context.get("primary_target"):
            lines.extend([
                "## Primary Target",
                spec.context["primary_target"],
                "",
            ])

        if spec.context.get("stakeholders"):
            lines.extend([
                "## Stakeholders",
                spec.context["stakeholders"],
                "",
            ])

        # Add domain-specific guidance
        lines.extend([
            "## Domain-Specific Requirements",
        ])
        for key, value in spec.domain_specific_params.items():
            lines.append(f"- {key}: {value}")
        lines.append("")

        # Add constraints
        if spec.constraints.get("hard_constraints"):
            lines.extend([
                "## Hard Constraints (MUST NOT VIOLATE)",
                spec.constraints["hard_constraints"],
                "",
            ])

        if spec.constraints.get("success_criteria"):
            lines.extend([
                "## Success Criteria",
                spec.constraints["success_criteria"],
                "",
            ])

        # Add output preference guidance
        output_guidance = {
            "direct": "Provide the final result directly without intermediate steps.",
            "outline_then_final": "First provide an outline/structure, then the final result.",
            "options_then_pick": "First provide multiple options, then refine based on feedback.",
        }
        lines.extend([
            "## Output Preference",
            output_guidance.get(spec.output_preference, ""),
            "",
        ])

        # Add domain-specific constraints
        domain_constraints = TaskTaxonomy.get_constraints(domain)
        if domain_constraints:
            lines.extend([
                "## Domain Constraints",
            ])
            for constraint_key, constraint_value in domain_constraints.items():
                lines.append(f"- {constraint_key}: {constraint_value}")
            lines.append("")

        return "\n".join(lines)

    @staticmethod
    def to_dict(spec: ExecutionSpec) -> Dict[str, Any]:
        """Convert spec to dictionary for storage/transmission."""
        return asdict(spec)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> ExecutionSpec:
        """Reconstruct spec from dictionary."""
        return ExecutionSpec(**data)


class PreflightValidator:
    """Validates specs before execution - catches issues early."""

    @staticmethod
    def run_preflight_checks(spec: ExecutionSpec) -> Dict[str, Any]:
        """
        Run comprehensive preflight checks.
        
        Returns:
            {
                "passed": bool,
                "warnings": List[str],
                "errors": List[str],
                "suggestions": List[str],
            }
        """
        warnings = []
        errors = []
        suggestions = []

        # Validate spec structure
        is_valid, validation_errors = SpecAlignmentEngine.validate_spec(spec)
        if not is_valid:
            errors.extend(validation_errors)

        # Check for common issues
        if len(spec.clarified_request) < 10:
            warnings.append("Clarified request is very short - may lack detail")

        if len(spec.clarified_request) > 500:
            suggestions.append("Consider breaking down the request into smaller tasks")

        # Check for missing context
        if not spec.context.get("motivation"):
            suggestions.append("Adding motivation context can improve result quality")

        if not spec.context.get("primary_target"):
            suggestions.append("Specifying the primary target helps with accuracy")

        # Check for missing constraints
        if not spec.constraints.get("hard_constraints"):
            suggestions.append("Consider adding hard constraints to prevent unwanted outputs")

        if not spec.constraints.get("success_criteria"):
            suggestions.append("Defining success criteria helps validate the result")

        # Domain-specific checks
        domain = BusinessDomain(spec.domain)
        domain_profile = TaskTaxonomy.get_domain_profile(domain)

        # Check if all required handlers are available
        for handler in spec.handlers:
            if handler not in ["email", "code", "content", "documentation", "analysis", "planning", "social_media", "architecture"]:
                warnings.append(f"Unknown handler type: {handler}")

        # Check domain-specific constraints
        domain_constraints = TaskTaxonomy.get_constraints(domain)
        if domain_constraints.get("requires_testing") and "code" in spec.handlers:
            if not spec.constraints.get("hard_constraints"):
                suggestions.append("For code tasks, specify testing requirements in constraints")

        if domain_constraints.get("requires_approval") and not spec.context.get("stakeholders"):
            suggestions.append("This domain requires approval - consider specifying stakeholders")

        return {
            "passed": len(errors) == 0,
            "warnings": warnings,
            "errors": errors,
            "suggestions": suggestions,
        }
