# TaskForge

[English Version](./README.md)

TaskForge 是一个 AI 任务编排原型系统（后端 + 前端）。
它把用户的模糊请求转成可执行流程：

`澄清 -> 规格对齐 -> 执行前校验 -> 执行 -> 验证 ->（可选）修复`

## 项目能力

- 接收自然语言任务请求
- 自动识别缺失信息并最小化追问
- 按任务类型路由到对应 handler（`email`、`writing`、`code`、`generic`）
- 构建结构化 Task Spec
- 生成模型适配提示词
- 支持执行器（`prompt_only`、`openai_compatible`、`local_lmstudio`）
- 执行前逻辑校验（`email` 和 `generic` 支持 plan graph）
- 执行后多层验证 + 单轮自动修复尝试

## 技术栈

- 后端：Python、Flask
- 前端：React 18
- 模型/API：Gemini（理解与分类链路）、OpenAI 兼容执行链路
- 可选基础设施：
  - MySQL：工作流会话持久化
  - Redis：会话缓存 + 幂等响应缓存

## 快速部署

### 1）启动后端

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python app.py
```

后端地址：`http://127.0.0.1:5001`

### 2）启动前端

```bash
cd frontend
npm install
npm start
```

前端地址：`http://127.0.0.1:3000`

## 可选：接入 MySQL / Redis

先启动基础设施（MySQL + Redis）：

```bash
docker compose up -d mysql redis
```

在 `backend/.env` 中设置：

```env
# 工作流存储后端：memory | mysql
WORKFLOW_STORE_BACKEND=mysql

# MySQL（SQLAlchemy URL）
MYSQL_URL=mysql+pymysql://user:password@127.0.0.1:3306/taskforge?charset=utf8mb4

# Redis（建议）
REDIS_URL=redis://127.0.0.1:6379/0
REDIS_PREFIX=taskforge
```

当 `WORKFLOW_STORE_BACKEND=mysql` 且 MySQL 可连接时，workflow 会话会落库。
配置 Redis 后，会启用会话缓存与幂等缓存。

### 初始化 MySQL 表结构（SQL 文件）

方式 A（推荐）：直接执行 SQL

```bash
mysql -u root -p < backend/sql/001_init_taskforge.sql
```

方式 B：通过 Python 脚本初始化（读取 `MYSQL_URL`）

```bash
cd backend
python scripts/init_mysql.py
```

方式 C：使用 Alembic 迁移

```bash
cd backend
alembic -c alembic.ini upgrade head
```

## 核心 API

- `POST /api/workflow/start`
- `POST /api/workflow/clarify`
- `POST /api/workflow/confirm_spec`
- `POST /api/workflow/execute`
- `POST /api/workflow/validate`
- `GET /openapi.json`
- `GET /metrics`
- `GET /api/health/liveness`
- `GET /api/health/readiness`

## 异步 API（v1）

- `POST /api/v1/workflow/start`
- `POST /api/v1/workflow/clarify`
- `POST /api/v1/workflow/confirm_spec`
- `POST /api/v1/workflow/execute`（返回 `job_id`）
- `POST /api/v1/workflow/validate`（返回 `job_id`）
- `GET /api/v1/jobs/{job_id}`

兼容旧接口：

- `POST /api/analyze`

## 当前阶段说明

项目仍处于 MVP 阶段，当前主要限制：

- 尚未接入完整异步任务队列
- 尚未完善可观测性体系（指标/追踪/告警）
- 幂等机制目前主要覆盖 workflow execute/validate 的响应缓存

## 安全与稳定性控制

- 可选 API Key 鉴权：设置 `AUTH_ENABLED=true` 与 `API_KEY=...`，请求头传 `X-API-Key`
- 可选限流（需 Redis）：设置 `RATE_LIMIT_ENABLED=true`
- 请求追踪：所有响应包含 `X-Request-Id`

## 启动 Celery Worker

```bash
cd backend
celery -A celery_app.celery worker -l INFO
```

或直接容器启动全栈：

```bash
docker compose up -d api worker mysql redis
```

## 测试

```bash
cd backend
pytest -q
```

运行集成测试（需要 MySQL + Redis）：

```bash
pytest -q -m integration
```

## License

个人项目（可按需调整）。
