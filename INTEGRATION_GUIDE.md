# 集成指南 - AI 任务编排系统 v2

## 快速开始

### 1. 后端集成

#### 步骤 1：在 `app.py` 中初始化服务

```python
from backend.orchestrator.service_v2 import OrchestrationService
from backend.api.routes_v2 import orchestration_bp, init_orchestration_service
from backend.llm_client import LLMClient
from backend.infrastructure.db import SessionStore

# 初始化 LLM 客户端
llm_client = LLMClient(api_key=os.getenv('OPENAI_API_KEY'))

# 初始化会话存储
session_store = SessionStore(db_session)

# 创建编排服务
orchestration_service = OrchestrationService(
    llm_client=llm_client,
    store=session_store
)

# 初始化 API 路由
init_orchestration_service(orchestration_service)

# 注册蓝图
app.register_blueprint(orchestration_bp)
```

#### 步骤 2：确保依赖已安装

```bash
pip install -r backend/requirements.txt
```

### 2. 前端集成

#### 步骤 1：导入组件和 API 客户端

```javascript
import APIClient from './api_v2';
import WorkflowOrchestrator from './components/workflow/WorkflowOrchestrator';
```

#### 步骤 2：在主应用中使用

```javascript
function App() {
  const [userText, setUserText] = useState('');
  const [showWorkflow, setShowWorkflow] = useState(false);

  const handleSubmit = (text) => {
    setUserText(text);
    setShowWorkflow(true);
  };

  const handleComplete = (session) => {
    console.log('Task completed:', session);
    // 处理完成逻辑
  };

  return (
    <div className="app">
      {!showWorkflow ? (
        <InputBox onSubmit={handleSubmit} />
      ) : (
        <WorkflowOrchestrator
          userText={userText}
          onComplete={handleComplete}
        />
      )}
    </div>
  );
}
```

### 3. 环境配置

#### 后端 `.env`

```
OPENAI_API_KEY=sk-...
DATABASE_URL=mysql://user:pass@localhost/taskforge
REDIS_URL=redis://localhost:6379
LOG_LEVEL=INFO
```

#### 前端 `.env`

```
REACT_APP_API_URL=http://localhost:5000/api
```

---

## 工作流详解

### 完整请求流程

```
用户输入 "帮我写一封给客户的邮件"
    ↓
[1] POST /api/v2/sessions
    → 分类为 COMMUNICATION
    → 返回 session_id
    ↓
[2] POST /api/v2/sessions/{id}/clarification
    → 检测完整度 (60%)
    → 返回最小化表单 (收件人、目标、语气)
    ↓
[3] 用户填写表单
    ↓
[4] POST /api/v2/sessions/{id}/clarification/answers
    → 保存答案
    → 推断缺失字段
    ↓
[5] POST /api/v2/sessions/{id}/specification
    → 生成结构化规格
    → 返回完整 spec
    ↓
[6] POST /api/v2/sessions/{id}/preflight
    → 验证规格完整性
    → 检查约束一致性
    → 返回通过/失败 + 建议
    ↓
[7] POST /api/v2/sessions/{id}/execute
    → 构建执行提示词
    → 调用 LLM
    → 返回输出
    ↓
[8] POST /api/v2/sessions/{id}/validate
    → 多层验证输出
    → 返回通过/失败 + 问题
    ↓
完成或修复
```

---

## API 端点详解

### 创建会话

```http
POST /api/v2/sessions
Content-Type: application/json

{
  "text": "帮我写一封给客户的邮件"
}
```

**响应**：
```json
{
  "session_id": "sess_abc123",
  "domain": "communication",
  "characteristics": ["generative"],
  "routing_confidence": 0.95,
  "state": "clarifying",
  "user_input": {
    "text": "帮我写一封给客户的邮件",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

### 处理澄清

```http
POST /api/v2/sessions/sess_abc123/clarification
```

**响应**：
```json
{
  "should_skip": false,
  "schema": {
    "domain": "communication",
    "title": "沟通任务澄清",
    "fields": [
      {
        "key": "recipient",
        "label": "收件人/对象",
        "field_type": "short_text",
        "required": true,
        "placeholder": "例如：我的经理、客户、团队成员"
      },
      {
        "key": "communication_goal",
        "label": "沟通目标",
        "field_type": "single_choice",
        "required": true,
        "options": [
          {"value": "inform", "label": "通知/告知"},
          {"value": "request", "label": "请求/询问"}
        ]
      }
    ]
  },
  "session_state": "clarifying"
}
```

### 提交澄清答案

```http
POST /api/v2/sessions/sess_abc123/clarification/answers
Content-Type: application/json

