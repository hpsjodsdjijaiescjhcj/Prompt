from __future__ import annotations


DEFAULT_PROJECT_MEMORY = {
    "writing_style": "natural_low_ai_tone",
    "default_output_preference": "direct",
    "ask_only_necessary_clarifications": True,
}


def initialize_project_memory(context: dict | None = None) -> dict:
    context = context or {}
    incoming = context.get("project_memory") if isinstance(context, dict) else None
    memory = dict(DEFAULT_PROJECT_MEMORY)
    if isinstance(incoming, dict):
        memory.update(incoming)
    return memory


def merge_project_memory(current: dict | None, updates: dict | None) -> dict:
    merged = dict(current or {})
    if isinstance(updates, dict):
        merged.update(updates)
    return merged
