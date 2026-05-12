from __future__ import annotations

import json
import os

from dotenv import load_dotenv

load_dotenv()

try:
    import redis
except Exception:  # pragma: no cover
    redis = None


REDIS_URL = os.getenv("REDIS_URL", "").strip()
REDIS_PREFIX = os.getenv("REDIS_PREFIX", "taskforge")

_client = None


def get_redis_client():
    global _client
    if _client is not None:
        return _client
    if not redis or not REDIS_URL:
        _client = False
        return _client
    try:
        _client = redis.Redis.from_url(REDIS_URL, decode_responses=True)
        _client.ping()
    except Exception:
        _client = False
    return _client


def redis_available() -> bool:
    return bool(get_redis_client())


def key(name: str) -> str:
    return f"{REDIS_PREFIX}:{name}"


def get_json(name: str):
    client = get_redis_client()
    if not client:
        return None
    raw = client.get(key(name))
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


def set_json(name: str, value, ex: int | None = None):
    client = get_redis_client()
    if not client:
        return False
    client.set(key(name), json.dumps(value, ensure_ascii=False), ex=ex)
    return True


def delete(name: str):
    client = get_redis_client()
    if not client:
        return False
    client.delete(key(name))
    return True


def set_if_absent(name: str, value: str, ex: int | None = None) -> bool:
    client = get_redis_client()
    if not client:
        return False
    return bool(client.set(key(name), value, nx=True, ex=ex))
