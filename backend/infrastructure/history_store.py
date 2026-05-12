from __future__ import annotations

import threading

from .db import (
    STORE_BACKEND,
    AnalyzeHistoryRow,
    db_session,
    dump_json,
    init_mysql_schema,
    load_json,
    mysql_available,
)


class InMemoryHistoryStore:
    def __init__(self, maxlen: int = 200):
        from collections import deque

        self._lock = threading.Lock()
        self._items = deque(maxlen=maxlen)

    def append(self, item: dict):
        with self._lock:
            self._items.appendleft(item)

    def list(self) -> list[dict]:
        with self._lock:
            return list(self._items)

    def delete(self, item_id: str) -> bool:
        """Delete a history item by ID."""
        with self._lock:
            original_len = len(self._items)
            self._items = type(self._items)(
                (item for item in self._items if item.get("id") != item_id),
                maxlen=self._items.maxlen
            )
            return len(self._items) < original_len


class MysqlHistoryStore:
    def __init__(self, fallback: InMemoryHistoryStore):
        self._lock = threading.Lock()
        self._fallback = fallback
        self._ready = init_mysql_schema()

    def append(self, item: dict):
        if not self._ready:
            self._fallback.append(item)
            return
        with self._lock:
            with db_session() as db:
                db.add(
                    AnalyzeHistoryRow(
                        id=str(item.get("id")),
                        payload=dump_json(item),
                        created_at=str(item.get("timestamp", "")),
                    )
                )

    def list(self) -> list[dict]:
        if not self._ready:
            return self._fallback.list()
        with self._lock:
            with db_session() as db:
                rows = db.query(AnalyzeHistoryRow).order_by(AnalyzeHistoryRow.created_at.desc()).limit(200).all()
                out = []
                for row in rows:
                    try:
                        out.append(load_json(row.payload))
                    except Exception:
                        continue
                return out

    def delete(self, item_id: str) -> bool:
        """Delete a history item by ID."""
        if not self._ready:
            return self._fallback.delete(item_id)
        with self._lock:
            with db_session() as db:
                result = db.query(AnalyzeHistoryRow).filter(AnalyzeHistoryRow.id == str(item_id)).delete()
                return result > 0


def build_history_store() -> InMemoryHistoryStore | MysqlHistoryStore:
    fallback = InMemoryHistoryStore(maxlen=200)
    if STORE_BACKEND == "mysql" and mysql_available():
        return MysqlHistoryStore(fallback=fallback)
    return fallback
