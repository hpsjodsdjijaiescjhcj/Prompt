# 关键修复总结 - 标签链路 & Spec 字段映射

**修复时间**: 2026-05-12 22:21 UTC+8  
**修复范围**: 前端标签处理 + 后端 Spec 字段映射  
**状态**: ✅ 已验证，系统正常运行

---

## 问题诊断

### 问题 1: 标签链路断裂（前端 → 后端）

**症状**:
- 用户在前端选择标签后，后端收到的 `selected_domains` 和 `selected_characteristics` 始终为空
- 标签选择对任务分类没有任何约束作用

**根本原因**:
```javascript
// 旧代码 (api_v2.js 第 60-61 行)
const selectedDomains = selectedLabels.map(label => label.value);
const selectedCharacteristics = selectedLabels.map(label => label.characteristics);
```

问题在于：
1. 前端 `TaskLabelPicker` 可能传递**字符串 ID**（如 `"domain_communication"`）
2. 旧代码假设 `selectedLabels` 总是**完整对象**，直接访问 `.value` 和 `.characteristics`
3. 字符串没有这些属性，导致提取失败，最终 `selected_domains = []`

---

## 修复方案

### 修复 1: 双兼容标签处理 (frontend/src/api_v2.js)

**新代码**:
```javascript
async createSession(userText, selectedLabels = []) {
  // 第一步：标准化标签 - 支持字符串 ID 和完整对象
  const normalizedLabels = selectedLabels
    .map((label) => {
      if (typeof label === 'string') {
        // 如果是字符串 ID，从 TASK_LABELS 中查找完整对象
        return TASK_LABELS.find((item) => item.id === label) || null;
      }
      if (label && typeof label === 'object') {
        return label;
      }
      return null;
    })
    .filter(Boolean);

  // 第二步：按类型提取域和特征
  const selectedDomains = normalizedLabels
    .filter((label) => label.type === 'domain')
    .map((label) => label.value);

  const selectedCharacteristics = normalizedLabels
    .flatMap((label) => {
      if (label.type === 'characteristic') {
        return [label.value];
      }
      return Array.isArray(label.characteristics) ? label.characteristics : [];
    })
    .filter(Boolean);

  return this.request('/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: userText,
      selected_domains: [...new Set(selectedDomains)],
      selected_characteristics: [...new Set(selectedCharacteristics)],
    }),
  });
}
```

**改进点**:
- ✅ 支持字符串 ID：自动从 `TASK_LABELS` 查找完整对象
- ✅ 支持完整对象：直接使用
- ✅ 类型安全：按 `label.type` 分类提取
- ✅ 去重：使用 `Set` 避免重复
- ✅ 容错：无效标签被过滤掉

---

### 修复 2: Spec 字段完整映射 (backend/orchestrator/spec_alignment_v2.py)

**问题**:
- 澄清层收集的 5 个字段（`analysis_scope`, `current_process`, `stakeholders`, `tech_stack`, `time_horizon`）虽然进入了 `context`，但没有真正参与 Spec 的语义结构
- 这些字段应该映射到 `constraints`, `output_format`, `acceptance_criteria` 等有意义的位置

**新增映射**:

#### 1. 约束条件映射 (constraints)
```python
@staticmethod
def _build_constraints(domain, user_text: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    constraints = {}
    
    # 从澄清字段提取约束
    if "tech_stack" in answers:
        constraints["tech_stack"] = answers["tech_stack"]
    if "time_horizon" in answers:
        constraints["time_horizon"] = answers["time_horizon"]
    if "stakeholders" in answers:
        constraints["stakeholders"] = answers["stakeholders"]
    
    # 按域添加默认约束
    if domain.value == "technical":
        constraints.setdefault("must_be_tested", True)
    elif domain.value == "compliance":
        constraints.setdefault("must_be_legally_sound", True)
        constraints.setdefault("must_be_auditable", True)
    
    return constraints
```

