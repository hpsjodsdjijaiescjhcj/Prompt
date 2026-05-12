from __future__ import annotations

import json
import os
from contextlib import contextmanager

from dotenv import load_dotenv

load_dotenv()

try:
    from sqlalchemy import Column, String, Text, create_engine
    from sqlalchemy.orm import declarative_base, sessionmaker
except Exception:  # pragma: no cover - optional dependency
    Column = DateTime = String = Text = None
    create_engine = None
    declarative_base = None
    sessionmaker = None


MYSQL_URL = os.getenv("MYSQL_URL", "").strip()
STORE_BACKEND = os.getenv("WORKFLOW_STORE_BACKEND", "memory").strip().lower()

Base = declarative_base() if declarative_base else None
engine = None
SessionLocal = None
WorkflowSessionRow = None
AnalyzeHistoryRow = None


if create_engine and MYSQL_URL:
    engine = create_engine(
        MYSQL_URL,
        pool_pre_ping=True,
        pool_recycle=1800,
        future=True,
    )
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


if Base:
    class WorkflowSessionRow(Base):
        __tablename__ = "workflow_sessions"

        session_id = Column(String(64), primary_key=True)
        state = Column(String(32), nullable=False)
        payload = Column(Text, nullable=False)
        created_at = Column(String(64), nullable=False)
        updated_at = Column(String(64), nullable=False)


    class AnalyzeHistoryRow(Base):
        __tablename__ = "analyze_history"

        id = Column(String(64), primary_key=True)
        payload = Column(Text, nullable=False)
        created_at = Column(String(64), nullable=False)


def mysql_available() -> bool:
    return bool(engine and SessionLocal and Base)


def init_mysql_schema() -> bool:
    if not mysql_available():
        return False
    try:
        Base.metadata.create_all(bind=engine)
        return True
    except Exception:
        return False


@contextmanager
def db_session():
    if not SessionLocal:
        raise RuntimeError("MySQL session factory not initialized")
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def dump_json(data: dict) -> str:
    return json.dumps(data, ensure_ascii=False)


def load_json(raw: str) -> dict:
    return json.loads(raw)
