# AI 任务编排系统 - 完整实施计划

## 当前状态诊断

### ✅ 已完成
- 后端架构 v2 框架完整（domain_model, service_v2, 各层模块）
- 前端基础组件（Sidebar, ContextPanel, WorkflowContainer）
- API 路由框架（routes_v2.py）
- 国际化基础（i18n）

### ⚠️ 需要完成
1. **后端核心逻辑补齐**
   - [ ] LLM 客户端真实集成（generate 方法）
   - [ ] 降级策略（无 LLM 时使用模板）
   - [ ] 超时和重试机制
   - [ ] 数据库持久化（MySQL）
   - [ ] Redis 缓存

2. **前端 UI/UX 重构**
   - [ ] 统一设计风格（现代化配色、一致组件）
   - [ ] 每阶段完整快照显示
   - [ ] Spec 原始输入 vs 专业化改写对比
   - [ ] 执行阶段模型/执行器可见性
   - [ ] 预检失败时的修复建议展示

3. **系统可靠性**
   - [ ] 结构化错误处理
   - [ ] request_id 追踪
   - [ ] 健康探针
   - [ ] Prometheus 指标

---

## 优先级排序

### Phase 1: 后端核心（P0 - 关键）
**目标**：让完整工作流能跑通

#### 1.1 LLM 客户端集成
- **文件**：`backend/llm_client.py`
- **任务**：
  - 实现 `generate()` 方法（支持 OpenAI/Gemini/本地）
  - 添加超时控制（30s）
  - 添加重试机制（3 次）
  - 降级策略（无 LLM 时返回模板）
- **验证**：能调用 LLM 并返回结果

#### 1.2 完善 task_taxonomy_v2.py
- **任务**：
  - 改进语义分类（不只是关键词）
  - 支持用户约束标签
  - 返回置信度评分
- **验证**：分类准确率 >85%

#### 1.3 完善 clarify_layer_v2.py
- **任务**：
  - 完整快照持久化
  - 推断缺失答案
  - 支持部分填写
- **验证**：澄清表单正确生成

#### 1.4 完善 spec_alignment_v2.py
- **任务**：
  - 语义重写优化
  - 完整字段映射
  - 用户可编辑
- **验证**：Spec 包含所有必要字段

#### 1.5 完善 preflight_v2.py
- **任务**：
  - 显式逻辑校验
  - 清晰的失败原因
  - 可操作的修复建议
- **验证**：预检能正确拦截问题

#### 1.6 完善 validation_v2.py
- **任务**：
  - 多层验证（格式/约束/验收）
  - 可定位问题
  - 单轮自动修复
- **验证**：验证能正确评估输出

#### 1.7 数据持久化
- **文件**：`backend/infrastructure/db.py`
- **任务**：
  - MySQL 会话存储
  - Redis 缓存
  - 会话恢复
- **验证**：数据能正确保存和恢复

#### 1.8 API 路由完善
- **文件**：`backend/api/routes_v2.py`
- **任务**：
  - 所有端点实现
  - 错误处理
  - request_id 追踪
- **验证**：所有端点能正确响应

### Phase 2: 前端 UI/UX（P1 - 高）
**目标**：用户体验达到企业级

#### 2.1 统一设计风格
- **文件**：`frontend/src/App.css`, `frontend/src/components/workflow/WorkflowContainer.css`
- **任务**：
  - 现代化配色（深色/浅色主题）
  - 一致的组件库
  - 响应式布局
- **验证**：UI 美观一致

#### 2.2 完整快照显示
- **文件**：`frontend/src/components/workflow/WorkflowContainer.jsx`
- **任务**：
  - 每阶段显示完整用户输入
  - 显示当前规格
  - 显示预检状态
- **验证**：用户始终知道系统在哪一步

#### 2.3 Spec 对比展示
- **文件**：`frontend/src/components/workflow/SpecEditor.js`（新建）
- **任务**：
  - 显示原始输入
  - 显示专业化改写
  - 允许用户编辑
- **验证**：用户能看到改写过程

#### 2.4 执行阶段可见性
- **文件**：`frontend/src/components/workflow/ExecutionPhase.js`（新建）
- **任务**：
  - 显示选中的模型
  - 显示执行器类型
  - 显示执行进度
- **验证**：用户能看到执行细节

#### 2.5 预检失败处理
- **文件**：`frontend/src/components/workflow/PreflightPhase.js`（新建）
- **任务**：
  - 清晰显示失败原因
  - 显示修复建议
  - 允许用户编辑规格后重试
- **验证**：用户能理解问题并修复

### Phase 3: 系统可靠性（P2 - 中）
**目标**：生产级别的可靠性

#### 3.1 错误处理
- **文件**：`backend/infrastructure/errors.py`
- **任务**：
  - 结构化错误
  - request_id 追踪
  - 详细日志