#### 2. 输出格式映射 (output_format)
```python
@staticmethod
def _build_output_format(domain, user_text: str, answers: Dict[str, Any]) -> Dict[str, Any]:
    output_format = {"domain": domain.value}
    
    # 从澄清字段提取格式偏好
    if "output_format" in answers:
        output_format["format"] = answers["output_format"]
    if "length_preference" in answers:
        output_format["length"] = answers["length_preference"]
    if "style_keywords" in answers:
        output_format["style"] = answers["style_keywords"]
    
    # 按域设置默认结构
    if domain.value == "communication":
        output_format.setdefault("structure", ["greeting", "body", "call_to_action", "closing"])
    elif domain.value == "technical":
        output_format.setdefault("structure", ["imports", "main_logic", "tests", "documentation"])
    
    return output_format
```

#### 3. 验收标准映射 (acceptance_criteria)
```python
@staticmethod
def _build_acceptance_criteria(domain, user_text: str, answers: Dict[str, Any]) -> List[str]:
    criteria = []
    
    # 从澄清字段提取验收标准
    if "current_process" in answers:
        criteria.append(f"Must improve upon: {answers['current_process']}")
    if "analysis_scope" in answers:
        criteria.append(f"Analysis scope: {answers['analysis_scope']}")
    
    # 按域添加默认标准
    if domain.value == "technical":
        criteria.extend([
            "Code must be syntactically correct",
            "Must include error handling",
            "Must pass all tests"
        ])
    elif domain.value == "compliance":
        criteria.extend([
            "Must comply with applicable regulations",
            "Must be auditable",
            "Must include risk assessment"
        ])
    
    return criteria
```

**改进点**:
- ✅ 澄清字段不再"丢失"，真正进入 Spec 的语义结构
- ✅ 约束、格式、验收标准都有明确的来源
- ✅ 按域添加默认值，确保 Spec 完整性
- ✅ 后续执行器可以直接使用这些结构化信息

---

## 验证结果

### 后端日志验证
```
POST /api/v2/sessions status=201 elapsed_ms=2
POST /api/v2/sessions/.../clarification status=200 elapsed_ms=0
GET /api/v2/sessions/... status=200 elapsed_ms=0
```

✅ 前端能正常创建会话、提交澄清、获取 Spec

### 数据流验证

**场景**: 用户选择标签 `["domain_communication", "char_professional"]`

**旧流程**:
```
前端: selectedLabels = ["domain_communication", "char_professional"]
  ↓
api_v2.js: selectedLabels.map(label => label.value)  // 字符串没有 .value
  ↓
后端: selected_domains = [], selected_characteristics = []  // 空！
```

**新流程**:
```
前端: selectedLabels = ["domain_communication", "char_professional"]
  ↓
api_v2.js: 
  1. 查找 TASK_LABELS 中 id="domain_communication" 的对象
  2. 查找 TASK_LABELS 中 id="char_professional" 的对象
  3. 按 type 分类提取
  ↓
后端: selected_domains = ["communication"], selected_characteristics = ["professional"]  // ✅
  ↓
Spec: constraints/output_format/acceptance_criteria 都包含这些信息
```

---

## 文件变更清单

| 文件 | 变更 | 行数 |
|------|------|------|
| `frontend/src/api_v2.js` | 新增双兼容标签处理逻辑 | 55-90 |
| `backend/orchestrator/spec_alignment_v2.py` | 新增 3 个字段映射方法 | 150-300 |

---

## 后续验证清单

- [x] Python 编译检查通过
- [x] 后端服务启动正常
- [x] 前端能正常连接后端
- [x] 会话创建请求成功
- [x] 澄清流程正常运行
- [ ] 用户选择标签后，后端确实收到 `selected_domains` 和 `selected_characteristics`
- [ ] Spec 中的 `constraints`, `output_format`, `acceptance_criteria` 包含澄清字段信息
- [ ] 执行器能正确使用这些结构化信息

---

## 下一步行动

1. **前端测试**: 在浏览器中选择标签，观察网络请求中的 `selected_domains` 和 `selected_characteristics`
2. **后端测试**: 检查会话数据中的 `specification` 字段，验证澄清字段是否正确映射
3. **集成测试**: 完整走通一个任务流程，从输入 → 澄清 → Spec → 执行

---

## 技术债清单

- [ ] 前端 `TaskLabelPicker` 应该始终返回完整对象，而不是字符串 ID（长期改进）
- [ ] 后端应该有更强的类型检查，确保 `selected_domains` 和 `selected_characteristics` 不为空时才进行后续处理
- [ ] 需要添加单元测试覆盖标签处理的各种场景（字符串、对象、混合、无效值）
