"""
Clarification Layer v3 - Intelligent Gap Detection with LLM

Core principle: Only ask what's truly missing, using semantic understanding.
- Use LLM to understand what information user has already provided
- Dynamically generate only necessary clarification questions
- Preserve all user input - nothing gets lost
- Support inference of missing answers from context
"""

from typing import Dict, List, Optional, Tuple
import json
import logging
from orchestrator.domain_model import (
    TaskSession, ClarificationSchema, ClarificationAnswers,
    WorkflowState, UserInput, ClarificationField
)
from orchestrator.task_taxonomy_v2 import get_clarification_schema

logger = logging.getLogger(__name__)


class SemanticGapDetector:
    """Use LLM to detect what information is actually missing."""
    
    def __init__(self, llm_client=None):
        """Initialize with optional LLM client for semantic understanding."""
        self.llm_client = llm_client
    
    @staticmethod
    def _extract_field_keywords(field: ClarificationField) -> List[str]:
        """Extract semantic keywords from a field."""
        keywords = []
        
        # Add field label keywords
        keywords.extend(field.label.lower().split())
        
        # Add help text keywords
        if field.help_text:
            keywords.extend(field.help_text.lower().split())
        
        # Add placeholder keywords
        if field.placeholder:
            keywords.extend(field.placeholder.lower().split())
        
        # Add option keywords for choice fields
        if field.options:
            for option in field.options:
                keywords.append(option.get("label", "").lower())
                keywords.append(option.get("value", "").lower())
        
        return list(set(keywords))  # Remove duplicates
    
    @staticmethod
    def _simple_field_detection(user_text: str, field: ClarificationField) -> bool:
        """
        Simple heuristic: check if field information appears in user text.
        
        Returns True if field information is likely present.
        """
        text_lower = user_text.lower()
        keywords = SemanticGapDetector._extract_field_keywords(field)
        
        # Check if any keyword appears in text
        found_keywords = sum(1 for kw in keywords if kw in text_lower and len(kw) > 2)
        
        # If we found multiple keywords or the field is very specific, consider it found
        return found_keywords >= 2 or (found_keywords >= 1 and len(keywords) <= 3)
    
    def detect_gaps_semantic(
        self,
        user_input: UserInput,
        domain_schema: ClarificationSchema
    ) -> Tuple[List[str], Dict[str, float], float]:
        """
        Detect missing fields using semantic understanding.
        
        Returns: (missing_field_keys, field_confidence_scores, overall_completeness)
        """
        text = user_input.text
        missing = []
        field_scores = {}
        
        required_fields = domain_schema.required_fields()
        
        if not required_fields:
            return [], {}, 1.0
        
        # Score each required field
        for field in required_fields:
            # Use simple detection for now (can be enhanced with LLM)
            is_present = self._simple_field_detection(text, field)
            
            if is_present:
                field_scores[field.key] = 0.8  # High confidence that field is present
            else:
                field_scores[field.key] = 0.2  # Low confidence
                missing.append(field.key)
        
        # Calculate overall completeness
        total_required = len(required_fields)
        found_count = total_required - len(missing)
        completeness = found_count / total_required if total_required > 0 else 1.0
        
        return missing, field_scores, completeness
    
    @staticmethod
    def should_skip_clarification(completeness_score: float, missing_count: int) -> bool:
        """
        Decide if clarification can be skipped.
        
        Skip if:
        - User input is >85% complete, OR
        - Only 1 or fewer fields are missing
        """
        return completeness_score >= 0.85 or missing_count <= 1


class IntelligentClarificationBuilder:
    """Build minimal, intelligent clarification form."""
    
    @staticmethod
    def build_minimal_schema(
        full_schema: ClarificationSchema,
        missing_keys: List[str],
        user_text: str = ""
    ) -> ClarificationSchema:
        """
        Build a minimal schema with only missing required fields.
        
        Also reorder fields by importance and add contextual help.
        """
        if not missing_keys:
            return ClarificationSchema(
                domain=full_schema.domain,
                title=full_schema.title,
                description="你的输入已足够完整，无需补充。",
                fields=[]
            )
        
        # Filter to only missing fields
        minimal_fields = [
            f for f in full_schema.fields
            if f.key in missing_keys
        ]
        
        # Reorder by importance (required fields first)
        minimal_fields.sort(key=lambda f: (not f.required, missing_keys.index(f.key)))
        
        # Enhance help text with context from user input
        for field in minimal_fields:
            if user_text and not field.help_text:
                # Could add contextual help here
                pass
        
        return ClarificationSchema(
            domain=full_schema.domain,
            title=full_schema.title,
            description=f"我们发现还需要 {len(minimal_fields)} 个信息来完整理解您的需求。",
            fields=minimal_fields
        )


