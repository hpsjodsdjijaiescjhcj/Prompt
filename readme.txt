# AI提示词管家（AI Prompt Router）

一个面向多模型时代的 AI 智能路由器：  
用户只需输入自然语言需求，系统自动完成任务理解、模型推荐，并生成可直接复制使用的模型专属提示词。

## 1. 产品定位

对应《AI智能路由器_产品需求文档.pdf》的核心方向：

- 解决“模型太多、不会选、不会写提示词”的问题
- 把“AI怎么用”这件事自动化：需求理解 -> 模型匹配 -> 提示词生成
- 先做轻量可落地 MVP，再逐步演进到多模型协作系统

一句话：**AI 的智能路由层 + 提示词操作系统**。

## 2. 当前已实现能力（代码现状）

### 后端（Flask）

- `POST /api/analyze`
  - 输入用户需求
  - 智能分类任务类型（写作/编程/学术/商业/搜索/推理）
  - 计算复杂度（low/medium/high）
  - 推荐 Top-N 模型（默认 3 个）
  - 为每个模型生成专属提示词
- `GET /api/history`
  - 返回最近历史分析记录（内存保存，重启丢失）
- `GET /api/health`
  - 返回服务健康状态和本地 LLM 可用性
- `POST /api/workflow/start`
  - 启动编排会话（任务识别 + 澄清表单）
- `POST /api/workflow/clarify`
  - 提交澄清答案，生成结构化 spec 草案
- `POST /api/workflow/confirm_spec`
  - 确认/编辑 spec，生成执行路由与可复制 prompts
- `POST /api/workflow/execute`
  - 按执行器运行任务（支持 `prompt_only` / `local_lmstudio` / `openai_compatible`）
- `POST /api/workflow/validate`
  - 校验输出并返回 pass/fail + issues；支持一次 auto revise

### 智能能力

- 分类器双模式：
  - 优先：本地 LLM（LM Studio OpenAI 兼容接口）
  - 降级：关键词匹配
- 推荐器：多维度评分
  - 能力匹配 + 复杂度权重 + 成本 + 速度 + 特殊加分
- 提示词生成：
  - 当前使用增强模板（速度更快）
  - 模板含 5 段结构：角色设定 / 任务描述 / 输出格式 / 约束条件 / 风格要求

### 前端（React）

- 聊天式输入体验 + 示例问题快捷触发
- 结果卡片视图与多模型对比视图切换
- 提示词复制、全部复制
- 历史记录侧栏
- LLM 状态提示（智能模式/基础模式）

## 3. 技术栈

- 前端：React 18 + react-scripts
- 后端：Flask + Flask-CORS
- LLM 接入：LM Studio（OpenAI 兼容 API）
- 配置与模型能力库：`backend/config.py`

## 4. 项目结构

```text
ai-prompt-manager/
├── frontend/
│   ├── src/
│   │   ├── App.js
│   │   ├── api.js
│   │   └── components/
│   └── package.json
├── backend/
│   ├── app.py
│   ├── classifier.py
│   ├── recommender.py
│   ├── prompt_generator.py
│   ├── llm_client.py
│   ├── config.py
│   └── requirements.txt
└── AI智能路由器_产品需求文档.pdf
```

## 5. 本地运行

### 5.1 启动后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

默认端口：`http://localhost:5001`

### 5.2 启动前端

```bash
cd frontend
npm install
npm start
```

默认地址：`http://localhost:3000`

## 6. 配置说明（可选）

在 `backend/config.py` 中可调整：

- `LLM_BASE_URL`：本地 LM Studio 服务地址（默认 `http://127.0.0.1:1234`）
- `LLM_MODEL`：用于分类/生成的本地模型名
- `MODELS`：模型能力评分、成本、速度、提示词风格等

若本地 LLM 不可用，系统会自动进入降级模式，仍可正常使用核心流程。

## 7. 与 PRD 对齐情况

已落地（MVP 核心）：

- 输入需求
- 模型推荐
- 生成提示词
- 多模型结果展示与对比（界面层）

未完全落地（后续）：

- 真实多模型 API 自动执行并返回答案（目前以“推荐 + 提示词”为主）
- 持久化历史、用户偏好学习、企业级权限与审计

## 8. 新增编排工作流（V1）

工作流状态：

- `input_received`
- `clarifying`
- `spec_ready`
- `executing`
- `validating`
- `done`

当前任务处理器：

- `email`（功能完整：澄清 -> spec -> prompt -> 执行 -> 规则校验）
- `code`（脚手架：澄清 -> spec -> codex 风格 prompt，支持 prompt-only）
- `other`（自动回退到旧的 `/api/analyze` 流程）

默认策略：

- 默认执行器是 `prompt_only`，即使没有外部模型 API 也可使用（可展示 spec + prompts）。

## 9. 手工验证场景

1. 邮件任务：
   - 输入：`帮我写一封邮件，催供应商给发票`
   - 应进入 `clarifying` 并返回表单；确认 spec 后可得到 prompts。
   - 若执行输出缺少截止日期，`/api/workflow/validate` 应返回 `missing_deadline` 问题。
2. 非编排任务：
   - 输入：`帮我总结一篇文章`
   - `workflow/start` 应返回 `task_type=other`，前端回退到旧分析卡片。
3. 代码任务（脚手架）：
   - 输入：`帮我给前端加一个按钮并接API`
   - 应进入 `code` 澄清表单并生成代码改动 prompt。

## 10. 下一阶段建议

结合 PRD，可按这个顺序推进：

1. 接入真实多模型调用（OpenAI/Anthropic/Google/DeepSeek）
2. 增加用户偏好记忆与路由个性化策略
3. 引入任务链（搜索型 AI -> 推理型 AI -> 写作型 AI）形成多模型协作闭环
