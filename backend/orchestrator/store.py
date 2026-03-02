from __future__ import annotations

import threading
import uuid

from .spec import now_iso, new_session_record


class InMemoryWorkflowStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._sessions: dict[str, dict] = {}

    def create(
        self,
        text: str,
        preferred_executor: str | None,
        context: dict | None,
        task_type: str,
    ) -> dict:
        session_id = str(uuid.uuid4())
        record = new_session_record(session_id, text, preferred_executor, context, task_type)
        with self._lock:
            self._sessions[session_id] = record
        return record

    def get(self, session_id: str) -> dict | None:
        with self._lock:
            session = self._sessions.get(session_id)
            return dict(session) if session else None

    def update(self, session_id: str, **changes) -> dict | None:
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return None
            session.update(changes)
            session["updated_at"] = now_iso()
            return dict(session)

    def all_sessions(self) -> list[dict]:
        with self._lock:
            return [dict(v) for v in self._sessions.values()]


store = InMemoryWorkflowStore()