- **验证**：错误能正确追踪

#### 3.2 健康探针
- **文件**：`backend/app.py`
- **任务**：
  - liveness 探针
  - readiness 探针
- **验证**：健康检查能正确响应

#### 3.3 Prometheus 指标
- **文件**：`backend/infrastructure/logging_config.py`
- **任务**：
  - 请求计数
  - 延迟分布
  - 错误率
- **验证**：指标能正确收集

### Phase 4: 端到端测试（P3 - 低）
**目标**：确保系统稳定

#### 4.1 集成测试
- **文件**：`backend/tests/test_integration_stack.py`
- **任务**：
  - 完整工作流测试
  - 边界情况测试
  - 性能测试
- **验证**：所有测试通过

#### 4.2 文档完善
- **任务**：
  - API 文档
  - 使用指南
  - 故障排查
- **验证**：文档完整清晰

---

## 实施步骤

### Week 1: 后端核心
1. **Day 1-2**: LLM 集成 + 降级策略
2. **Day 3-4**: 澄清/规格/预检/验证层完善
3. **Day 5**: 数据持久化 + API 路由

### Week 2: 前端重构
1. **Day 1-2**: 设计风格统一
2. **Day 3-4**: 快照显示 + Spec 对比
3. **Day 5**: 执行/预检阶段 UI

### Week 3: 系统可靠性
1. **Day 1-2**: 错误处理 + 日志
2. **Day 3-4**: 健康探针 + 指标
3. **Day 5**: 集成测试

### Week 4: 文档和优化
1. **Day 1-2**: 文档完善
2. **Day 3-4**: 性能优化
3. **Day 5**: 最终测试

---

## 关键文件清单

### 后端
```
backend/
├── llm_client.py                    # LLM 集成
├── orchestrator/
│   ├── domain_model.py              # 数据模型
│   ├── task_taxonomy_v2.py          # 分类
│   ├── clarify_layer_v2.py          # 澄清
│   ├── spec_alignment_v2.py         # 规格
│   ├── preflight_v2.py              # 预检
│   ├── validation_v2.py             # 验证
│   ├── service_v2.py                # 服务
│   └── executor.py                  # 执行器
├── api/
│   └── routes_v2.py                 # API 路由
├── infrastructure/
│   ├── db.py                        # 数据库
│   ├── redis_client.py              # Redis
│   ├── errors.py                    # 错误处理
│   └── logging_config.py            # 日志
└── tests/
    └── test_integration_stack.py    # 集成测试
```

### 前端
```
frontend/src/
├── api_v2.js                        # API 客户端
├── App.css                          # 全局样式
├── components/
│   ├── layout/
│   │   ├── Sidebar.js               # 历史侧栏
│   │   └── ContextPanel.js          # 上下文面板
│   └── workflow/
│       ├── WorkflowContainer.jsx    # 主容器
│       ├── WorkflowContainer.css    # 样式
│       ├── ClarifyPhase.js          # 澄清阶段
│       ├── SpecEditor.js            # 规格编辑
│       ├── PreflightPhase.js        # 预检阶段
│       ├── ExecutionPhase.js        # 执行阶段
│       └── ValidationPhase.js       # 验证阶段
└── i18n/
    ├── useI18n.js                   # 国际化 Hook
    └── translations.js              # 翻译
```

---

## 成功指标

1. **功能完整性**: 所有 6 个阶段都能真实工作
2. **用户体验**: 用户始终知道系统在哪一步
3. **可靠性**: 99% 的请求能正确处理
4. **性能**: 澄清 <100ms, 规格 <200ms, 预检 <150ms
5. **可维护性**: 代码覆盖率 >80%, 文档完整

---

## 技术决策

### 后端
- **LLM**: OpenAI API (支持降级到本地)
- **存储**: MySQL + Redis
- **框架**: Flask
- **监控**: Prometheus + 结构化日志

### 前端
- **框架**: React 18+
- **样式**: CSS3 + 现代设计
- **状态**: React Hooks
- **API**: Fetch API

---

## 风险和缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| LLM 不可用 | 无法执行 | 降级到模板 |
| 数据库连接失败 | 无法持久化 | 内存缓存 + 重试 |
| 前端构建失败 | 无法部署 | 增量构建 + 缓存 |
| 性能不达标 | 用户体验差 | 缓存 + 异步 + 优化 |

---

## 下一步

1. **立即开始**: Phase 1 Day 1-2 (LLM 集成)
2. **并行进行**: 前端样式统一
3. **持续验证**: 每天构建 + 集成测试
4. **文档同步**: 每个功能完成后更新文档

---

## 联系和支持

- 架构文档: `ARCHITECTURE_V2.md`
- 集成指南: `INTEGRATION_GUIDE.md`
- 改进路线图: `IMPROVEMENT_ROADMAP.md`
- 日志位置: `logs/orchestration.log`
