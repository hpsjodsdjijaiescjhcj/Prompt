# AI 任务编排系统 - 快速启动指南

## 📋 当前状态

✅ **已完成**
- 前端 UI 框架（企业级设计）
- 后端核心架构（7 层编排系统）
- 数据库 schema（MySQL + Redis）
- API 路由框架（v2）
- 工作流状态机

⏳ **待完成**
- AI API 集成（需要你提供 Key）
- 各层核心逻辑完善
- 端到端测试

---

## 🚀 立即行动清单

### 第 1 步：准备 AI API（今天）

你需要选择并准备至少 1 个 AI API Key：

**推荐方案 A（最稳妥）**
```
✓ OpenAI API Key        (主执行)
✓ Anthropic API Key     (高质量验证)
✓ Gemini API Key        (备选/分类)
```

**推荐方案 B（成本优先）**
```
✓ OpenAI API Key        (主执行)
✓ Gemini API Key        (备选)
```

**推荐方案 C（质量优先）**
```
✓ Anthropic API Key     (主执行)
✓ OpenAI API Key        (备选)
```

### 第 2 步：配置环境变量（今天）

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env，填入你的 API Key
# 最少需要填：
# - OPENAI_API_KEY 或 ANTHROPIC_API_KEY 或 GEMINI_API_KEY
# - MYSQL_* 数据库配置
# - REDIS_* 缓存配置
```

### 第 3 步：启动本地开发环境（今天）

```bash
# 后端
cd backend
pip install -r requirements.txt
python app.py

# 前端（新终端）
cd frontend
npm install
npm start
```

### 第 4 步：测试端到端流程（明天）

访问 `http://localhost:3000`，输入任务：
```
"帮我写一份产品需求文档，包括功能列表、用户故事、验收标准"
```

观察系统是否能：
1. ✓ 接收输入
2. ✓ 自动澄清（如果需要）
3. ✓ 生成规格
4. ✓ 预检验证
5. ✓ 执行任务
6. ✓ 验证结果

---

## 📦 需要准备的外部服务

### 必须
- [ ] **MySQL 8.0+**
  - 本地：`brew install mysql` 或 Docker
  - 云端：AWS RDS / 阿里云 RDS

- [ ] **Redis 6.0+**
  - 本地：`brew install redis` 或 Docker
  - 云端：AWS ElastiCache / 阿里云 Redis

- [ ] **AI API Key**（至少 1 个）
  - OpenAI: https://platform.openai.com/api-keys
  - Anthropic: https://console.anthropic.com/
  - Gemini: https://aistudio.google.com/

### 可选（后续补充）
- Embedding API（向量化）
- 向量数据库（Pinecone / Weaviate）
- 监控系统（Prometheus + Grafana）

---

## 🔧 本地快速启动（Docker）

如果你不想手动安装 MySQL 和 Redis：

```bash
# 启动 MySQL + Redis
docker-compose up -d

# 初始化数据库
python backend/scripts/init_mysql.py

# 启动后端
cd backend && python app.py

# 启动前端（新终端）
cd frontend && npm start
```

---

## 📝 核心文件说明

### 后端
```
backend/
├── app.py                          # Flask 主应用
├── config.py                       # 配置管理
├── llm_client.py                   # LLM 客户端（Gemini）
├── orchestrator/
│   ├── service_v2.py              # 核心编排服务
│   ├── clarify_layer_v2.py        # 澄清层
│   ├── spec_alignment_v2.py       # 规格对齐层
│   ├── preflight_v2.py            # 预检层
│   ├── validation_v2.py           # 验证层
│   ├── executor.py                # 执行器
│   └── task_taxonomy_v2.py        # 任务分类
├── api/
│   └── routes_v2.py               # API 路由
└── infrastructure/
    ├── db.py                      # 数据库连接
    ├── redis_client.py            # Redis 客户端
    └── logging_config.py          # 日志配置
```

