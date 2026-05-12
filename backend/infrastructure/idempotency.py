from __future__ import annotations

import uuid

from .redis_client import get_json, set_json
from .redis_client import delete as redis_delete
from .redis_client import set_if_absent


IDEMPOTENCY_TTL_SECONDS = 60 * 30
LOCK_TTL_SECONDS = 60 * 5


def read_cached_response(idempotency_key: str):
    if not idempotency_key:
        return None
    return get_json(f"idempotency:{idempotency_key}")


def cache_response(idempotency_key: str, payload: dict):
    if not idempotency_key:
        return False
    return set_json(f"idempotency:{idempotency_key}", payload, ex=IDEMPOTENCY_TTL_SECONDS)


def acquire_lock(idempotency_key: str) -> str | None:
    if not idempotency_key:
        return None
    token = str(uuid.uuid4())
    locked = set_if_absent(f"idempotency_lock:{idempotency_key}", token, ex=LOCK_TTL_SECONDS)
    return token if locked else None


def release_lock(idempotency_key: str):
    if not idempotency_key:
        return False
    return redis_delete(f"idempotency_lock:{idempotency_key}")