{
  "answers": {
    "recipient": "我的主要客户",
    "communication_goal": "inform",
    "tone_preference": "formal"
  }
}
```

**响应**：
```json
{
  "success": true,
  "session_state": "spec_ready",
  "next_step": "specification_alignment"
}
```

### 对齐规格

```http
POST /api/v2/sessions/sess_abc123/specification
```

**响应**：
```json
{
  "success": true,
  "specification": {
    "domain": "communication",
    "objective": "撰写专业邮件：通知主要客户关于新产品功能",
    "context": {
      "recipient": "我的主要客户",
      "domain": "communication"
    },
    "constraints": {
      "tone": "formal",
      "must_be_professional": true,
      "must_be_clear": true
    },
    "output_format": {
      "domain": "communication",
      "format": "email",
      "structure": ["greeting", "body", "call_to_action", "closing"]
    },
    "acceptance_criteria": [
      "语言清晰、无歧义",
      "符合预期的语气和风格",
      "适合发送给我的主要客户"
    ]
  },
  "session_state": "preflight_check",
  "next_step": "preflight_validation"
}
```

### 运行预检

```http
POST /api/v2/sessions/sess_abc123/preflight
```

**响应**：
```json
{
  "passed": true,
  "issues": [],
  "risk_level": "low",
  "recovery_suggestions": [],
  "session_state": "executing",
  "next_step": "execution"
}
```

### 执行任务

```http
POST /api/v2/sessions/sess_abc123/execute
```

**响应**：
```json
{
  "success": true,
  "output": "尊敬的客户，\n\n我们很高兴地通知您...",
  "execution_time_ms": 2345,
  "model_used": "gpt-4",
  "next_step": "validation"
}
```

### 验证输出

```http
POST /api/v2/sessions/sess_abc123/validate
```

**响应**：
```json
{
  "passed": true,
  "issues": [],
  "risk_level": "low",
  "can_repair": false,
  "session_state": "completed",
  "next_step": "completed"
}
```

---

## 错误处理

### 常见错误

#### 1. 会话不存在

```json
{
  "error": "Session not found: sess_invalid"
}
```

**处理**：创建新会话

#### 2. 预检失败

```json
{
  "passed": false,
  "issues": [
    {
      "issue_type": "missing_input",
      "severity": "error",
      "message": "技术栈未明确",
      "suggestion": "指定编程语言、框架、版本等"
    }
  ],
  "recovery_suggestions": [
    "请在规格中补充技术栈信息"
  ]
}
```

**处理**：
1. 显示问题给用户
2. 允许用户编辑规格
3. 重新运行预检

#### 3. 执行失败

```json
{
  "success": false,
  "error": "LLM client not configured"
}
```

**处理**：检查后端配置

---

## 前端状态管理

### 使用 React Hooks

```javascript
function useWorkflow(userText) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [currentPhase, setCurrentPhase] = useState('input');

  // 创建会话
  const createSession = async () => {
    try {
      setLoading(true);
      const result = await APIClient.createSession(userText);
      setSession(result);
      setCurrentPhase('clarify');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 提交澄清
  const submitClarification = async (answers) => {
    try {
      setLoading(true);
      await APIClient.submitClarificationAnswers(session.session_id, answers);
      const updated = await APIClient.getSession(session.session_id);
      setSession(updated);
      setCurrentPhase('spec');
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return {
    session,
    loading,
    error,
    currentPhase,
    createSession,
    submitClarification,
  };
}
```

---

## 测试

### 后端单元测试

```bash
cd backend
pytest tests/test_orchestration_v2.py -v
```

### 前端测试

```bash
cd frontend
npm test
```

### 集成测试

```bash
# 启动后端
python backend/app.py

# 在另一个终端启动前端
cd frontend
npm start

# 手动测试完整流程
```

---

## 部署

### Docker 部署

```bash
docker-compose up -d
```

### 健康检查

```bash
curl http://localhost:5000/api/v2/health
```

**响应**：
```json
{
  "status": "healthy",
  "service": "orchestration",
  "version": "2.0"
}
```

---

## 性能优化

### 1. 缓存澄清表单

```python
# 在 clarify_layer_v2.py 中
@cache.cached(timeout=3600, key_prefix='clarification_schema')
def get_clarification_schema(domain):
    # ...
```

### 2. 异步执行

```python
# 在 service_v2.py 中
@celery.task
def execute_task(session_id):
    # ...
```

### 3. 数据库索引

```sql
CREATE INDEX idx_session_id ON sessions(session_id);
CREATE INDEX idx_domain ON sessions(domain);
CREATE INDEX idx_created_at ON sessions(created_at);
```

---

## 故障排查

### 问题 1：澄清表单不显示

**原因**：完整度检测失败

**解决**：
```python
# 在 clarify_layer_v2.py 中调整阈值
should_skip = self.gap_detector.should_skip_clarification(completeness)
# 改为
should_skip = completeness >= 0.9  # 提高阈值
```

### 问题 2：预检总是失败

**原因**：验证规则过严

**解决**：
```python
# 在 preflight_v2.py 中调整规则
if error_count > 0:
    return RiskLevel.HIGH
# 改为
if error_count > 2:
    return RiskLevel.HIGH
```

### 问题 3：执行超时

**原因**：LLM 响应慢

**解决**：
```python
# 在 service_v2.py 中增加超时
timeout = 30  # 秒
output = self.llm_client.generate(prompt, timeout=timeout)
```

---

## 下一步

1. **集成更强模型** - 支持 Claude、Gemini 等
2. **多轮对话修复** - 允许用户与系统对话修复问题
3. **工作流模板** - 预定义常见任务模板
4. **协作功能** - 支持团队协作
5. **分析仪表板** - 任务执行统计和分析

---

## 支持

如有问题，请：
1. 查看 `ARCHITECTURE_V2.md`
2. 检查日志：`logs/orchestration.log`
3. 运行测试：`pytest tests/`
4. 提交 Issue
