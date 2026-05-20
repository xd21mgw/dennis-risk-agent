# Plan Mode / Execution Mode Text Regression Run v1

## 1. 回归目标

本轮对 Dennis Risk Agent 当前 Plan 模式 / 执行模式路由做文档级回归自测。

目标是确认：

- 真实研判问题不会被误拦到 Plan。
- 显式计划请求、边界不清、批量扩展、高风险动作会进入 Plan。
- Plan 阶段不会调用真实接口、不会生成 observation、不会输出最终风险结论。
- 执行模式仍保留证据强弱分层。
- ATO / 登录日志类场景保持在线日志窗口限制口径。

本轮不调用真实接口，不生成真实 observation，不修改平台手脚实现，不提交 git。

## 2. 当前核心口径

```text
真实研判问题默认进入执行模式；Plan 不是默认前置流程。
Plan 只在用户显式要求“先说怎么查 / 先给计划 / 先不要执行”，
或边界不清、批量扩展、高风险动作不适合直接执行时触发。
```

Plan 模式定位：

- 执行前解释层。
- 不是真实查询结果。
- 不调用真实接口。
- 不生成 observation。
- 不输出最终风险结论。
- 不承诺处置动作。
- 不假设已有正式安全执行框架。

执行模式定位：

- 用于真实查询和研判。
- 识别实体、路由能力、调用平台手脚、收集 observation。
- 输出研判结论和证据强弱分层。

## 3. 覆盖 case 范围

### A. 应默认进入执行模式的 case

覆盖以下输入：

1. 帮我看下 user_id=123 是不是风险用户
2. 这个账号是不是盗号
3. 这批账号是不是一伙的
4. 这个用户是不是误伤
5. 这个 request_id=xxx 为什么被风控拦了
6. 这个 device_id=abc 有没有问题
7. 查一下 user_id=123 的基础画像
8. 看下 device_id=abc 的设备风险标签

回归结论：

- 预期模式均为 `execution_mode`。
- 文档口径均支持“真实研判默认执行”。
- 执行前可以轻量说明查询思路，但不应只输出 Plan。
- 最终结果要求保留强 / 中 / 弱证据与反证分层。

### B. 应触发 Plan 模式的 case

覆盖以下输入：

1. 先说下你准备怎么查 user_id=123
2. 查之前先给我一个研判计划
3. 先不要执行，先说下排查路径
4. 这个问题要怎么查比较合理
5. 帮我设计一个排查路径
6. 帮我扩展这批账号所有关联设备和关联用户
7. 帮我计划下后续怎么查和处置这批风险账号

回归结论：

- 预期模式均为 `plan_mode`。
- 文档口径均支持显式计划请求或高风险边界触发 Plan。
- Plan 标准结构已覆盖：
  - 我理解的问题
  - 本次研判目标
  - 查询路径与强区分证据卡
  - 证据强弱说明
  - 查询边界
  - 预期输出
  - 你可以选择
- “查询路径与强区分证据卡”使用一张合并表，不拆成重复模块。
- 批量扩展场景要求说明 `too_many_candidates` / 不默认无限扩展。
- 涉及处置时只说明需要后续安全约束或人工确认，不承诺处置执行。

### C. 应澄清或给通用 Plan 的 case

覆盖以下输入：

1. 帮我看看是不是风险
2. 这个是不是有问题
3. 看下这个账号
4. 帮我查一下原因

回归结论：

- 预期模式为 `clarification_or_plan_mode`。
- 缺少 `user_id / device_id / request_id` 等关键实体时，不能伪造实体。
- 可以追问缺失实体，或给通用研判计划。
- 不应假装已查询，不生成真实 observation。

## 4. 通过结论

本轮文档级回归通过。

```yaml
regression_result: passed
real_judgement_default_execution: passed
explicit_plan_request_triggers_plan: passed
unclear_or_large_scope_triggers_plan: passed
missing_entity_does_not_fake_execution: passed
plan_standard_structure_present: passed
execution_mode_evidence_strength_layering_required: passed
```

## 5. 未发现的问题清单

未发现以下冲突或风险：

- 未发现“所有复杂研判默认先 Plan”。
- 未发现“用户风险研判默认 Plan”。
- 未发现“盗号 / 误伤 / 群控问题默认 Plan”。
- 未发现“Plan 阶段可以调用真实接口”。
- 未发现“Plan 阶段会生成 observation”。
- 未发现“Plan 可以输出最终风险结论”。
- 未发现“安全执行框架已经存在 / 已接入”。
- 未发现“Data Agent 是默认万能数据底座”。
- 未发现“在线登录日志无记录 = 无异常登录”。
- 未发现“关联账号 / 关联设备 = 作弊结论”。

## 6. 关键风险确认

```yaml
key_risk_checks:
  real_judgement_misrouted_to_plan: not_found
  plan_over_execution_risk: not_found
  safety_execution_framework_assumed_existing: not_found
  ato_login_log_window_conflict: not_found
  data_agent_over_generalized_as_universal_data_layer: not_found
```

补充确认：

- ATO / 登录日志类 Plan 和执行结果均要求提示在线日志窗口限制。
- 超出在线窗口后，无登录记录 / 无异常登录记录不能作为“没有盗号 / 没有异常登录”的强反证。
- 需要标注 `login_log_window_incomplete` / `offline_hive_required` 等缺口。
- 关联关系只作为候选证据，不直接等于作弊结论。

## 7. 下一步建议

1. 云端集成时重点验证主 Agent 路由，尤其是“真实研判默认执行，不默认 Plan”。
2. 如果更新 release 包，需要同步：
   - `computer_use_poc/plan_mode_capability_v1.md`
   - `computer_use_poc/capability_registry.md`
   - `computer_use_poc/scene_to_capability_routing.md`
   - `computer_use_poc/answer_experience_templates.md`
   - `computer_use_poc/smoke_tests.md`
   - 本 run log
3. 后续如接正式安全执行框架，应重新回归 Plan 中涉及处置、敏感字段、批量扩展的边界表达。
