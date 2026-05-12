# TaskForge

[中文说明](./README.zh-CN.md)

TaskForge is an AI task workflow backend + UI prototype.
It turns vague user requests into a structured workflow:

`Clarify -> Spec Align -> Preflight Check -> Execute -> Validate -> (Optional Repair)`

## What It Does

- Accepts natural language task requests
- Detects missing info and asks only required follow-up fields
- Routes to task handlers (`email`, `writing`, `code`, `generic`)
- Builds structured task specs
- Generates model-adapted prompts
- Supports execution adapters (`prompt_only`, `openai_compatible`, `local_lmstudio`)
- Runs pre-execution logic checks (plan graph for `email` and `generic`)
- Runs post-execution validation and one-pass repair attempt

## Tech Stack

- Backend: Python, Flask
- Frontend: React 18
- LLM/API: Gemini (classification/understanding path), OpenAI-compatible executor path
- Optional infra:
  - MySQL for workflow session persistence
  - Redis for session cache + idempotency response cache

## Quick Start

### 1) Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

Backend runs at `http://127.0.0.1:5001`.

### 2) Frontend

```bash
cd frontend
npm install
npm start
```

Frontend runs at `http://127.0.0.1:3000`.

## Optional Production-like Infra Setup

Start infra services (MySQL + Redis):

```bash
docker compose up -d mysql redis
```

Set environment variables in `backend/.env`:

```env
# Workflow store backend: memory | mysql
WORKFLOW_STORE_BACKEND=mysql

# MySQL (SQLAlchemy URL)
MYSQL_URL=mysql+pymysql://user:password@127.0.0.1:3306/taskforge?charset=utf8mb4

# Redis (optional but recommended)
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_PREFIX=taskforge
```

If `WORKFLOW_STORE_BACKEND=mysql` is set and MySQL is reachable, workflow sessions are persisted to MySQL.
If Redis is configured, session cache and idempotency cache are enabled.

### Initialize MySQL Schema (SQL file)

Option A (recommended): run SQL directly

```bash
mysql -u root -p < backend/sql/001_init_taskforge.sql
```

Option B: initialize via Python script (uses `MYSQL_URL`)

```bash
cd backend
python scripts/init_mysql.py
```

Option C: use Alembic migration

```bash
cd backend
alembic -c alembic.ini upgrade head
```

## API (Core)

- `POST /api/workflow/start`
- `POST /api/workflow/clarify`
- `POST /api/workflow/confirm_spec`
- `POST /api/workflow/execute`
- `POST /api/workflow/validate`
- `GET /openapi.json`
- `GET /metrics`
- `GET /api/health/liveness`
- `GET /api/health/readiness`

## Async API (v1)

- `POST /api/v1/workflow/start`
- `POST /api/v1/workflow/clarify`
- `POST /api/v1/workflow/confirm_spec`
- `POST /api/v1/workflow/execute` (returns `job_id`)
- `POST /api/v1/workflow/validate` (returns `job_id`)
- `GET /api/v1/jobs/{job_id}`

Legacy compatibility endpoint remains:

- `POST /api/analyze`

## Current Stage

This project is still MVP.
Main limitations today:

- No full async job queue yet
- No full observability stack yet
- Idempotency currently focused on workflow execute/validate response caching

## Security & Reliability Controls

- API key auth (optional): set `AUTH_ENABLED=true` and `API_KEY=...`, send `X-API-Key`
- Rate limit (optional, Redis required): set `RATE_LIMIT_ENABLED=true`
- Request trace header: every response includes `X-Request-Id`

## Run Celery Worker

```bash
cd backend
celery -A celery_app.celery worker -l INFO
```

Or run full stack with containers:

```bash
docker compose up -d api worker mysql redis
```

## Test

```bash
cd backend
pytest -q
```

Run integration tests (MySQL + Redis required):

```bash
pytest -q -m integration
```

## License

Internal/Personal project (adjust as needed).
