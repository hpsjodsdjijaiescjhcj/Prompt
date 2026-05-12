# AI 任务编排系统 v2 - 架构文档

## 核心定位

这是一个**企业级任务编排与可靠性交付系统**，不是模型聊天壳。

**核心价值**：把用户一句模糊需求，变成"可执行、可验证、可回退、可持续优化"的任务流程。

---

## 系统架构

### 完整工作流

```
用户输入
   ↓
[1] 分类与路由 (Classification)
   ↓
[2] 澄清 (Clarification) - 最少必要提问
   ↓
[3] 规格对齐 (Specification Alignment) - 语义重写
   ↓
[4] 预检 (Preflight) - 逻辑门控
   ↓
[5] 执行 (Execution) - 异步任务
   ↓
[6] 验证 (Validation) - 多层校验
   ↓
完成或修复
```

---

## 核心模块

### 1. 分类与路由 (`task_taxonomy_v2.py`)

**职责**：语义理解用户意图，分类到具体领域

**支持的领域**：
- `COMMUNICATION` - 邮件、消息、沟通
- `CONTENT_CREATION` - 文章、文案、创意
- `TECHNICAL` - 代码、架构、调试
- `ANALYSIS` - 分析、研究、报告
- `OPERATIONS` - 流程、优化、管理
- `COMPLIANCE` - 法律、合规、风险
- `STRATEGY` - 战略、规划、决策
- `UNKNOWN` - 未知领域（降级处理）

**特点**：
- 不依赖硬编码关键词，使用语义标记
- 返回置信度分数
- 自动推断任务特征（创意、分析、程序化等）

**输出**：
```python
domain: TaskDomain
characteristics: List[TaskCharacteristic]
confidence: float  # 0.0-1.0
```

---

### 2. 澄清层 (`clarify_layer_v2.py`)

**职责**：最少必要提问，补充缺失信息

**核心原则**：
- 如果用户输入已 >80% 完整，跳过澄清
- 只问真正缺失的字段
- 保存所有用户输入，不允许丢失

**工作流**：
1. 检测缺口（目标、对象、上下文、约束、验收标准）
2. 计算完整度分数
3. 决定是否跳过或显示最小化表单
4. 推断缺失答案（从用户输入中提取）

**输出**：
```python
should_skip: bool
schema: ClarificationSchema | None  # 最小化表单
completeness: float
```

---

### 3. 规格对齐层 (`spec_alignment_v2.py`)

**职责**：把用户意图转换成结构化执行合同

**特点**：
- 语义重写（换词不换意思）
- 完整映射所有澄清字段
- 专业化表述整理
- 用户可随时编辑

**生成的规格包含**：
```python
objective: str              # 目标
context: Dict              # 背景信息
constraints: Dict          # 约束条件
output_format: Dict        # 输出格式
acceptance_criteria: List  # 验收标准
```

---

### 4. 预检门控 (`preflight_v2.py`)

**职责**：执行前逻辑校验，不允许"跳过装作做了"

**检查项**：
- ✓ 规格完整性（所有必要字段）
- ✓ 约束一致性（是否有冲突）
- ✓ 验收映射（标准是否可验证）
- ✓ 领域特定规则（如技术任务需要技术栈）

**失败时**：
- 明确告诉用户缺哪一步
- 提供修复建议
- 回流到澄清或规格编辑

**输出**：
```python
passed: bool
issues: List[ValidationIssue]
risk_level: RiskLevel  # LOW/MEDIUM/HIGH/CRITICAL
recovery_suggestions: List[str]
```

---

### 5. 执行层 (`service_v2.py`)

**职责**：协调所有层，执行任务

**特点**：
- 异步任务队列支持
- 幂等与重复提交保护
- 可查询状态
- 支持多种执行器（prompt_only, openai-compatible, local）

**执行流程**：
1. 构建执行提示词
2. 调用 LLM 客户端
3. 记录执行时间和模型信息
4. 保存结果

---

### 6. 验证层 (`validation_v2.py`)

**职责**：多层验证输出，支持单轮自动修复

**验证阶段**：
1. **格式验证** - 输出结构是否匹配
2. **约束验证** - 是否遵守所有约束
3. **验收验证** - 是否满足所有标准

**特点**：
- 不只是 Pass/Fail，给出可定位问题
- 提供修复建议
- 支持单轮 auto-revise

**输出**：
```python
passed: bool
issues: List[ValidationIssue]
risk_level: RiskLevel
can_repair: bool  # 是否可自动修复
```

---

## 前端架构

### 主视图 (`WorkflowOrchestrator.js`)

**布局**：
```
┌─────────────────────────────────────────────────┐
│  📝 ❓ 📋 ✓ ⚙️ ✅  (阶段进度条)                 │
├─────────────────────────────────────────────────┤
│                                                 │
│  当前阶段内容                                   │
│  - 表单 / 显示 / 结果                           │
│                                                 │
│  [继续 →] 按钮                                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

**特点**：
- 每阶段都能看到完整用户输入快照
- 显示当前规格和预检状态
- 用户始终知道系统在哪一步
- 为什么被拦截、下一步怎么过

### API 层 (`api_v2.js`)

**端点**：
```
POST   /api/v2/sessions                          # 创建会话
GET    /api/v2/sessions/{id}                     # 获取会话
POST   /api/v2/sessions/{id}/clarification       # 处理澄清
POST   /api/v2/sessions/{id}/clarification/answers  # 提交答案
POST   /api/v2/sessions/{id}/specification       # 对齐规格
PATCH  /api/v2/sessions/{id}/specification       # 编辑规格
POST   /api/v2/sessions/{id}/preflight           # 运行预检
POST   /api/v2/sessions/{id}/execute             # 执行任务
POST   /api/v2/sessions/{id}/validate            # 验证输出
```

---

## 数据模型

### TaskSession

```python
session_id: str
user_input: UserInput
domain: TaskDomain
characteristics: List[TaskCharacteristic]
routing_confidence: float

