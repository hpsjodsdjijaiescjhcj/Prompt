# AI提示词管家（AI Prompt Router / Task Orchestrator）

一个面向多模型时代的 AI 智能路由与编排层：  
输入自然语言需求，系统完成任务识别、澄清补全、结构化对齐、模型推荐与提示词生成，并支持可选执行与验收。

## 1. 产品定位

- 解决“模型太多、不会选、不会写提示词”的问题
- 把“AI 怎么用”从单次问答升级为工作流：`Clarify -> Align(Spec) -> Execute -> Validate`
- 保留原有轻量能力，同时逐步过渡到编排体系

一句话：**AI 的智能路由层 + 任务编排层 + 提示词操作系统**。

## 2. 当前能力

### 2.1 后端（Flask）

- `POST /api/analyze`
  - 原有流程：任务分类 -> 模型推荐 -> 专属提示词
- `GET /api/history`
  - 返回最近历史记录（内存，重启丢失）
- `GET /api/health`
  - 返回服务健康状态和 LLM 可用性

- `POST /api/workflow/start`
  - 启动工作流会话（路由 + 澄清表单或直出 spec 草案）
- `POST /api/workflow/clarify`
  - 提交澄清答案，生成结构化 spec 草案
- `POST /api/workflow/confirm_spec`
  - 确认 spec，返回执行路由、推荐模型与生成提示词
- `POST /api/workflow/execute`
  - 调用执行器运行（`prompt_only` / `local_lmstudio` / `openai_compatible`）
- `POST /api/workflow/validate`
  - 输出验收（pass/fail + issues），支持一次 auto revise

### 2.2 前端（React）

- 聊天式输入 + 示例快捷触发
- 旧流程卡片视图 / 对比视图
- 新增 workflow 多步交互（澄清、spec 确认、执行与验收）
- 历史侧栏、复制提示词、状态提示

## 3. 编排工作流（V1）

### 3.1 会话状态

- `input_received`
- `clarifying`
- `spec_ready`
- `executing`
- `validating`
- `done`

### 3.2 任务处理器

- `email`
  - 邮件类任务，支持细化字段、规则验收
- `code`
  - 代码任务脚手架，支持 codex 风格提示词
- `writing`
  - 写作类任务澄清与结构化 spec
- `generic`
  - 通用澄清层（信息不足或未覆盖任务）
  - 对天气类查询会追加专项字段（地点/时间范围/单位等）
- `other`
  - 仅低置信度兜底时回退旧 `/api/analyze`

### 3.3 路由策略

- 优先：LLM 语义路由（`email | code | writing | generic | other`）
- 降级：分类器 + 规则兜底
- 核心策略：**信息不足优先进入 `generic` 澄清，不直接回退**

### 3.4 Clarify 校验

后端基于 schema 强校验：

- 必填校验（含条件必填 `required_when`）
- 条件显示逻辑（`show_when`）
- 字段类型校验（字符串、数字、布尔、枚举、多选）
- 数值边界校验（`min/max`）

## 4. 模型推荐与提示词

- 保留原推荐器能力（`backend/recommender.py`）
- 在 workflow 的 `confirm_spec` 中返回 `recommended_models`（Top 3）
- 提示词模板已升级为结构化专业模板（不再简单参数拼接）

## 5. 项目结构

```text
ai-prompt-manager/
├── backend/
│   ├── app.py
│   ├── classifier.py
│   ├── recommender.py
│   ├── prompt_generator.py
│   ├── llm_client.py
│   ├── config.py
│   ├── requirements.txt
│   └── orchestrator/
│       ├── service.py
│       ├── router.py
│       ├── executor.py
│       ├── store.py
│       ├── validator.py
│       ├── email_handler.py
│       ├── code_handler.py
│       ├── writing_handler.py
│       └── generic_handler.py
└── frontend/
    ├── src/
    │   ├── App.js
    │   ├── api.js
    │   └── components/
    └── package.json
```

## 6. 本地运行

### 6.1 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

默认地址：`http://localhost:5001`

### 6.2 启动前端

```bash
cd frontend
npm install
npm start
```

默认地址：`http://localhost:3000`

## 7. 配置说明

- 后端环境变量位于 `backend/.env`
- 关键配置在 `backend/config.py`：
  - `GEMINI_BASE_URL`
  - `GEMINI_API_KEY`
  - `GEMINI_MODEL`

说明：

- 若 LLM 不可用，系统会自动降级到本地规则/模板能力
- 默认执行器为 `prompt_only`（无需外部 API 即可使用）

## 8. 手工验证场景

### 场景 A：邮件

输入：`帮我写一封邮件，催供应商给发票`

预期：

- 进入 `clarifying`
- 提交后得到 `spec_ready`
- `confirm_spec` 返回提示词 + 推荐模型
- 若输出缺截止时间，`validate` 返回 `missing_deadline`

### 场景 B：写作

输入：`帮我写一篇小红书文案`

预期：

- 进入 `writing` 澄清流程
- 可在 spec 阶段编辑目标、约束、验收标准

### 场景 C：通用分析

输入：`帮我分析特斯拉商业模式`

预期：

- 进入 `generic`（可能直接 `spec_ready`，取决于语义明确度）
- `confirm_spec` 不应报错

### 场景 D：天气查询

输入：`纽约最近三天天气`

预期：

- generic 澄清出现天气专项字段（地点/时间范围/单位）
- 最终 prompt 保留原始请求与天气参数

## 9. 已知限制（V1）

- 会话与历史均为内存存储，重启丢失
- `code` handler 仍偏提示词与结构化输出，不是完整自动改仓库闭环
- 路由策略虽已语义化，但仍有降级规则

## 10. 下一步建议

1. 将 task schema 抽离为配置文件（减少代码级硬编码）
2. 加强 generic 的子域识别（法律、金融、教育等）
3. 增加持久化存储与用户偏好记忆
4. 打通执行器观测（耗时、失败原因、自动重试策略）

