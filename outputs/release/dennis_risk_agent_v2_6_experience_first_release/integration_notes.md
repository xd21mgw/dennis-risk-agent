# Integration Notes

## 1. 推荐加载顺序

云端内部 Agent 集成时，建议优先加载：

1. `computer_use_poc/user_experience_golden_cases.md`
2. `computer_use_poc/answer_experience_templates.md`
3. `computer_use_poc/scene_to_capability_routing.md`
4. `computer_use_poc/smoke_tests.md`
5. `computer_use_poc/run_logs/user_experience_golden_cases_dry_run_001.md`
6. `computer_use_poc/README.md`

使用顺序：

- 先用 golden cases 判断用户问题属于哪个体验 Case。
- 再用 scene_to_capability_routing 选择最小必要能力。
- 最后用 answer templates 组织可读回答。

## 2. 缺失输入和阻断处理

### missing_device_id

当用户问设备风险，但没有明确 deviceId / did / deviceceid：

- 如果输入是 userId，先走 user_to_device entity resolution。
- 如果无法解析，返回 `missing_device_id`。
- 不允许直接进入 Device SDK。

### missing_required_input

当用户问题缺少必要对象或时间窗口：

- 先说明缺少什么。
- 给出最小补充字段。
- 不要编造查询对象。

### permission_blocked

当平台权限不足：

- 记录为 blocker。
- 进入 missing_evidence。
- 不解释为无风险或无数据。

### api_failed

当 API 失败：

- 记录 failure reason。
- 如有 fallback 才进入 fallback。
- 不解释为用户无数据。

## 3. 敏感信息边界

不允许打印：

- cookie
- token
- session
- storageState
- KIM code
- password
- authorization
- refresh token / access token
- 完整请求 header
- 完整认证票据

## 4. 证据边界

不允许因为以下单一证据直接定性作弊或盗号：

- 单一设备关联。
- 单一策略命中。
- 单一登录失败。
- 单一前端活跃或无活跃。
- 单一档案状态。

必须保留：

- supporting_evidence
- counter_evidence
- missing_evidence
- boundary_notes
- next_suggested_checks

## 5. 回答体验要求

每次回答优先满足：

- 先给结论或直接解释。
- 再给关键证据。
- 明确不确定性和边界。
- 给出下一步最小动作。
- 不输出平台导航式回答。
