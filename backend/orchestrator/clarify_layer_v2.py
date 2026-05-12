"""
Clarification Layer v2 - Minimal Necessary Questions

Core principle: Only ask what's truly missing.
- If user input is already complete, skip or minimize clarification.
- Detect gaps: objective, context, constraints, acceptance criteria.
- Preserve all user input - nothing gets lost.
"""

from typing import Dict, List, Optional, Tuple
from orchestrator.domain_model import (
    TaskSession, ClarificationSchema, ClarificationAnswers,
    WorkflowState, UserInput
)
from orchestrator.task_taxonomy_v2 import get_clarification_schema


class ClarificationGapDetector:
    """Detect what information is actually missing."""
    
    @staticmethod
    def detect_gaps(user_input: UserInput, domain_schema: ClarificationSchema) -> Tuple[List[str], float]:
        """
        Detect which fields are truly necessary and missing.
        
        Returns: (missing_field_keys, completeness_score)
        """
        text = user_input.text.lower()
        missing = []
        completeness = 0.0
        
        # Check required fields
        required_fields = domain_schema.required_fields()
        total_required = len(required_fields)
        
        if total_required == 0:
            return [], 1.0
        
        for field in required_fields:
            # Simple heuristic: check if field keywords appear in text
            field_keywords = field.label.lower().split()
            found = any(kw in text for kw in field_keywords)
            
            if not found:
                missing.append(field.key)
            else:
                completeness += 1.0
        
        completeness = completeness / total_required if total_required > 0 else 1.0
        
        return missing, completeness
    
    @staticmethod
    def should_skip_clarification(completeness_score: float) -> bool:
        """
        Decide if clarification can be skipped.
        
        If user input is already >80% complete, skip clarification.
        """
        return completeness_score >= 0.8


class MinimalClarificationBuilder:
    """Build minimal clarification form with only necessary fields."""
    
    @staticmethod
    def build_minimal_schema(
        full_schema: ClarificationSchema,
        missing_keys: List[str]
    ) -> ClarificationSchema:
        """
        Build a minimal schema with only missing required fields.
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
        
        return ClarificationSchema(
            domain=full_schema.domain,
            title=full_schema.title,
            description=full_schema.description,
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


class ClarifyLayer:
    """Main clarification layer orchestrator."""
    
    def __init__(self):
        self.gap_detector = ClarificationGapDetector()
        self.schema_builder = MinimalClarificationBuilder()
        self.processor = ClarificationProcessor()
    
    def process(self, session: TaskSession) -> Tuple[bool, Optional[ClarificationSchema]]:
        """
        Process clarification for a session.
        
        Returns: (should_skip_clarification, schema_if_needed)
        """
        # Get domain-specific schema
        full_schema = get_clarification_schema(session.domain)
        
        # Detect gaps
        missing_keys, completeness = self.gap_detector.detect_gaps(
            session.user_input,
            full_schema
        )
        
        # Decide if we should skip
        should_skip = self.gap_detector.should_skip_clarification(completeness)
        
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
        
        # Build minimal schema
        minimal_schema = self.schema_builder.build_minimal_schema(
            full_schema, missing_keys
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
