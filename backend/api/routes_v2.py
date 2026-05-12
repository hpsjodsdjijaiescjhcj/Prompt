"""
API Routes v2 - Orchestration Service Endpoints

Exposes the complete workflow orchestration service via REST API.
"""

from flask import Blueprint, request, jsonify
import logging

from orchestrator.service_v2 import OrchestrationService

logger = logging.getLogger(__name__)

# Create blueprint
orchestration_bp = Blueprint('orchestration', __name__, url_prefix='/api/v2')

# Initialize service (should be injected in production)
_service: OrchestrationService = None


def init_orchestration_service(service: OrchestrationService):
    """Initialize the orchestration service."""
    global _service
    _service = service


def get_service() -> OrchestrationService:
    """Get the orchestration service."""
    if _service is None:
        raise RuntimeError("Orchestration service not initialized")
    return _service


# ════════════════════════════════════════════════════════════════════════════
# SESSION MANAGEMENT
# ════════════════════════════════════════════════════════════════════════════

@orchestration_bp.route('/sessions', methods=['POST'])
def create_session():
    """
    Create a new task session.
    
    Request body:
    {
        "text": "user input text",
        "selected_domains": ["domain1", "domain2"],
        "selected_characteristics": ["char1", "char2"]
    }
    
    Response:
    {
        "session_id": "...",
        "domain": "...",
        "characteristics": [...],
        "routing_confidence": 0.95,
        "state": "clarifying"
    }
    """
    try:
        data = request.get_json()
        user_text = data.get('text', '').strip()
        selected_domains = data.get('selected_domains', [])
        selected_characteristics = data.get('selected_characteristics', [])
        
        if not user_text:
            return jsonify({"error": "User text is required"}), 400
        
        service = get_service()
        session = service.create_session(user_text, selected_domains, selected_characteristics)
        
        return jsonify(session.to_dict()), 201
    
    except Exception as e:
        logger.error(f"Error creating session: {e}")
        return jsonify({"error": str(e)}), 500


@orchestration_bp.route('/sessions/<session_id>', methods=['GET'])
def get_session(session_id: str):
    """Get session state."""
    try:
        service = get_service()
        session_data = service.get_session(session_id)
        return jsonify(session_data), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return jsonify({"error": str(e)}), 500


@orchestration_bp.route('/sessions', methods=['GET'])
def list_sessions():
    """List all sessions."""
    try:
        service = get_service()
        sessions = service.list_sessions()
        return jsonify({"sessions": sessions}), 200
    
    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        return jsonify({"error": str(e)}), 500


@orchestration_bp.route('/sessions/<session_id>', methods=['DELETE'])
def delete_session(session_id: str):
    """Delete a session by ID."""
    try:
        service = get_service()
        success = service.delete_session(session_id)
        
        if not success:
            return jsonify({"error": "Session not found"}), 404
        
        return jsonify({"message": "Session deleted successfully"}), 200
    
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════════════════
# CLARIFICATION PHASE
# ════════════════════════════════════════════════════════════════════════════

@orchestration_bp.route('/sessions/<session_id>/clarification', methods=['POST'])
def process_clarification(session_id: str):
    """
    Process clarification for a session.
    
    Response:
    {
        "should_skip": bool,
        "schema": {...} or null,
        "session_state": "..."
    }
    """
    try:
        service = get_service()
        result = service.process_clarification(session_id)
        return jsonify(result), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error processing clarification: {e}")
        return jsonify({"error": str(e)}), 500


@orchestration_bp.route('/sessions/<session_id>/clarification/answers', methods=['POST'])
def submit_clarification_answers(session_id: str):
    """
    Submit clarification answers.
    
    Request body:
    {
        "answers": {
            "field_key": "value",
            ...
        }
    }
    
    Response:
    {
        "success": bool,
        "session_state": "...",
        "next_step": "..."
    }
    """
    try:
        data = request.get_json()
        answers = data.get('answers', {})
        
        service = get_service()
        result = service.submit_clarification_answers(session_id, answers)
        
        return jsonify(result), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error submitting answers: {e}")
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════════════════
# SPECIFICATION PHASE
# ════════════════════════════════════════════════════════════════════════════

@orchestration_bp.route('/sessions/<session_id>/specification', methods=['POST'])
def align_specification(session_id: str):
    """
    Align and build task specification.
    
    Response:
    {
        "success": bool,
        "specification": {...},
        "session_state": "...",
        "next_step": "..."
    }
    """
    try:
        service = get_service()
        result = service.align_specification(session_id)
        return jsonify(result), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error aligning specification: {e}")
        return jsonify({"error": str(e)}), 500


@orchestration_bp.route('/sessions/<session_id>/specification', methods=['PATCH'])
def update_specification(session_id: str):
    """
    Update specification.
    
    Request body:
    {
        "objective": "...",
        "context": {...},
        "constraints": {...},
        "output_format": {...},
        "acceptance_criteria": [...]
    }
    
    Response:
    {
        "success": bool,
        "specification": {...}
    }
    """
    try:
        data = request.get_json()
        
        service = get_service()
        result = service.update_specification(session_id, data)
        
        return jsonify(result), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error updating specification: {e}")
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════════════════
# PREFLIGHT PHASE
# ════════════════════════════════════════════════════════════════════════════

@orchestration_bp.route('/sessions/<session_id>/preflight', methods=['POST'])
def run_preflight(session_id: str):
    """
    Run preflight validation.
    
    Response:
    {
        "passed": bool,
        "issues": [...],
        "risk_level": "...",
        "recovery_suggestions": [...],
        "session_state": "...",
        "next_step": "..."
    }
    """
    try:
        service = get_service()
        result = service.run_preflight(session_id)
        return jsonify(result), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error running preflight: {e}")
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════════════════
# EXECUTION PHASE
# ════════════════════════════════════════════════════════════════════════════

@orchestration_bp.route('/sessions/<session_id>/execute', methods=['POST'])
def execute(session_id: str):
    """
    Execute the task.
    
    Response:
    {
        "success": bool,
        "output": "...",
        "execution_time_ms": 1234,
        "model_used": "...",
        "next_step": "..."
    }
    """
    try:
        service = get_service()
        result = service.execute(session_id)
        
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error executing: {e}")
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════════════════
# VALIDATION PHASE
# ════════════════════════════════════════════════════════════════════════════

@orchestration_bp.route('/sessions/<session_id>/validate', methods=['POST'])
def validate_output(session_id: str):
    """
    Validate execution output.
    
    Response:
    {
        "passed": bool,
        "issues": [...],
        "risk_level": "...",
        "can_repair": bool,
        "session_state": "...",
        "next_step": "..."
    }
    """
    try:
        service = get_service()
        result = service.validate_output(session_id)
        return jsonify(result), 200
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Error validating: {e}")
        return jsonify({"error": str(e)}), 500


# ════════════════════════════════════════════════════════════════════════════
# HEALTH CHECK
# ════════════════════════════════════════════════════════════════════════════

@orchestration_bp.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "orchestration",
        "version": "2.0"
    }), 200
