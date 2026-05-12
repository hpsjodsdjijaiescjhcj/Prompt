"""
Enterprise-Grade Domain Model for AI Task Orchestration System

Core data structures that represent the complete lifecycle of a task:
- Input → Clarification → Specification → Execution → Validation → Delivery

This is the authoritative source of truth for all task-related data.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid


# ════════════════════════════════════════════════════════════════════════════
# ENUMS: Task Classification & State Management
# ════════════════════════════════════════════════════════════════════════════

class TaskDomain(str, Enum):
    """Primary business domains - semantic classification."""
    COMMUNICATION = "communication"      # Email, messaging, notifications
    CONTENT_CREATION = "content_creation"  # Writing, copywriting, creative
    TECHNICAL = "technical"              # Code, architecture, infrastructure
    ANALYSIS = "analysis"                # Data analysis, research, insights
    OPERATIONS = "operations"            # Process, workflow, optimization
    COMPLIANCE = "compliance"            # Legal, contracts, policies
    STRATEGY = "strategy"                # Planning, decision support
    UNKNOWN = "unknown"


class TaskCharacteristic(str, Enum):
    """Nature of the work - what kind of thinking is required."""
    CREATIVE = "creative"                # Requires originality, ideation
    ANALYTICAL = "analytical"            # Requires reasoning, decomposition
    PROCEDURAL = "procedural"            # Follows defined steps
    TRANSFORMATIVE = "transformative"    # Converts one form to another
    GENERATIVE = "generative"            # Creates new content


class WorkflowState(str, Enum):
    """Complete workflow state machine."""
    INPUT_RECEIVED = "input_received"    # User input captured
    CLARIFYING = "clarifying"            # Asking minimal necessary questions
    SPEC_READY = "spec_ready"            # Specification confirmed
    PREFLIGHT_CHECK = "preflight_check"  # Logic validation before execution
    PREFLIGHT_PASSED = "preflight_passed"  # Preflight validation passed
    READY_FOR_EXECUTION = "ready_for_execution"  # Ready to execute
    EXECUTING = "executing"              # Task execution in progress
    EXECUTED = "executed"                # Execution completed
    VALIDATING = "validating"            # Output validation in progress
    VALIDATION_FAILED = "validation_failed"  # Validation failed
    REPAIR_ATTEMPT = "repair_attempt"    # Auto-repair in progress
    COMPLETED = "completed"              # Task completed successfully
    FAILED = "failed"                    # Task failed, needs manual intervention


class RiskLevel(str, Enum):
    """Risk assessment levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ValidationPhase(str, Enum):
    """Validation phases in the workflow."""
    PREFLIGHT = "preflight"              # Before execution
    OUTPUT = "output"                    # After execution
    ACCEPTANCE = "acceptance"            # Against acceptance criteria


# ════════════════════════════════════════════════════════════════════════════
# CORE DATA STRUCTURES
# ════════════════════════════════════════════════════════════════════════════

@dataclass
class UserInput:
    """Raw user input - the starting point."""
    text: str
    selected_domains: List[TaskDomain] = field(default_factory=list)
    selected_characteristics: List[TaskCharacteristic] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def is_empty(self) -> bool:
        return not self.text or not self.text.strip()


@dataclass
class ClarificationField:
    """A single field in the clarification form."""
    key: str
    label: str
    field_type: str  # text, multiline, choice, multi_choice, boolean
    required: bool
    placeholder: str = ""
    help_text: str = ""
    options: List[Dict[str, str]] = field(default_factory=list)
    default_value: Optional[Any] = None
    depends_on: Optional[str] = None
    depends_on_value: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ClarificationSchema:
    """Complete clarification form schema."""
    domain: TaskDomain
    fields: List[ClarificationField]
    title: str = ""
    description: str = ""
    
    def required_fields(self) -> List[ClarificationField]:
        return [f for f in self.fields if f.required]
    
    def optional_fields(self) -> List[ClarificationField]:
        return [f for f in self.fields if not f.required]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "domain": self.domain.value,
            "title": self.title,
            "description": self.description,
            "fields": [f.to_dict() for f in self.fields],
        }


