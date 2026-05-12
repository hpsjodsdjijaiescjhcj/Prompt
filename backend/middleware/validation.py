from __future__ import annotations

try:
    from jsonschema import ValidationError, validate
except Exception:  # pragma: no cover
    ValidationError = Exception
    validate = None

from infrastructure.errors import ERROR_CODES, error_response


def validate_json_payload(payload: dict, schema: dict):
    if not validate:
        return None
    try:
        validate(instance=payload, schema=schema)
    except ValidationError as exc:
        return error_response(ERROR_CODES["BAD_REQUEST"], f"JSON schema validation failed: {exc.message}", 400)
    return None
