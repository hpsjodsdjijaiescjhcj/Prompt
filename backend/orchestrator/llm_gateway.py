"""
Unified LLM gateway for TaskForge execution.

Supports OpenAI-compatible providers used in this project:
- qwen: Alibaba Cloud DashScope compatible mode
- doubao: VolcEngine Ark compatible mode

The gateway never requires secrets at import time. If no provider is configured,
callers can fall back to deterministic local rendering.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import logging
import os
import urllib.error
import urllib.request

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class LLMProviderConfig:
    provider: str
    base_url: str
    api_key: str
    model: str

    @property
    def configured(self) -> bool:
        return bool(self.base_url and self.api_key and self.model)


@dataclass(frozen=True)
class LLMResponse:
    text: str
    provider: str
    model: str
    tokens_used: dict | None = None


class LLMGateway:
    """Small OpenAI-compatible chat completions client."""

    DEFAULTS = {
        "qwen": {
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-plus",
            "key_env": "QWEN_API_KEY",
            "base_env": "QWEN_BASE_URL",
            "model_env": "QWEN_MODEL",
        },
        "doubao": {
            "base_url": "https://ark.cn-beijing.volces.com/api/v3",
            "model": "doubao-seed-1-6-250615",
            "key_env": "DOUBAO_API_KEY",
            "base_env": "DOUBAO_BASE_URL",
            "model_env": "DOUBAO_MODEL",
        },
    }

    def __init__(self, provider: str | None = None):
        self.provider = (provider or os.getenv("LLM_PROVIDER") or "doubao").strip().lower()

    def get_config(self) -> LLMProviderConfig:
        provider = self.provider if self.provider in self.DEFAULTS else "doubao"
        defaults = self.DEFAULTS[provider]
        return LLMProviderConfig(
            provider=provider,
            base_url=os.getenv(defaults["base_env"], defaults["base_url"]).rstrip("/"),
            api_key=os.getenv(defaults["key_env"], "").strip(),
            model=os.getenv(defaults["model_env"], defaults["model"]).strip(),
        )

    def is_configured(self) -> bool:
        return self.get_config().configured

    def status(self) -> dict:
        config = self.get_config()
        return {
            "provider": config.provider,
            "model": config.model,
            "configured": config.configured,
            "base_url_configured": bool(config.base_url),
            "api_key_configured": bool(config.api_key),
        }

    def chat(
        self,
        prompt: str,
        system_prompt: str = "你是 TaskForge 的任务执行代理，输出最终可交付结果。",
        temperature: float = 0.3,
        max_tokens: int = 2048,
        timeout: int = 45,
    ) -> LLMResponse:
        config = self.get_config()
        if not config.configured:
            raise RuntimeError(f"{config.provider} provider is not fully configured")

        payload = {
            "model": config.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        req = urllib.request.Request(
            f"{config.base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            logger.warning("%s LLM request failed: HTTP %s", config.provider, exc.code)
            raise RuntimeError(f"{config.provider} request failed: HTTP {exc.code} {detail[:300]}") from exc
        except urllib.error.URLError as exc:
            logger.warning("%s LLM request failed: %s", config.provider, exc)
            raise RuntimeError(f"{config.provider} request failed: {exc}") from exc

        try:
            text = body["choices"][0]["message"]["content"].strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"{config.provider} response did not contain message content") from exc

        if not text:
            raise RuntimeError(f"{config.provider} returned empty output")

        return LLMResponse(
            text=text,
            provider=config.provider,
            model=config.model,
            tokens_used=body.get("usage"),
        )


def get_runtime_status() -> dict:
    return LLMGateway().status()