@dataclass
class ClarificationAnswers:
    """User's answers to clarification questions."""
    answers: Dict[str, Any] = field(default_factory=dict)
    inferred_answers: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def get_answer(self, key: str) -> Optional[Any]:
        """Get answer with fallback to inferred."""
        return self.answers.get(key) or self.inferred_answers.get(key)
    
    def all_answers(self) -> Dict[str, Any]:
        """Merge inferred and explicit answers."""
        return {**self.inferred_answers, **self.answers}


@dataclass
class TaskSpecification:
    """Structured task specification - the execution contract."""
    domain: TaskDomain
    objective: str                        # What needs to be done
    context: Dict[str, Any]              # Background, motivation, stakeholders
    constraints: Dict[str, Any]          # Hard constraints, success criteria
    output_format: Dict[str, Any]        # Expected output shape
    acceptance_criteria: List[str]       # How to verify success
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = "1.0"
    
    def is_complete(self) -> bool:
        """Check if spec has all required fields."""
        return bool(
            self.objective and
            self.context and
            self.constraints and
            self.output_format and
            self.acceptance_criteria
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationIssue:
    """A single validation issue."""
    issue_type: str                      # missing_input, logic_error, constraint_violation
    severity: str                        # error, warning, info
    message: str
    step_id: Optional[str] = None
    suggestion: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ValidationResult:
    """Result of a validation phase."""
    phase: ValidationPhase
    passed: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def has_errors(self) -> bool:
        return any(i.severity == "error" for i in self.issues)
    
    def has_warnings(self) -> bool:
        return any(i.severity == "warning" for i in self.issues)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "phase": self.phase.value,
            "passed": self.passed,
            "issues": [i.to_dict() for i in self.issues],
            "risk_level": self.risk_level.value,
            "timestamp": self.timestamp,
        }


