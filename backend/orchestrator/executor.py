from __future__ import annotations

import json
import urllib.error
import urllib.request

from .spec import now_iso


def run_executor(
    executor: str,
    prompt: str,
    executor_config: dict | None,
    session_meta: dict | None = None,
) -> dict:
    cfg = executor_config or {}
    started_at = now_iso()

    if executor == "prompt_only":
        return {
            "executor": "prompt_only",
            "model": cfg.get("model") or "prompt_only",
            "raw_output": "",
            "tokens_estimate": None,
            "started_at": started_at,
            "finished_at": now_iso(),
        }

    if executor == "local_lmstudio":
        base_url = cfg.get("api_base_url") or "http://127.0.0.1:1234"
        model = cfg.get("model") or "local-model"
        api_key = cfg.get("api_key") or "lm-studio"
        return _openai_chat_completion(
            base_url=base_url,
            api_key=api_key,
            model=model,
            prompt=prompt,
            temperature=cfg.get("temperature", 0.2),
            max_tokens=cfg.get("max_tokens", 1200),
            started_at=started_at,
            executor_name="local_lmstudio",
        )

    if executor == "openai_compatible":
        base_url = cfg.get("api_base_url") or "https://api.openai.com"
        model = cfg.get("model") or "gpt-4o-mini"
        api_key = cfg.get("api_key") or ""
        if not api_key:
            return {
                "executor": executor,
                "model": model,
                "raw_output": "",
                "tokens_estimate": None,
                "started_at": started_at,
                "finished_at": now_iso(),
                "error": "Missing api_key for openai_compatible executor.",
            }
        return _openai_chat_completion(
            base_url=base_url,
            api_key=api_key,
            model=model,
            prompt=prompt,
            temperature=cfg.get("temperature", 0.2),
            max_tokens=cfg.get("max_tokens", 1200),
            started_at=started_at,
            executor_name="openai_compatible",
        )

    return {
        "executor": executor,
        "model": cfg.get("model") or "unknown",
        "raw_output": "",
        "tokens_estimate": None,
        "started_at": started_at,
        "finished_at": now_iso(),
        "error": f"Unsupported executor: {executor}",
    }


def _openai_chat_completion(
    base_url: str,
    api_key: str,
    model: str,
    prompt: str,
    temperature: float,
    max_tokens: int,
    started_at: str,
    executor_name: str,
) -> dict:
    url = base_url.rstrip("/") + "/v1/chat/completions"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a reliable execution agent."},
            {"role": "user", "content": prompt},
        ],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            raw_output = (
                body.get("choices", [{}])[0]
                .get("message", {})
                .get("content", "")
                .strip()
            )
            usage = body.get("usage") or {}
            tokens = usage.get("total_tokens")

            return {
                "executor": executor_name,
                "model": model,
                "raw_output": raw_output,
                "tokens_estimate": tokens,
                "started_at": started_at,
                "finished_at": now_iso(),
            }
    except urllib.error.HTTPError as exc:
        detail = ""
        try:
            detail = exc.read().decode("utf-8")
        except Exception:
            detail = str(exc)
        return {
            "executor": executor_name,
            "model": model,
            "raw_output": "",
            "tokens_estimate": None,
            "started_at": started_at,
            "finished_at": now_iso(),
            "error": f"HTTP {exc.code}: {detail}",
        }
    except Exception as exc:
        return {
            "executor": executor_name,
            "model": model,
            "raw_output": "",
            "tokens_estimate": None,
            "started_at": started_at,
            "finished_at": now_iso(),
            "error": str(exc),
        }