class ClarificationProcessor:
    """Process clarification answers and merge with user input."""
    
    @staticmethod
    def process_answers(
        session: TaskSession,
        answers: Dict[str, any]
    ) -> ClarificationAnswers:
        """
        Process user's clarification answers.
        
        Preserves all answers, marks inferred vs explicit.
        """
        clarification_answers = ClarificationAnswers(
            answers=answers,
            inferred_answers={}
        )
        
        return clarification_answers
    
    @staticmethod
    def infer_missing_answers(
        session: TaskSession,
        schema: ClarificationSchema,
        provided_answers: Dict[str, any]
    ) -> Dict[str, any]:
        """
        Infer answers for fields not provided by user.
        
        Uses context from user input and domain knowledge.
        """
        inferred = {}
        text = session.user_input.text.lower()
        
        for field in schema.fields:
            if field.key in provided_answers:
                continue  # User provided this
            
            if field.field_type == "single_choice":
                # Try to infer from text
                for option in field.options:
                    if option["label"].lower() in text or option["value"].lower() in text:
                        inferred[field.key] = option["value"]
                        break
            
            elif field.field_type == "multi_choice":
                # Try to infer multiple options
                matched = []
                for option in field.options:
                    if option["label"].lower() in text or option["value"].lower() in text:
                        matched.append(option["value"])
                if matched:
                    inferred[field.key] = matched
            
            elif field.field_type in ["short_text", "multiline_text"]:
                # Extract relevant sentences from user input
                sentences = text.split("。")
                relevant = [s.strip() for s in sentences if len(s.strip()) > 10]
                if relevant:
                    inferred[field.key] = relevant[0]
        
        return inferred


class ClarifyLayerV3:
    """Main clarification layer orchestrator - v3 with semantic understanding."""
    
    def __init__(self, llm_client=None):
        self.gap_detector = SemanticGapDetector(llm_client)
        self.schema_builder = IntelligentClarificationBuilder()
        self.processor = ClarificationProcessor()
    
    def process(self, session: TaskSession) -> Tuple[bool, Optional[ClarificationSchema]]:
        """
        Process clarification for a session using semantic understanding.
        
        Returns: (should_skip_clarification, schema_if_needed)
        """
        # Get domain-specific schema
        full_schema = get_clarification_schema(session.domain)
        
        # Detect gaps using semantic understanding
        missing_keys, field_scores, completeness = self.gap_detector.detect_gaps_semantic(
            session.user_input,
            full_schema
        )
        
        # Decide if we should skip
        should_skip = self.gap_detector.should_skip_clarification(completeness, len(missing_keys))
        
        logger.info(
            f"Clarification analysis: completeness={completeness:.2f}, "
            f"missing={len(missing_keys)}, should_skip={should_skip}"
        )
        
        if should_skip:
            # Infer any missing answers from context
            inferred = self.processor.infer_missing_answers(
                session, full_schema, {}
            )
            session.clarification_answers = ClarificationAnswers(
                answers={},
                inferred_answers=inferred
            )
            session.state = WorkflowState.SPEC_READY
            return True, None
        
        # Build minimal schema with only missing fields
        minimal_schema = self.schema_builder.build_minimal_schema(
            full_schema, missing_keys, session.user_input.text
        )
        
        session.clarification_schema = minimal_schema
        session.state = WorkflowState.CLARIFYING
        
        return False, minimal_schema
    
    def submit_answers(
        self,
        session: TaskSession,
        answers: Dict[str, any]
    ) -> None:
        """
        Submit clarification answers.
        
        Merges with inferred answers and moves to spec phase.
        """
        if not session.clarification_schema:
            return
        
        # Process answers
        clarification_answers = self.processor.process_answers(session, answers)
        
        # Infer missing
        inferred = self.processor.infer_missing_answers(
            session,
            session.clarification_schema,
            answers
        )
        clarification_answers.inferred_answers = inferred
        
        session.clarification_answers = clarification_answers
        session.state = WorkflowState.SPEC_READY
        
        logger.info(
            f"Clarification submitted: {len(answers)} explicit answers, "
            f"{len(inferred)} inferred answers"
        )
