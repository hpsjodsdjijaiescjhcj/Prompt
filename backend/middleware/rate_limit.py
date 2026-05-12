from __future__ import annotations

import os
import time

from flask import request

from infrastructure.errors import ERROR_CODES, error_response
from infrastructure.redis_client import get_redis_client, key as redis_key


def enforce_rate_limit():
    enabled = os.getenv("RATE_LIMIT_ENABLED", "false").strip().lower() == "true"
    if not enabled:
        return None

    client = get_redis_client()
    if not client:
        return None

    window_sec = int(os.getenv("RATE_LIMIT_WINDOW_SEC", "60"))
    max_req = int(os.getenv("RATE_LIMIT_MAX_REQ", "120"))

    identifier = (
        request.headers.get("X-API-Key")
        or request.headers.get("X-Forwarded-For")
        or request.remote_addr
        or "anonymous"
    )
    now_window = int(time.time() // window_sec)
    k = redis_key(f"ratelimit:{identifier}:{now_window}")

    pipe = client.pipeline()
    pipe.incr(k)
    pipe.expire(k, window_sec + 2)
    current, _ = pipe.execute()

    if int(current) > max_req:
        return error_response(ERROR_CODES["RATE_LIMITED"], "Rate limit exceeded.", 429)
    return None
