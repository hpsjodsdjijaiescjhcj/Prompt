from __future__ import annotations


def initialize_run_memory(context: dict | None = None) -> dict:
    context = context or {}
    incoming = context.get("run_memory") if isinstance(context, dict) else None
    base = {
        "events": [],
        "spec_snapshots": [],
        "validation_failures": [],
        "notes": [],
    }
    if isinstance(incoming, dict):
        base.update(incoming)
    return base


def append_run_note(run_memory: dict | None, note: str) -> dict:
    result = dict(run_memory or {})
    notes = list(result.get("notes") or [])
    notes.append(note)
    result["notes"] = notes[-30:]
    return result


def merge_run_memory(current: dict | None, updates: dict | None) -> dict:
    merged = dict(current or {})
    if isinstance(updates, dict):
        merged.update(updates)
    return merged
