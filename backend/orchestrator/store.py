from __future__ import annotations

import threading
import uuid

from infrastructure.db import (
    STORE_BACKEND,
    WorkflowSessionRow,
    db_session,
    dump_json,
    init_mysql_schema,
    load_json,
    mysql_available,
)
from infrastructure.redis_client import delete as redis_delete
from infrastructure.redis_client import get_json as redis_get_json
from infrastructure.redis_client import set_json as redis_set_json
from infrastructure.redis_client import redis_available

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
        session_id: str | None = None,
    ) -> dict:
        if session_id is None:
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

    def delete(self, session_id: str) -> bool:
        """Delete a session by ID."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                return True
            return False


class MysqlWorkflowStore:
    def __init__(self):
        self._lock = threading.Lock()
        self._ready = init_mysql_schema()

    def create(
        self,
        text: str,
        preferred_executor: str | None,
        context: dict | None,
        task_type: str,
        session_id: str | None = None,
    ) -> dict:
        if session_id is None:
            session_id = str(uuid.uuid4())
        record = new_session_record(session_id, text, preferred_executor, context, task_type)
        with self._lock:
            with db_session() as db:
                db.add(
                    WorkflowSessionRow(
                        session_id=session_id,
                        state=record["state"],
                        payload=dump_json(record),
                        created_at=record["created_at"],
                        updated_at=record["updated_at"],
                    )
                )
            self._cache_session(record)
        return record

    def get(self, session_id: str) -> dict | None:
        cached = self._read_cache(session_id)
        if cached:
            return cached
        with self._lock:
            with db_session() as db:
                row = db.get(WorkflowSessionRow, session_id)
                if not row:
                    return None
                payload = load_json(row.payload)
                self._cache_session(payload)
                return payload

    def update(self, session_id: str, **changes) -> dict | None:
        with self._lock:
            with db_session() as db:
                row = db.get(WorkflowSessionRow, session_id)
                if not row:
                    return None
                payload = load_json(row.payload)
                payload.update(changes)
                payload["updated_at"] = now_iso()
                row.payload = dump_json(payload)
                row.state = payload.get("state", row.state)
                row.updated_at = payload["updated_at"]
                self._cache_session(payload)
                return payload

    def all_sessions(self) -> list[dict]:
        with self._lock:
            with db_session() as db:
                rows = db.query(WorkflowSessionRow).all()
                out = []
                for row in rows:
                    try:
                        out.append(load_json(row.payload))
                    except Exception:
                        continue
                return out

    def _cache_session(self, payload: dict) -> None:
        if not redis_available():
            return
        redis_set_json(f"session:{payload.get('session_id')}", payload, ex=3600)

    def _read_cache(self, session_id: str):
        if not redis_available():
            return None
        return redis_get_json(f"session:{session_id}")

    def invalidate(self, session_id: str) -> None:
        if not redis_available():
            return
        redis_delete(f"session:{session_id}")

    def delete(self, session_id: str) -> bool:
        """Delete a session by ID from both database and cache."""
        with self._lock:
            with db_session() as db:
                row = db.get(WorkflowSessionRow, session_id)
                if not row:
                    return False
                db.delete(row)
                self.invalidate(session_id)
                return True


def _build_store():
    if STORE_BACKEND == "mysql" and mysql_available():
        return MysqlWorkflowStore()
    return InMemoryWorkflowStore()


store = _build_store()