# 澄清阶段
clarification_schema: ClarificationSchema | None
clarification_answers: ClarificationAnswers | None

# 规格阶段
specification: TaskSpecification | None

# 预检阶段
preflight_validation: ValidationResult | None

# 执行阶段
execution_result: ExecutionResult | None

# 验证阶段
output_validation: ValidationResult | None

# 状态
state: WorkflowState
created_at: datetime
updated_at: datetime
```

### TaskSpecification

```python
domain: TaskDomain
objective: str
context: Dict[str, Any]
constraints: Dict[str, Any]
output_format: Dict[str, Any]
acceptance_criteria: List[str]
```

---

## 集成指南

### 后端集成

```python
from backend.orchestrator.service_v2 import OrchestrationService
from backend.api.routes_v2 import orchestration_bp, init_orchestration_service

# 初始化服务
service = OrchestrationService(llm_client=llm_client, store=session_store)
init_orchestration_service(service)

# 注册蓝图
app.register_blueprint(orchestration_bp)
```

### 前端集成

```javascript
import APIClient from './api_v2';
import WorkflowOrchestrator from './components/workflow/WorkflowOrchestrator';

// 使用 API 客户端
const session = await APIClient.createSession(userText);

// 使用工作流组件
<WorkflowOrchestrator 
  userText={userText}
  onComplete={handleComplete}
/>
```

---

## 关键特性

### 1. 最少必要提问
- 自动检测完整度
- 只问缺失的字段
- 推断可推断的答案

### 2. 语义理解
- 不依赖硬编码关键词
- 支持多个特征组合
- 置信度评分

### 3. 显式逻辑门控
- 预检不允许跳过
- 清晰的失败原因
- 可操作的修复建议

### 4. 完整可追踪
- 所有输入都被保存
- 每个阶段都有快照
- 支持历史回溯

### 5. 多层验证
- 格式 + 约束 + 验收
- 可定位问题
- 单轮自动修复

---

## 可靠性保证

### 数据持久化
- Redis 缓存会话
- MySQL 存储历史
- 支持会话恢复

### 错误处理
- 结构化错误
- request_id 追踪
- 详细日志

### 可观测性
- Prometheus 指标
- 健康探针（liveness/readiness）
- 分级日志

---

## 后续扩展

### 短期
- [ ] 集成更强模型
- [ ] 支持多轮对话修复
- [ ] 添加用户反馈循环

### 中期
- [ ] 支持工作流模板
- [ ] 添加协作功能
- [ ] 支持批量任务

### 长期
- [ ] 自学习与优化
- [ ] 支持自定义领域
- [ ] 企业级权限管理

---

## 技术栈

**后端**：
- Python 3.9+
- Flask
- SQLAlchemy
- Redis
- MySQL

**前端**：
- React 18+
- Fetch API
- CSS3

**部署**：
- Docker
- Docker Compose
- Kubernetes (可选)

---

## 文件结构

```
backend/orchestrator/
├── domain_model.py           # 核心数据模型
├── task_taxonomy_v2.py       # 分类与路由
├── clarify_layer_v2.py       # 澄清层
├── spec_alignment_v2.py      # 规格对齐
├── preflight_v2.py           # 预检门控
├── validation_v2.py          # 验证层
├── service_v2.py             # 服务编排

backend/api/
├── routes_v2.py              # API 路由

frontend/src/
├── api_v2.js                 # API 客户端
├── components/workflow/
│   ├── WorkflowOrchestrator.js    # 主工作流组件
│   └── WorkflowOrchestrator.css   # 样式
```

---

## 使用示例

### 完整流程

```javascript
// 1. 创建会话
const session = await APIClient.createSession("帮我写一封给客户的邮件");

// 2. 处理澄清
const clarify = await APIClient.processClarification(session.session_id);
if (!clarify.should_skip) {
  // 显示表单，用户填写
  await APIClient.submitClarificationAnswers(session.session_id, answers);
}

// 3. 对齐规格
await APIClient.alignSpecification(session.session_id);

// 4. 运行预检
const preflight = await APIClient.runPreflight(session.session_id);
if (!preflight.passed) {
  // 显示问题和建议
  // 用户可编辑规格后重试
}

// 5. 执行
const result = await APIClient.execute(session.session_id);

// 6. 验证
const validation = await APIClient.validateOutput(session.session_id);
if (validation.passed) {
  // 完成
} else {
  // 显示问题，用户可修复
}
```

---

## 性能指标

- **澄清延迟**：< 100ms
- **规格生成**：< 200ms
- **预检验证**：< 150ms
- **执行时间**：取决于 LLM（通常 1-10s）
- **验证延迟**：< 200ms

---

## 安全考虑

- ✓ 输入验证
- ✓ 输出清理
- ✓ 会话隔离
- ✓ 错误不泄露敏感信息
- ✓ 支持 RBAC（可选）

---

## 许可证

MIT