### 前端
```
frontend/src/
├── App.js                         # 主应用
├── api_v2.js                      # API 客户端
├── components/
│   └── workflow/
│       ├── WorkflowContainer.jsx  # 主工作流 UI
│       ├── WorkflowContainer.css  # 样式
│       └── ...
└── i18n/                          # 国际化
```

---

## 🎯 系统架构概览

```
用户输入
   ↓
[输入层] → 接收自然语言任务
   ↓
[澄清层] → 自动识别缺口，最少必要提问
   ↓
[规格层] → 转换为结构化 Task Spec
   ↓
[预检层] → 逻辑校验，检查依赖闭包
   ↓
[执行层] → 调用 LLM 执行任务
   ↓
[验证层] → 多层验收，检查结果
   ↓
[完成] → 保存历史，支持回退
```

---

## 🔑 关键概念

### Task Spec（任务规格）
结构化合同，包含：
- `objective`: 任务目标
- `context`: 背景信息
- `constraints`: 约束条件
- `acceptance_criteria`: 验收标准
- `style`: 风格要求
- `executor_type`: 执行器类型

### Preflight Validation（预检验证）
执行前的逻辑门，检查：
- 输入完备性
- 依赖闭包
- 出口可达性
- 验收标准映射

### Executor（执行器）
支持多种执行方式：
- `openai-compatible`: OpenAI API
- `anthropic`: Anthropic API
- `gemini`: Google Gemini API
- `prompt_only`: 仅返回提示词
- `local`: 本地模型

---

## 📊 API 端点速查

### 工作流
```
POST   /api/v2/workflow/start              # 开始工作流
GET    /api/v2/workflow/{session_id}       # 获取工作流状态
POST   /api/v2/workflow/{session_id}/clarify
POST   /api/v2/workflow/{session_id}/spec
POST   /api/v2/workflow/{session_id}/preflight
POST   /api/v2/workflow/{session_id}/execute
POST   /api/v2/workflow/{session_id}/validate
```

### 历史
```
GET    /api/v2/history                     # 获取历史列表
GET    /api/v2/history/{session_id}        # 获取历史详情
```

### 健康检查
```
GET    /api/health                         # 健康检查
GET    /api/metrics                        # Prometheus 指标
```

---

## 🐛 常见问题

### Q: 启动时报 "GEMINI_API_KEY not found"
**A:** 这是正常的。系统会自动降级到关键词匹配。你可以：
1. 在 `.env` 中填入 API Key
2. 或者继续使用降级模式（功能受限）

### Q: 前端无法连接后端
**A:** 检查：
1. 后端是否运行在 `http://localhost:5000`
2. CORS 配置是否正确
3. 防火墙是否阻止

### Q: 数据库连接失败
**A:** 检查：
1. MySQL 是否运行
2. 用户名密码是否正确
3. 数据库是否已创建

---

## 📚 下一步学习

1. **理解 7 层编排系统**
   - 阅读 `ARCHITECTURE_V2.md`

2. **了解任务分类**
   - 查看 `backend/orchestrator/task_taxonomy_v2.py`

3. **学习 API 集成**
   - 查看 `backend/api/routes_v2.py`

4. **前端开发**
   - 查看 `frontend/src/components/workflow/`

---

## 💡 建议

1. **先用 Gemini 或 OpenAI 测试**
   - 快速验证系统流程
   - 不需要复杂配置

2. **逐步添加功能**
   - 先做基础流程
   - 再加高级特性（历史召回、自动修复等）

3. **定期备份数据**
   - MySQL 定期导出
   - Redis 持久化配置

4. **监控系统运行**
   - 查看日志
   - 监控 API 响应时间

---

## 📞 需要帮助？

当你准备好 API Key 时，告诉我：
1. 你选择了哪个 AI 提供商
2. 你的 API Key 格式（用于验证）
3. 你想要的执行器类型

我会帮你完成集成和测试。

---

**最后一句话：** 这个系统的核心价值不在于"接很多模型"，而在于"把模糊需求变成可执行、可验证、可优化的任务流程"。先把流程做扎实，模型只是执行引擎。

