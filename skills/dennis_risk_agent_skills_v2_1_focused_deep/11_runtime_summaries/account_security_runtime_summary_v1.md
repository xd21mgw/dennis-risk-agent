# Account Security Runtime Summary v1

## 1. 定位

本 summary 支撑半开放 runtime 下的账号安全 / ATO / 盗号判断。重点是避免把批量统计直接解释成攻击本质。

通用研判纪律：本 summary 必须遵守 `computer_use_poc/general_evidence_reasoning_contract_v1.md`。登录日志 no_data、策略命中、模型分、用户反馈、Hive pending 结果都不能单独作为最终定性；必须区分 raw_evidence / strategy_hit / model_score / inference / user_claim / counter_evidence / missing_evidence，并在新证据到达后重算结论。

## 2. ATO 攻击类型识别

### 2.1 撞库 ATO

主线特征：

- 密码尝试、登录失败、CAPTCHA 或验证挑战密集。
- 同 IP / 代理 / 设备对多账号做凭证测试。
- 成功登录后出现敏感动作、资料修改、私信、发布、支付等后置行为。

判断边界：

- `password fail + CAPTCHA + kick_out` 只能提示账号安全异常，不能单独定性撞库。
- 必须看到密码尝试是攻击主线，而不是改密 / 密码验证环节的后置现象。

### 2.2 一键登录 / 三方授权 / 鸿蒙一键登录 ATO

候选触发信号：

- 出现 `HARMONY_` 设备 ID 或鸿蒙设备前缀。
- token issued / token 下发成功。
- 多账号登录成功。
- 同一 IP 集中登录多个用户。
- token revoke / kick out。
- 后续小米 / Android 设备改密或密码验证失败。
- 用户原设备与新 HARMONY 设备明显不一致。

判断：

- 这类 case 应优先识别为“一键登录 / 三方授权接管 / 鸿蒙一键登录 ATO”候选。
- 不应直接归为撞库。
- 大量 password fail / CAPTCHA 可能来自改密环节，不一定是撞库尝试。

## 3. 批量 ATO 逐条时序抽样

批量 ATO case 中出现以下任一信号时，不能只看 totalCount / kick_out 次数 / fail 次数：

- kick_out 密集。
- password fail / CAPTCHA 密集。
- 多设备切换。
- 同 IP 集中。
- 三方登录 / 一键登录 / OAuth / HARMONY 相关字段。

必须抽取 3-5 个代表用户做 timeline：

- 正常登录设备。
- 异常登录设备。
- 登录方式。
- token issued。
- token revoke / kick out。
- password verify / change password。
- IP。
- device model / did prefix。
- event order。

输出必须包含“撞库 ATO vs 一键登录 ATO”的替代解释对比。

## 4. 禁止结论跳跃

禁止：

- 只凭 `kick_out + password fail + CAPTCHA` 直接输出“撞库 ATO”。
- 只看 totalCount 汇总，不抽样逐条时序。
- 把改密阶段的 password fail / CAPTCHA 当作撞库主线证据。

推荐表述：

```text
当前批量统计显示账号安全异常，但不能直接定性撞库。日志中出现 HARMONY_ 设备、同 IP token 下发、token revoke / kick out，以及后续小米 / Android 改密尝试，更应优先验证一键登录 / 三方授权接管 / 鸿蒙一键登录 ATO 链路。
```

## 5. 单案 evidence card 证据类型分离

单个 user_id / case 的 ATO 研判必须区分：

- `raw_evidence`: 平台日志、发布审计、登录日志、设备画像、策略命中等事实。
- `behavior_event`: 违规内容发布、改密、换绑、私信、关注、支付等动作发生事实。
- `user_claim`: 用户声称被盗、非本人操作、客服备注。
- `inference`: 基于多源证据的解释。
- `hypothesis`: 需要补证的候选路径。
- `missing_evidence`: 未查到、未查询、blocked、timeout、超窗的关键证据。

边界：

- 用户反馈账号被盗只能作为 `user_claim` / weak signal。
- 违规内容发布只能证明违规发生，不能证明被盗。
- 钓鱼页访问、OAuth 授权、前端行为、token 链路、发布审计如果未实际查到，必须写入 `missing_evidence`，不得写“已确认”。
- 发布设备与日常设备不一致通常是 medium evidence，需要登录、设备、行为或发布审计补证；不能单独强判盗号。
- 每条 strong / medium / weak / counter evidence 都必须带 `evidence_type` 和 `strength`。

单案 evidence card 必须包含：

- `conclusion`
- `confidence`
- `strong_evidence`
- `medium_evidence`
- `weak_evidence`
- `counter_evidence`
- `missing_evidence`
- `completed_sources`
- `blocked_or_timeout_sources`
- `source_quality`
- `next_action`

平台 blocked、timeout、browser loop 时，输出 partial evidence card，不裸 timeout。

## 5.1 ATO 单案 source checkpoint 与 deadline

明确 `user_id` 的 ATO 单案允许进入 `single_entity_execution_mode` 并查询只读平台，但必须按 source 编排，不能让后续高耗时 source 吞掉已完成证据。

