from __future__ import annotations

from collections import defaultdict
from typing import Callable


HookHandler = Callable[[dict], dict | None]


class HookManager:
    SUPPORTED_EVENTS = {
        "before_clarify",
        "after_spec_generated",
        "before_execution",
        "after_execution",
        "before_final_output",
        "on_validation_failed",
    }

    def __init__(self) -> None:
        self._handlers: dict[str, list[HookHandler]] = defaultdict(list)

    def register(self, event: str, handler: HookHandler) -> None:
        if event not in self.SUPPORTED_EVENTS:
            raise ValueError(f"Unsupported hook event: {event}")
        self._handlers[event].append(handler)

    def emit(self, event: str, context: dict) -> dict:
        if event not in self.SUPPORTED_EVENTS:
            raise ValueError(f"Unsupported hook event: {event}")
        ctx = context
        trace = list(ctx.get("hook_trace") or [])
        for handler in self._handlers.get(event, []):
            maybe_ctx = handler(ctx)
            if isinstance(maybe_ctx, dict):
                ctx = maybe_ctx
            trace.append(
                {
                    "event": event,
                    "handler": getattr(handler, "__name__", "anonymous"),
                }
            )
        ctx["hook_trace"] = trace
        return ctx
