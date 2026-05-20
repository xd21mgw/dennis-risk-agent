# Expert Reasoning First Text Regression Run v1

## 1. Run Status

```yaml
run_id: expert_reasoning_first_text_regression_run_v1
capability: expert_reasoning_first
capability_type: brain_capability
platform_called: false
real_data_read: false
write_action: false
plan_mode_changed: false
real_execution_framework_changed: false
git_commit_created: false
```

## 2. Regression Summary

```yaml
total_cases: 11
pass: 11
fail: 0
result: passed
routing_tightening_added: true
```

## 3. Case Results

### Case 1: 登录设备只有本人，但账号发布色情视频，访问过“快手助力成功”

```yaml
recognized_scene: appeal_text_with_core_contradiction
selected_capability: expert_reasoning_first
platform_called: false
result: pass
```

Expected behavior:

- 一句话判断指向助力 / 活动页钓鱼导致登录态、Cookie、Token 或 OAuth 授权凭证被滥用的候选方向。
- 不写“已确认 token 劫持”。
- 不写“确定协议破解”。
- 解释“登录设备只有本人”不能排除 token 复用或授权滥用。
- 输出五类候选路径：token/cookie 复用、OAuth 授权滥用、新设备盗号但设备列表缺失、客户端木马、本人误操作 / 家庭共用 / 申诉信息不完整。
- 输出强区分证据卡。

### Case 2: 新设备登录后发布违规内容

```yaml
recognized_scene: account_takeover_with_new_login_signal
selected_capability: expert_reasoning_first
platform_called: false
result: pass
```

Expected behavior:

- 候选路径优先新设备盗号登录。
- token 复用只能作为候选，不应默认排第一。
- 区分登录日志证据和发布接口来源证据。

### Case 3: 发布来源是本人常用设备、常用 IP、正常客户端

```yaml
recognized_scene: appeal_claim_conflicts_with_common_environment_publish
selected_capability: expert_reasoning_first
platform_called: false
result: pass
```

Expected behavior:

- 提示本人误操作、家庭共用设备或申诉信息不完整可能性上升。
- ATO / token 复用置信度下降。
- 仍要求发布审计和时间线确认。

### Case 4: 用户称没操作，但存在 OAuth 新授权和异常 scope

```yaml
recognized_scene: possible_oauth_abuse
selected_capability: expert_reasoning_first
platform_called: false
result: pass
```

Expected behavior:

- 优先怀疑 OAuth / 第三方授权滥用。
- 区分 OAuth 授权滥用、普通 token 泄露、新设备盗号。
- 不把 OAuth 授权存在直接定性为盗号。

### Case 5: 只有申诉文本，无关键时间、作品、设备、链接信息

```yaml
recognized_scene: insufficient_case_text
selected_capability: expert_reasoning_first
platform_called: false
result: pass
```

Expected behavior:

- `current_confidence=low`。
- 输出补充信息清单。
- 只给候选路径，不给事实结论。
- 不进入平台查询。

### Case 6: 明确 case + userId + 时间 + “研判下”

```yaml
recognized_scene: explicit_entity_time_fact_verification
selected_capability: plan_mode_or_read_only_execution_mode
expert_reasoning_first_used: false
result: pass
```

Expected behavior:

- 不进入完整 `expert_reasoning_first`。
- Plan 开头可以生成一句简短专家假设。
- 主体必须是只读查询计划。

### Case 7: 明确 case + 明确先不查数

```yaml
recognized_scene: explicit_request_for_expert_prior_without_query
selected_capability: expert_reasoning_first
platform_called: false
result: pass
```

Expected behavior:

- 即使输入包含 userId 和时间，只要用户明确说“先不查数 / 先从专家视角判断”，进入 `expert_reasoning_first`。
- 输出完整专家认知先判模板。

### Case 8: 只有申诉文本，无实体和时间窗口

```yaml
recognized_scene: vague_appeal_text_without_queryable_conditions
selected_capability: expert_reasoning_first
platform_called: false
result: pass
```

Expected behavior:

- 进入专家先判。
- 输出候选路径、强区分证据和补充信息清单。

### Case 9: 已有 observation / 日志返回

```yaml
recognized_scene: evidence_synthesis_required
selected_capability: evidence_synthesis_or_conclusion_generation
expert_reasoning_first_used: false
result: pass
```

Expected behavior:

- 不进入 `expert_reasoning_first`。
- 围绕已有 observation 输出 supporting_evidence / counter_evidence / missing_evidence / conclusion_boundary。

### Case 10: 明确要求查具体日志

```yaml
recognized_scene: explicit_log_query_request
selected_capability: plan_mode_or_read_only_execution_mode
expert_reasoning_first_used: false
result: pass
```

Expected behavior:

- 进入 Plan 或 read-only execution。
- 不展开完整专家认知模板。

### Case 11: 概念解释

```yaml
recognized_scene: concept_explanation
selected_capability: normal_risk_concept_answer
expert_reasoning_first_used: false
result: pass
```

Expected behavior:

- 解释 token 复用与协议破解的本质差异。
- 不进入 `expert_reasoning_first`。

## 4. Validated Guardrails

- `expert_reasoning_first` 不调用任何平台手脚。
- 不读取真实用户数据。
- 不输出“已确认 / 确定就是”。
- 不是所有 case 默认入口。
- 不是所有“研判 / 判断”默认入口。
- 明确 case + 明确实体 / 时间 / 查询对象 / 事实验证诉求，默认进入 Plan 或 read-only execution。
- Plan 可给一句简短专家假设，但不展开完整专家认知模板。
- 输出区分已知事实、高概率推断、待验证假设、反证可能。
- 强区分证据卡包含区分路径的原因。
- “设备列表只有本人”不能排除 token 复用或 OAuth 授权滥用。
- “API 直调”不能直接写成协议破解。
- 查询路径只作为建议，不进入执行。

## 5. Follow-Up

- 如用户需要事实闭环，下一步进入 Plan 模式生成只读查询计划。
- 若后续要接真实 observation，必须从 expert_reasoning_first 转到 evidence digest，而不是继续用先验替代事实。
