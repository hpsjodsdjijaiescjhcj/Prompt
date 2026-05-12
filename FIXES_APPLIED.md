# 关键问题修复执行记录

## 修复 1: 会话 ID 一致性 (service_v2.py)
**问题**: service_v2 创建 TaskSession(session_id=A)，但 store.create() 生成新 UUID(session_id=B)
**修复**: 让 store.create() 接收 session_id 参数，保证一致性

## 修复 2: App.js 初始化流程优化
**问题**: App.js 已完整初始化，但 WorkflowContainer 还会再次初始化，导致冲突
**修复**: 
- App.js 负责完整初始化（createSession → processClarification → getSession）
- WorkflowContainer 只负责渲染和用户交互
- 移除 WorkflowContainer 中的冗余初始化逻辑

## 修复 3: 标签选择传递
**问题**: 前端 selectedLabels 未传给后端
**修复**:
- api_v2.js createSession() 接收 selectedLabels 参数
- routes_v2.py create_session() 接收 selected_domains/selected_characteristics
- App.js handleSubmit() 传递 selectedLabels

## 修复 4: 澄清答案展示结构
**问题**: ClarificationAnswersDisplay 直接 Object.entries(answers)，但实际结构是 {answers, inferred_answers, timestamp}
**修复**: 修改组件正确处理嵌套结构

## 修复 5: Preflight 状态一致性
**问题**: 后端设置 PREFLIGHT_CHECK，前端判断 preflight_failed
**修复**: 统一状态名称为 preflight_failed

---

## 执行状态
- [ ] 修复 1: store.py 接收 session_id
- [ ] 修复 2: WorkflowContainer.jsx 移除冗余初始化
- [ ] 修复 3: api_v2.js + routes_v2.py + App.js 传递标签
- [ ] 修复 4: WorkflowStagePanel.jsx 修复澄清答案展示
- [ ] 修复 5: preflight_v2.py 状态名称统一
