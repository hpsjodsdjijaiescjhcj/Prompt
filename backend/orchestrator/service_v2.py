"""
Orchestration Service v2 - Complete Workflow Orchestrator

Integrates all layers:
- Input → Classification → Clarification → Specification → Preflight → Execution → Validation

This is the main entry point for the entire system.
"""

from typing import Dict, Optional, Tuple
import uuid
import logging
from datetime import datetime, timezone

from orchestrator.domain_model import (
    TaskSession, UserInput, WorkflowState, ExecutionResult
)
from orchestrator.task_taxonomy_v2 import (
    infer_domain_and_characteristics, get_clarification_schema
)
from orchestrator.clarify_layer_v3 import ClarifyLayerV3
from orchestrator.spec_alignment_v2 import SpecAlignmentLayer
from orchestrator.preflight_v2 import PreflightLayer
from orchestrator.validation_v2 import ValidationLayer
from orchestrator.llm_gateway import LLMGateway

logger = logging.getLogger(__name__)


class OrchestrationService:
    """Main orchestration service - coordinates all workflow layers."""
    
    def __init__(self, llm_client=None, store=None):
        """
        Initialize orchestration service.
        
        Args:
            llm_client: LLM client for execution (optional)
            store: Session store for persistence (optional)
        """
        self.llm_client = llm_client
        self.store = store
        self.llm_gateway = LLMGateway()
        
        # Initialize all layers
        self.clarify_layer = ClarifyLayerV3(llm_client=llm_client)
        self.spec_layer = SpecAlignmentLayer()
        self.preflight_layer = PreflightLayer()
        self.validation_layer = ValidationLayer()
        
        # Session cache
        self._sessions: Dict[str, TaskSession] = {}
    
    # ════════════════════════════════════════════════════════════════════════
    # PHASE 1: INPUT & CLASSIFICATION
    # ════════════════════════════════════════════════════════════════════════
    
    def create_session(
        self,
        user_text: str,
        selected_domains: Optional[list] = None,
        selected_characteristics: Optional[list] = None,
        context: Optional[Dict] = None,
    ) -> TaskSession:
        """
        Create a new task session from user input.

        Optional user-selected labels are preserved as soft routing constraints,
        not hard overrides.
        """
        # Create session
        session = TaskSession.create(user_text)
        session.user_input.selected_domains = selected_domains or []
        session.user_input.selected_characteristics = selected_characteristics or []
        session.user_input.context = context or {}

        # Classify domain and characteristics
        domain, characteristics, confidence = infer_domain_and_characteristics(user_text)
        domain, characteristics, confidence = self._apply_user_routing_hints(
            domain,
            characteristics,
            confidence,
            session.user_input.selected_domains,
            session.user_input.selected_characteristics,
        )
        session.domain = domain
        session.characteristics = characteristics
        session.routing_confidence = confidence
        
        # Cache session
        self._sessions[session.session_id] = session
        
        # Persist if store available
        if self.store:
            self.store.create(
                text=user_text,
                preferred_executor=None,
                context=context or {},
                task_type=domain,
                session_id=session.session_id,
            )
        
        return session
    
    # ════════════════════════════════════════════════════════════════════════
    # PHASE 2: CLARIFICATION
    # ════════════════════════════════════════════════════════════════════════
    
    def process_clarification(self, session_id: str) -> Dict:
        """
        Process clarification for a session.
        
        Returns: {
            "should_skip": bool,
            "schema": ClarificationSchema or None,
            "completeness": float
        }
        """
        session = self._get_session(session_id)
        
        # Run clarification layer
        should_skip, schema = self.clarify_layer.process(session)
        
        # Persist
        if self.store:
            self.store.update(session_id, state=session.state.value)
        
        return {
            "should_skip": should_skip,
            "schema": schema.to_dict() if schema else None,
            "session_state": session.state.value,
        }
    
    def submit_clarification_answers(
        self,
        session_id: str,
        answers: Dict[str, any]
    ) -> Dict:
        """
        Submit clarification answers.
        
        Returns: {
            "success": bool,
            "session_state": str,
            "next_step": str
        }
        """
        session = self._get_session(session_id)
        
        # Submit answers
        self.clarify_layer.submit_answers(session, answers)
        
        # Persist
        if self.store:
            self.store.update(session_id, state=session.state.value, clarification_answers=answers)
        
        return {
            "success": True,
            "session_state": session.state.value,
            "next_step": "specification_alignment",
        }
    
    # ════════════════════════════════════════════════════════════════════════
    # PHASE 3: SPECIFICATION ALIGNMENT
    # ════════════════════════════════════════════════════════════════════════
    
    def align_specification(self, session_id: str) -> Dict:
        """
        Align and build task specification.
        
        Returns: {
            "success": bool,
            "specification": dict,
            "session_state": str
        }
        """
        session = self._get_session(session_id)
        
        # Build spec
        is_valid = self.spec_layer.process(session)
        
        # Persist
        if self.store:
            spec_dict = session.specification.to_dict() if session.specification else None
            self.store.update(session_id, state=session.state.value, specification=spec_dict)
        
        return {
            "success": is_valid,
            "specification": session.specification.to_dict() if session.specification else None,
            "session_state": session.state.value,
            "next_step": "preflight_validation",
        }
    
    def update_specification(
        self,
        session_id: str,
        updates: Dict[str, any]
    ) -> Dict:
        """
        Allow user to edit specification before execution.
        
        Returns: {
            "success": bool,
            "specification": dict
        }
        """
        session = self._get_session(session_id)
        
        if not session.specification:
            return {"success": False, "error": "No specification to update"}
        
        spec = session.specification
        
        # Apply updates
        if "objective" in updates:
            spec.objective = updates["objective"]
        
        if "context" in updates:
            spec.context.update(updates["context"])
        
        if "constraints" in updates:
            spec.constraints.update(updates["constraints"])
        
        if "output_format" in updates:
            spec.output_format.update(updates["output_format"])
        
        if "acceptance_criteria" in updates:
            spec.acceptance_criteria = updates["acceptance_criteria"]
        
        # Persist
        if self.store:
            self.store.update(session_id, specification=spec.to_dict())
        
        return {
            "success": True,
            "specification": spec.to_dict(),
        }
    
    # ════════════════════════════════════════════════════════════════════════
    # PHASE 4: PREFLIGHT VALIDATION
    # ════════════════════════════════════════════════════════════════════════
    
    def run_preflight(self, session_id: str) -> Dict:
        """
        Run preflight validation.
        
        Returns: {
            "passed": bool,
            "issues": list,
            "risk_level": str,
            "recovery_suggestions": list
        }
        """
        session = self._get_session(session_id)
        
        # Run preflight
        result = self.preflight_layer.validate(session)
        
        # Persist
        if self.store:
            self.store.update(session_id, state=session.state.value, preflight_result={
                "passed": result.passed,
                "issues": [i.to_dict() for i in result.issues],
                "risk_level": result.risk_level.value,
            })
        
        return {
            "passed": result.passed,
            "issues": [i.to_dict() for i in result.issues],
            "risk_level": result.risk_level.value,
            "recovery_suggestions": result.recovery_suggestions,
            "session_state": session.state.value,
            "next_step": "execution" if result.passed else "specification_update",
        }
    
    # ════════════════════════════════════════════════════════════════════════
    # PHASE 5: EXECUTION
    # ════════════════════════════════════════════════════════════════════════
    
    def execute(self, session_id: str) -> Dict:
        """
        Execute the task.
        
        Returns: {
            "success": bool,
            "output": str,
            "execution_time_ms": int,
            "model_used": str
        }
        """
        session = self._get_session(session_id)
        
        # Check if preflight passed (check session state)
        if session.state not in [WorkflowState.PREFLIGHT_PASSED, WorkflowState.READY_FOR_EXECUTION, WorkflowState.SPEC_READY]:
            return {
                "success": False,
                "error": "Preflight validation not passed",
            }
        
        if not session.specification:
            return {
                "success": False,
                "error": "No specification to execute",
            }
        
        session.state = WorkflowState.EXECUTING
        
        try:
            # Build execution prompt
            prompt = self._build_execution_prompt(session)
            
            # Execute
            start_time = datetime.now(timezone.utc)
            output, model_used, provider, inference_mode, tokens_used = self._execute_with_fallback(session, prompt)
            end_time = datetime.now(timezone.utc)
            
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Create execution result
            execution_result = ExecutionResult(
                output=output,
                execution_time_ms=execution_time_ms,
                model_used=model_used,
                tokens_used=tokens_used,
                inference_mode=inference_mode,
                provider=provider,
            )
            
            session.execution_result = execution_result
            session.state = WorkflowState.EXECUTED
            
            # Persist
            if self.store:
                self.store.update(session_id, state=session.state.value, execution_result={
                    "output": output,
                    "execution_time_ms": execution_time_ms,
                    "model_used": model_used,
                    "tokens_used": tokens_used,
                    "inference_mode": inference_mode,
                    "provider": provider,
                })
            
            return {
                "success": True,
                "output": output,
                "execution_time_ms": execution_time_ms,
                "model_used": execution_result.model_used,
                "tokens_used": execution_result.tokens_used,
                "inference_mode": execution_result.inference_mode,
                "provider": execution_result.provider,
                "next_step": "validation",
            }
        
        except Exception as e:
            logger.exception("Execution failed for session %s", session_id)
            session.state = WorkflowState.FAILED
            if self.store:
                self.store.update(session_id, state=session.state.value, error=str(e))
            
            return {
                "success": False,
                "error": str(e),
            }
    
    # ════════════════════════════════════════════════════════════════════════
    # PHASE 6: VALIDATION
    # ════════════════════════════════════════════════════════════════════════
    
    def validate_output(self, session_id: str) -> Dict:
        """
        Validate execution output.
        
        Returns: {
            "passed": bool,
            "issues": list,
            "risk_level": str,
            "can_repair": bool
        }
        """
        session = self._get_session(session_id)
        
        if not session.execution_result:
            return {
                "success": False,
                "error": "No execution result to validate",
            }
        
        # Validate
        result = self.validation_layer.validate(session, session.execution_result)
        
        # Determine if repair is possible
        can_repair = result.passed is False and len(result.issues) > 0 and result.risk_level.value != "critical"
        
        # Update session state
        if result.passed:
            session.state = WorkflowState.COMPLETED
        else:
            session.state = WorkflowState.VALIDATION_FAILED
        
        # Persist
        if self.store:
            self.store.update(session_id, state=session.state.value, validation_result={
                "passed": result.passed,
                "issues": [i.to_dict() for i in result.issues],
                "risk_level": result.risk_level.value,
            })
        
        return {
            "passed": result.passed,
            "issues": [i.to_dict() for i in result.issues],
            "risk_level": result.risk_level.value,
            "can_repair": can_repair,
            "session_state": session.state.value,
            "next_step": "completed" if result.passed else "repair_or_manual_review",
        }
    
    # ════════════════════════════════════════════════════════════════════════
    # SESSION MANAGEMENT
    # ════════════════════════════════════════════════════════════════════════
    
    def get_session(self, session_id: str) -> Dict:
        """Get complete session state."""
        session = self._get_session(session_id)
        return session.to_dict()
    
    def list_sessions(self) -> list:
        """List all sessions."""
        return [s.to_dict() for s in self._sessions.values()]
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        if session_id in self._sessions:
            del self._sessions[session_id]
        
        if self.store:
            return self.store.delete(session_id)
        
        return session_id not in self._sessions
    
    def _get_session(self, session_id: str) -> TaskSession:
        """Get session from cache or store."""
        if session_id in self._sessions:
            return self._sessions[session_id]
        
        if self.store:
            session_data = self.store.get(session_id)
            if session_data:
                # Reconstruct TaskSession from stored data
                session = TaskSession.from_dict(session_data)
                self._sessions[session_id] = session
                return session
        
        raise ValueError(f"Session not found: {session_id}")
    
    # ════════════════════════════════════════════════════════════════════════
    # HELPERS
    # ════════════════════════════════════════════════════════════════════════
    
    def _build_execution_prompt(self, session: TaskSession) -> str:
        """Build execution prompt from specification."""
        spec = session.specification
        
        prompt_parts = [
            "# 角色",
            "你是一个可靠的任务执行代理，必须严格遵守规格、约束与验收标准。",
            "",
            "# 任务目标",
            spec.objective,
            "",
            "# 背景信息",
            self._format_dict(spec.context),
            "",
            "# 约束条件",
            self._format_dict(spec.constraints),
            "",
            "# 输出格式",
            self._format_dict(spec.output_format),
            "",
            "# 验收标准",
            "\n".join(f"- {c}" for c in spec.acceptance_criteria),
            "",
            "# 执行要求",
            "输出最终可交付结果，不要解释你的思考过程；若信息不足，优先在结果中显式标出假设。",
        ]
        
        return "\n".join(prompt_parts)

    def _apply_user_routing_hints(
        self,
        domain,
        characteristics,
        confidence: float,
        selected_domains: list,
        selected_characteristics: list,
    ):
        """Merge user label hints as soft constraints into routing result."""
        boosted_confidence = confidence
        if selected_domains and domain in selected_domains:
            boosted_confidence = min(1.0, confidence + 0.15)
        elif selected_domains and domain not in selected_domains and confidence < 0.55:
            domain = selected_domains[0]
            boosted_confidence = 0.56

        merged_characteristics = list(characteristics or [])
        for item in selected_characteristics or []:
            if item not in merged_characteristics:
                merged_characteristics.append(item)

        return domain, merged_characteristics, boosted_confidence

    def _execute_with_fallback(self, session: TaskSession, prompt: str) -> Tuple[str, str, str, str, Optional[Dict]]:
        """Run with best available executor and safe degradation."""
        if self.llm_gateway.is_configured():
            try:
                response = self.llm_gateway.chat(prompt)
                return response.text, response.model, response.provider, "api_primary", response.tokens_used
            except Exception as exc:
                logger.warning("Configured LLM gateway failed; falling back locally for session %s: %s", session.session_id, exc)

        if self.llm_client:
            try:
                if hasattr(self.llm_client, "generate"):
                    return self.llm_client.generate(prompt), getattr(self.llm_client, "model_name", "configured-llm"), "legacy", "api_legacy", None
                if hasattr(self.llm_client, "chat"):
                    return self.llm_client.chat(prompt), getattr(self.llm_client, "model_name", "configured-llm"), "legacy", "api_legacy", None
            except Exception as exc:
                logger.warning("Legacy llm_client failed; falling back locally for session %s: %s", session.session_id, exc)

        logger.warning("No compatible llm_client found; using deterministic fallback for session %s", session.session_id)
        return self._render_fallback_output(session), "deterministic-fallback", "local", "fallback_rule", None

    def _render_fallback_output(self, session: TaskSession) -> str:
        """Deterministic fallback so workflow remains executable/testable without API access."""
        spec = session.specification
        output_format = (spec.output_format or {}).get("format", "generic")
        if output_format == "email":
            recipient = spec.context.get("recipient", "相关方")
            return (
                f"您好，{recipient}：\n\n"
                f"关于本次事项，我已根据当前需求整理如下：{spec.objective}。\n"
                f"关键约束：{self._single_line(spec.constraints)}。\n"
                f"请确认是否按该方向继续推进。\n\n"
                "此致\n敬礼"
            )
        if "code" in output_format:
            return (
                "# Fallback implementation scaffold\n"
                "def execute_task():\n"
                f"    \"\"\"{spec.objective}\"\"\"\n"
                "    raise NotImplementedError('LLM unavailable; provide configured executor for full generation')\n"
            )
        return (
            f"任务目标：{spec.objective}\n\n"
            f"背景摘要：{self._single_line(spec.context)}\n"
            f"执行约束：{self._single_line(spec.constraints)}\n"
            "\n已根据当前规格生成可继续验证的基础交付稿；接入模型后可替换为正式高质量结果。"
        )

    @staticmethod
    def _single_line(data: Dict) -> str:
        if not data:
            return "无"
        parts = []
        for key, value in data.items():
            parts.append(f"{key}={value}")
        return "；".join(parts)
    
    @staticmethod
    def _format_dict(d: Dict) -> str:
        """Format dictionary for display."""
        if not d:
            return "(无)"
        
        lines = []
        for key, value in d.items():
            if isinstance(value, dict):
                lines.append(f"- {key}:")
                for k, v in value.items():
                    lines.append(f"  - {k}: {v}")
            elif isinstance(value, list):
                lines.append(f"- {key}:")
                for item in value:
                    lines.append(f"  - {item}")
            else:
                lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)
