from __future__ import annotations

import os

from flask import request

from infrastructure.errors import ERROR_CODES, error_response


PUBLIC_PATHS = {
    "/api/health",
    "/openapi.json",
}


def enforce_api_key_auth():
    enabled = os.getenv("AUTH_ENABLED", "false").strip().lower() == "true"
    if not enabled:
        return None

    if request.path in PUBLIC_PATHS:
        return None

    expected = os.getenv("API_KEY", "").strip()
    provided = request.headers.get("X-API-Key", "").strip()
    if not expected:
        return error_response(ERROR_CODES["INTERNAL_ERROR"], "Server API key is not configured.", 500)
    if provided != expected:
        return error_response(ERROR_CODES["UNAUTHORIZED"], "Unauthorized API key.", 401)
    return None