@dataclass
class ExecutionResult:
    """Result of task execution."""
    output: str
    execution_time_ms: int
    model_used: str
    tokens_used: Optional[Dict[str, int]] = None
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class TaskSession:
    """Complete task session - the root aggregate."""
    session_id: str
    user_input: UserInput
    
    # Classification
    domain: TaskDomain
    characteristics: List[TaskCharacteristic]
    routing_confidence: float
    
    # Workflow state
    state: WorkflowState
    
    # Clarification phase
    clarification_schema: Optional[ClarificationSchema] = None
    clarification_answers: Optional[ClarificationAnswers] = None
    
    # Specification phase
    specification: Optional[TaskSpecification] = None
    
    # Validation phases
    preflight_validation: Optional[ValidationResult] = None
    output_validation: Optional[ValidationResult] = None
    
    # Execution
    execution_result: Optional[ExecutionResult] = None
    
    # Metadata
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_input": asdict(self.user_input),
            "domain": self.domain.value,
            "characteristics": [c.value for c in self.characteristics],
            "routing_confidence": self.routing_confidence,
            "state": self.state.value,
            "clarification_schema": self.clarification_schema.to_dict() if self.clarification_schema else None,
            "clarification_answers": asdict(self.clarification_answers) if self.clarification_answers else None,
            "specification": self.specification.to_dict() if self.specification else None,
            "preflight_validation": self.preflight_validation.to_dict() if self.preflight_validation else None,
            "output_validation": self.output_validation.to_dict() if self.output_validation else None,
            "execution_result": self.execution_result.to_dict() if self.execution_result else None,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @staticmethod
    def create(text: str, domain: TaskDomain = TaskDomain.UNKNOWN) -> TaskSession:
        """Factory method to create a new session."""
        return TaskSession(
            session_id=str(uuid.uuid4()),
            user_input=UserInput(text=text),
            domain=domain,
            characteristics=[],
            routing_confidence=0.0,
            state=WorkflowState.INPUT_RECEIVED,
        )
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> TaskSession:
        """Deserialize TaskSession from dictionary."""
        # Parse enums
        domain = TaskDomain(data.get("domain", "unknown"))
        state = WorkflowState(data.get("state", "input_received"))
        characteristics = [
            TaskCharacteristic(c) for c in data.get("characteristics", [])
        ]
        
        # Parse nested objects
        user_input_data = data.get("user_input", {})
        user_input = UserInput(
            text=user_input_data.get("text", ""),
            selected_domains=[
                TaskDomain(d) for d in user_input_data.get("selected_domains", [])
            ],
            selected_characteristics=[
                TaskCharacteristic(c) for c in user_input_data.get("selected_characteristics", [])
            ],
            context=user_input_data.get("context", {}),
        )
        
        # Parse clarification schema
        clarification_schema = None
        if data.get("clarification_schema"):
            schema_data = data["clarification_schema"]
            fields = [
                ClarificationField(
                    key=f.get("key"),
                    label=f.get("label"),
                    field_type=f.get("field_type"),
                    required=f.get("required", False),
                    placeholder=f.get("placeholder", ""),
                    help_text=f.get("help_text", ""),
                    options=f.get("options", []),
                    default_value=f.get("default_value"),
                    depends_on=f.get("depends_on"),
                    depends_on_value=f.get("depends_on_value"),
                )
                for f in schema_data.get("fields", [])
            ]
            clarification_schema = ClarificationSchema(
                domain=TaskDomain(schema_data.get("domain", "unknown")),
                fields=fields,
                title=schema_data.get("title", ""),
                description=schema_data.get("description", ""),
            )
        
        # Parse clarification answers
        clarification_answers = None
        if data.get("clarification_answers"):
            ans_data = data["clarification_answers"]
            clarification_answers = ClarificationAnswers(
                answers=ans_data.get("answers", {}),
                inferred_answers=ans_data.get("inferred_answers", {}),
                timestamp=ans_data.get("timestamp", now_iso()),
            )
        
        # Parse specification
        specification = None
        if data.get("specification"):
            spec_data = data["specification"]
            specification = TaskSpecification(
                domain=TaskDomain(spec_data.get("domain", "unknown")),
                objective=spec_data.get("objective", ""),
                context=spec_data.get("context", {}),
                constraints=spec_data.get("constraints", {}),
                output_format=spec_data.get("output_format", {}),
                acceptance_criteria=spec_data.get("acceptance_criteria", []),
                created_at=spec_data.get("created_at", now_iso()),
                version=spec_data.get("version", "1.0"),
            )
        
        # Parse preflight validation
        preflight_validation = None
        if data.get("preflight_validation"):
            val_data = data["preflight_validation"]
            issues = [
                ValidationIssue(
                    issue_type=i.get("issue_type"),
                    severity=i.get("severity"),
                    message=i.get("message"),
                    step_id=i.get("step_id"),
                    suggestion=i.get("suggestion"),
                )
                for i in val_data.get("issues", [])
            ]
            preflight_validation = ValidationResult(
                phase=ValidationPhase.PREFLIGHT,
                passed=val_data.get("passed", False),
                issues=issues,
                risk_level=RiskLevel(val_data.get("risk_level", "low")),
                timestamp=val_data.get("timestamp", now_iso()),
            )
        
        # Parse output validation
        output_validation = None
        if data.get("output_validation"):
            val_data = data["output_validation"]
            issues = [
                ValidationIssue(
                    issue_type=i.get("issue_type"),
                    severity=i.get("severity"),
                    message=i.get("message"),
                    step_id=i.get("step_id"),
                    suggestion=i.get("suggestion"),
                )
                for i in val_data.get("issues", [])
            ]
            output_validation = ValidationResult(
                phase=ValidationPhase.OUTPUT,
                passed=val_data.get("passed", False),
                issues=issues,
                risk_level=RiskLevel(val_data.get("risk_level", "low")),
                timestamp=val_data.get("timestamp", now_iso()),
            )
        
        # Parse execution result
        execution_result = None
        if data.get("execution_result"):
            exec_data = data["execution_result"]
            execution_result = ExecutionResult(
                output=exec_data.get("output", ""),
                execution_time_ms=exec_data.get("execution_time_ms", 0),
                model_used=exec_data.get("model_used", ""),
                tokens_used=exec_data.get("tokens_used"),
                timestamp=exec_data.get("timestamp", now_iso()),
            )
        
        return TaskSession(
            session_id=data.get("session_id", str(uuid.uuid4())),
            user_input=user_input,
            domain=domain,
            characteristics=characteristics,
            routing_confidence=data.get("routing_confidence", 0.0),
            state=state,
            clarification_schema=clarification_schema,
            clarification_answers=clarification_answers,
            specification=specification,
            preflight_validation=preflight_validation,
            output_validation=output_validation,
            execution_result=execution_result,
            created_at=data.get("created_at", now_iso()),
            updated_at=data.get("updated_at", now_iso()),
        )


# ════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════

def now_iso() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


def create_session(text: str) -> TaskSession:
    """Create a new task session."""
    return TaskSession.create(text)
