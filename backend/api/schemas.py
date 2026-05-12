from __future__ import annotations

SCHEMAS = {
    "analyze_request": {
        "type": "object",
        "required": ["input"],
        "properties": {
            "input": {"type": "string", "minLength": 1},
        },
        "additionalProperties": False,
    },
    "workflow_start_request": {
        "type": "object",
        "required": ["text"],
        "properties": {
            "text": {"type": "string", "minLength": 1},
            "preferred_executor": {"type": ["string", "null"]},
            "context": {"type": "object"},
        },
        "additionalProperties": True,
    },
    "workflow_clarify_request": {
        "type": "object",
        "required": ["session_id", "answers"],
        "properties": {
            "session_id": {"type": "string", "minLength": 1},
            "answers": {"type": "object"},
        },
        "additionalProperties": True,
    },
    "workflow_confirm_request": {
        "type": "object",
        "required": ["session_id", "spec"],
        "properties": {
            "session_id": {"type": "string", "minLength": 1},
            "spec": {"type": "object"},
        },
        "additionalProperties": True,
    },
    "workflow_execute_request": {
        "type": "object",
        "required": ["session_id"],
        "properties": {
            "session_id": {"type": "string", "minLength": 1},
            "executor": {"type": "string"},
            "executor_config": {"type": "object"},
        },
        "additionalProperties": True,
    },
    "workflow_validate_request": {
        "type": "object",
        "required": ["session_id"],
        "properties": {
            "session_id": {"type": "string", "minLength": 1},
            "output": {"type": ["string", "null"]},
            "auto_revise": {"type": "boolean"},
        },
        "additionalProperties": True,
    },
}
