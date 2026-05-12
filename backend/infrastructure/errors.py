from __future__ import annotations

from flask import jsonify, g


ERROR_CODES = {
    "BAD_REQUEST": "BAD_REQUEST",
    "SESSION_NOT_FOUND": "SESSION_NOT_FOUND",
    "INVALID_STATE": "INVALID_STATE",
    "IDEMPOTENCY_CONFLICT": "IDEMPOTENCY_CONFLICT",
    "RATE_LIMITED": "RATE_LIMITED",
    "UNAUTHORIZED": "UNAUTHORIZED",
    "INTERNAL_ERROR": "INTERNAL_ERROR",
    "NOT_FOUND": "NOT_FOUND",
}


def error_response(code: str, message: str, status: int):
    payload = {
        "error": {
            "code": code,
            "message": message,
            "request_id": getattr(g, "request_id", ""),
        }
    }
    return jsonify(payload), status
