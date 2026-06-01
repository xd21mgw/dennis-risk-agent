# Full Runtime Inference Contract v1

`full_runtime` 是本地完整 dennis-risk-agent 运行态测试包，用于模拟线上真实用户体感和验证输出契约。Boundary marker: `full_runtime_test_package_not_development_target`。它不是本轮规则开发对象；开发应落在 Dennis 母体的 runtime 规则、编排、模板、validation cases 和 smoke tests 中，不直接修改 `outputs/full_runtime`、`outputs/release` 或 `outputs/dist`。

## 1. entity_type_inference

当用户给出纯数字 ID，且上下文是 case / ATO / 账号安全 / 策略命中 / 用户风险研判时：

- 默认推断为 `entity_type=user_id_candidate`。
- internal/debug routing metadata 的 boundary flags 应包含 `entity_type_inferred`；普通用户正文只用自然语言说明实体类型推断和 caveat。
- 输出中保留 `entity_inference_confidence` 与 caveat。
- caveat：纯数字 ID 也可能是 sourceId、eventId、case id 或内部 request id；若后续 source plan 需要更精确字段，应在 source_quality / missing_evidence 中标注。

只有在用户明确提到 `sourceId` / `source_id` / `source`，或上下文强匹配策略命中请求 source 字段时，才推断 `source_id_candidate`。

只有在用户明确提到 `eventId` / `event_id` / `事件ID`，或上下文强匹配单事件归因时，才推断 `event_id_candidate`。

推断不是强事实，不得在 evidence card 中包装为已验证实体类型。

## 2. time_window_inference

用户未给时间窗时：

- 按 source playbook default window 做 bounded_time_range inference。
- 如果 playbook 未给默认窗口，单 case / 策略命中默认近 24h 到近 7d 的有界窗口。
- internal/debug routing metadata 的 boundary flags 应包含 `time_window_inferred`；普通用户正文只说明默认窗口不代表全量历史覆盖。
- 输出中必须写明默认窗口不代表全量历史覆盖。

默认窗口查询结果不能被解释为全量历史结论。

在线登录日志约 7 天可靠窗口；超窗或未覆盖时，标 `login_log_window_incomplete` / `source_time_range_gap` / `offline_hive_required`，不得把 no_data 当无风险反证。

## 3. explicit_source_execution

用户明确问策略命中、被哪些策略拦、有没有生产策略证据、RCP / 天师命中、eventId 为什么被阻止时：

- 策略 source 是 explicit target source。
- `strategy_hit_read` / `tianshi_strategy_hit` 不得因其他 source 已完成而静默跳过。
- 需要请求级明细时，`rcp_event_list` / `tianshi_eventlist_read` 是 explicit supplement source。
- 缺必要字段时输出字段缺口和 source_quality，不直接 blocked 全局回答。

策略命中只能作为辅助风险信号，不是最终 ATO / 作弊定性。

## 4. user_facing_answer_style

`full_runtime` 输出顺序应贴近用户真实体感：

1. 先给一句话判断或当前状态。
2. 再给 evidence card，区分 strong / medium / weak / counter / missing evidence。
3. 再给用户可读的 source-quality 摘要和证据缺口。
4. 完整 `routing_metadata` 只在 debug / run log / validation fixture / 用户明确要求内部过程字段时输出。

不要一上来只输出 routing dump、source plan 或 contract checklist。

若当前只完成部分 source，先输出 partial evidence card，而不是空研判或裸 timeout。

## 5. source_failure_policy

source 失败必须进入 `source_quality`：

- `no_data`
- `blocked`
- `auth_failed`
- `timeout`
- `parse_error`
- `tool_gap`
- `missing_required_fields`

`blocked` / `auth_failed` / `timeout` / `tool_gap` 不等于无风险。

source failure 后禁止：

- debug 认证。
- debug `SmartSSOSession` / `sso_session_runner.py` / `sso_session.py`。
- 手拼 Cookie / Header。
- 读取 `.ks_sso`。
- 访问未登记 source。
- 猜 URL 或 probe arbitrary endpoint。

## 6. no_data_not_risk_exclusion

`no_data` 只说明当前 source、当前字段、当前窗口下无可见记录或无返回。

它不能直接推出：

- 无风险。
- 无盗号。
- 无策略命中。
- 无设备异常。
- 无历史异常。

只有存在覆盖充分、窗口匹配、source completed、且能形成业务反证的记录，才可作为 counter evidence。

## 7. DataAgent / Hive Boundary

DataAgent / Hive 仍需逐次授权。

- full_runtime 可以输出 query plan、推荐表、字段、窗口、join key 和 no-data 解释。
- 未经用户本次明确授权，不执行 DataAgent / Hive。
- 已提交或 pending 的 DataAgent / Hive job 不是 evidence result，只能标 `hive_query_pending` / `missing_hive_result`。

## 8. Case Rule: 544963630

用户问：

```text
544963630 这个 case 有没有策略命中能辅助判断？
```

full_runtime 不应直接 blocked。

默认行为：

- `entity_type=user_id_candidate`
- `entity_type_inferred=true`
- `time_window_inferred=true`
- `strategy_hit` 是 explicit target source
- 尝试 `tianshi_strategy_hit` / `rcp_event_list` 只读 source
- 若 source 失败，进入 `source_quality`
- 结论不能说“没有命中”，只能说本轮 source 状态如何

示例边界：

- 如果 `tianshi_strategy_hit` completed no_data：只能说“当前默认窗口内未看到可见策略命中，不排除窗口外或 source 覆盖外命中”。
- 如果 `tianshi_strategy_hit` blocked / timeout / tool_gap：只能说“策略命中 source 未完成，无法确认是否命中”，并给 next_action。
