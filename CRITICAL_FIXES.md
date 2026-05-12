# 关键问题修复清单 (P0 + P1)

## P0 - 流程卡住问题

### 1. WorkflowContainer 初始化逻辑冲突
**问题**：App.js 先调用 createSession + getSession，传入 initialData.session_id。
WorkflowContainer 的初始化 effect 条件是 `if (!userText || sessionId) return;`，导致不会再调用 processClarification。

**修复**：
- 移除 WorkflowContainer 中的冗余初始化逻辑
- 让 App.js 负责完整的初始化流程（createSession → processClarification → getSession）
- WorkflowContainer 只负责渲染和用户交互

### 2. 会话 ID 不一致
**问题**：service_v2.py 创建 TaskSession（session_id=A），但 store.create() 又生成新 UUID（session_id=B）。

**修复**：
- service_v2.py 的 create_session() 应该先创建 session，然后用同一个 session_id 调用 store.create()
- 或者让 store 接收 session_id 参数而不是自己生成

### 3. 标签选择未传给后端
**问题**：前端 App.js 维护 selectedLabels，但 APIClient.createSession() 只传 text。

**修复**：
- api_v2.js createSession() 接收 selectedLabels 参数
- routes_v2.py create_session() 接收 selected_domains/selected_characteristics
- service_v2.py create_session() 已有参数，只需前端传过来

### 4. 澄清答案展示结构错误
**问题**：WorkflowStagePanel.jsx 的 ClarificationAnswersDisplay 直接 Object.entries(answers)，但实际结构是 {answers, inferred_answers, timestamp}。

**修复**：
- 修改 ClarificationAnswersDisplay 正确处理嵌套结构
- 或者在后端返回时扁平化

### 5. Preflight 失败状态机不一致
**问题**：后端设置 PREFLIGHT_CHECK，前端判断 preflight_failed。

**修复**：
- 统一状态名称：失败时设置 preflight_failed
- 或更新前端的 STATE_TO_PHASE 映射

---

## 修复顺序（按依赖关系）

1. **修复会话 ID 一致性** (service_v2.py + store.py)
2. **修复 App.js 初始化流程** (App.js + api_v2.js)
3. **移除 WorkflowContainer 冗余初始化** (WorkflowContainer.jsx)
4. **添加标签传递** (api_v2.js + routes_v2.py)
5. **修复澄清答案展示** (WorkflowStagePanel.jsx)

---

## 验证方式

- [ ] 前端输入 → 后端 createSession 返回正确 session_id
- [ ] processClarification 返回 should_skip 或 schema
- [ ] 如果 should_skip=true，自动跳到 spec 阶段
- [ ] 如果 should_skip=false，显示澄清表单
- [ ] 澄清答案正确展示
- [ ] 标签选择被后端接收并影响分类