每个 source 查询结束后必须立即记录 checkpoint：

- `source_name`
- `source_type`
- `source_status`: completed / no_data / blocked / auth_failed / timeout / parse_error / skipped
- `evidence_summary`
- `evidence_time_range`
- `source_quality`
- `raw_reference_safe_id`
- `collected_at`
- `failure_reason`
- `next_source_decision`

source 优先级：

- P0：统一登录日志、Weapon riskData / graphData、天师策略命中摘要。
- P1：档案中心画像、track-analysis stats-first。
- P2：RCP browser、档案中心 browser recoverable_preflight、track-analysis SPA 明细。

规则：

- completed source 不得因后续 source timeout / blocked / parse_error 丢失。
- no_data 也算 completed source，但必须标 `no_data_not_risk_exclusion`。
- P0 source completed 后，已具备输出 partial evidence card 的最低条件。
- 默认总预算 180s；任一 P0/P1 source completed 后，在 120s 或 150s checkpoint 应停止扩展 P2 browser source 并输出 partial evidence card。
- P2 browser source 不得阻塞 P0/P1 已完成 evidence 输出。
- execution 开始时先写 observation skeleton；最终 timeout 也必须写 partial / timeout observation。

## 5.2 ATO 小批量客诉执行与登录日志边界

2-9 个 `user_id` 的 ATO 客诉小批量默认进入 `small_batch_execution_with_checkpoint`，不是纯 plan-only，也不是 10+ 的 batch clustering。

执行规则：

- 允许逐个查 P0 source，优先统一登录日志。
- 只对异常用户补 P1 source：Weapon、天师策略命中、设备 SDK、档案中心画像等。
- 默认不进入 P2 browser source。
- 每个 user/source 独立 checkpoint。
- 单用户 auth_failed / timeout / blocked / parse_error 不得导致整体无输出。

统一登录日志 source boundary：

- 在线 API 约 7 天可靠窗口。
- admin / user-center-workbench 主要覆盖 APP 登录、refresh token、密码验证等登录侧行为。
- 客诉时间不在在线窗口内时，必须标 `login_log_window_incomplete` 与 `source_time_range_gap`。
- APP 登录日志 no_data、单 DID、IP 稳定，只能写“登录日志侧可见窗口内未见强异常，ATO 证据不足”。
- 不得仅凭 APP 登录日志输出“低风险 / 无风险 / 排除 ATO”。
- 扫码 / OAuth / 地推欺诈 / 陌生链接诱导 / 发布违规 / 好友删除类客诉，必须标 `app_login_only_source_gap`、`missing_oauth_or_scan_chain`、`missing_publish_audit`、`missing_device_sdk`、`missing_strategy_hit`。

## 6. ATO 离线 Hive 数据源运行态规则

在线统一登录日志只按近 7 天可靠窗口处理。历史 ATO / 盗号 case、超窗 case、批量 ATO case 不能把在线 no_data / 超窗 no_data 写成“无登录异常”或“无 ATO 风险”反证。

必须标记：

- `login_log_window_incomplete`
- `offline_hive_required`
- `online_login_log_may_be_false_negative`

### 6.1 选表规则

| 用户问题 | runtime 选表 | 关键约束 |
|---|---|---|
| 有没有异设备成功登录 / 成功登录轨迹 | `ks_rc_bs.ks_account_login_basic_info` | 成功登录专用，9999 天，全量历史；只查成功登录。 |
| 是否被撞库 / 登录失败 / 暴力破解 | `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` | 表名必须是 `orign`；`p_action_type='login'`；`finalloginresult=1` 成功，其他失败，null 不确定。 |
| 有没有改密 / resetPwd | `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` | `p_action_type='resetPwd'`。 |
| Web/H5 端风控拦截 | `ks_rc_arch.antispam_feature_map_default_partitioned` | 生命周期 30 天；必须限制 `p_date + p_hourmin + p_action_type`。 |
| App 发布 / 登录 / 互动 / 协议风险命中 | `ks_raw_log_v2.antispam_feature_map_partitioned` | 生命周期 50 天；必须限制 `p_date + p_hourmin + p_action_type`；禁止全表扫描。 |

### 6.2 标准输出

如果在线数据缺失或窗口不足，不能只说“建议补充登录日志”，必须输出 Hive query plan：

```yaml
query_goal:
selected_table:
reason_for_table_selection:
partition_filters:
entity_filters:
key_fields:
expected_signal:
risk_if_missing:
fallback_table:
no_data_interpretation:
```

示例边界：

- `ks_account_login_basic_info` 无数据，只能说明该日期分区未发现成功登录，不代表没有失败登录、未走完流程或改密。
- `dwd_risk_usr_accnt_login_orign_info` 中 `finalloginresult is null` 是流程未完成 / 状态不确定，不得简单写成失败。
- Web RCP 超过 30 天、App RCP 超过 50 天时，必须标记 `source_gap`，不得作为无风险反证。
- DataAgent 只作为 Hive / 数仓取数分析能力，不是万能风控执行器。
