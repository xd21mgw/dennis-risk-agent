# Black Market Account Matrix v2 Targeted Rerun

## 1. Execution Scope

- sample_set_id: `black_market_account_matrix_sample_set`
- sample_set_type: `black_market_account_matrix`
- is_ato: false
- run_id: `black_market_matrix_v2_targeted_rerun`
- run_type: `targeted_readonly_rerun_summary`
- source: `internal_agent_returned_observation`
- readonly_only: true
- platform_write_action: false
- dataagent_called: false
- no_sensitive_plaintext: true
- release_package_updated: false

本 run log 只落盘内部 Agent 返回的 targeted rerun 摘要，并对统一登录日志在线窗口口径做纠偏。不调用真实平台，不调用 DataAgent，不输出敏感明文。

## 2. Source Status

| source | status | interpretation |
|---|---|---|
| 档案中心 | success | 可读取当前 profile、负向标签、封禁状态 |
| Weapon | success | 可读取设备与风险标签摘要 |
| 统一登录日志 | invalid_over_window_query / login_log_window_incomplete / offline_hive_required | 超长窗口 `totalCount=0` 不作为 counter evidence，也不作为 log cleanup evidence |
| 天司 / 天狮 | 2FA blocked | 不作为 no_data，不进入反证 |
| 行为链 | not_reached | 关注 / 点赞 / 评论 / 私信对象聚集仍是最大缺口 |

## 3. Profile Template Verification

- current_profile_status: `current_profile_default_or_empty`
- before_after_status: `current_profile_default_or_empty`
- current_state:
  - 5/5 UID 当前均为默认昵称 `快手用户+数字`。
  - 5/5 当前简介为空。
- original_profile_status:
  - 原始模板化用户名和同构简介已被重置。
  - 用户名 / 昵称 / 简介三层同构仍保留为原始样本模式，但当前资料状态不能直接复现原始截图。
- original_template_pattern:
  - 用户名 / 昵称：数字 + emoji + “茨 / 佰 / 四 / 五 / 六 / 三”等近似字符组合。
  - 简介：`一起互动 + 薇[redacted]`。

证据解释：

- 当前默认昵称 + 空简介不是强风险证据。
- 当前默认昵称 + 空简介更可能是治理后的 cleanup aftermath 或资料变化结果。
- 该解释是 hypothesis，需要 profile_change_history / adminaction reason / audit log / before-after diff 继续确认。

## 4. Profile Cleanup Evidence

- three_layer_ban_effective: true
- ban_layers:
  - username_modify_forbidden
  - intro_modify_forbidden
  - avatar_modify_forbidden
- rollout_time_range: `2026-04-28_to_2026-05-19`
- archives_negative_label: `头像昵称重置`
- cleanup_evidence_strength: `partial`

证据边界：

- `actionBan + 负向标签` 能证明封禁生效和重置发生。
- reviewLogs 为空，不能确认操作者、触发原因、清理时间细节。
- 因此三层封禁 / 头像昵称重置是 medium-strong evidence，但不是 strong closed-loop。

## 5. Adminaction Reason Status

- adminaction_code: `2011262`
- adminaction_meaning: `unknown`
- archives_api_exposes_adminaction_field: false
- known_negative_record_terms:
  - `生态审-机审`
  - `业务安全-机审处置`

口径：

- `生态审-机审` 和 `业务安全-机审处置` 不能等价解释为 adminaction=2011262。
- adminaction=2011262 的含义仍需后续通过 adminaction 字典、审核原因或权限更高的审计链路确认。

## 6. Device / Registration / Login Summary

- matrix_shape: `single_device_single_account_distributed_matrix`
- not_primary_shape: `traditional_same_device_multi_account_group_control`
- registration_ip_cohorts:
  - 湖北移动 `223.104.xxx.xxx`: 3 cases
  - 非湖北电信网段: 2 cases
- registration_time_cohort:
  - 样本注册时间 / 注册天数集中。
- device_signals:
  - `5247058312` 注册设备被另一正常用户后续使用，提示设备共享 / 回收。
  - `5239767360` 是 1:1 单设备，但 Weapon 标记“机器小号” + 屏锁未设 + 启动少于 10 次。
  - `5239767360` 90 天被 138 人取消关注，存在刷粉痕迹。

解释：

- 1:1 单设备单账号不是低风险证据。
- 在分布式养号矩阵里，1:1 设备配置可能是规避同设备聚集的形态。
- 该批更像“单设备单账号分布式养号矩阵 + 导流小号矩阵”，不是传统同设备多号群控。

## 7. Behavior Chain Gap

- behavior_chain_reached: false
- largest_missing_evidence:
  - 关注对象聚集
  - 粉丝对象聚集
  - 点赞对象聚集
  - 评论对象聚集
  - 私信对象聚集

该缺口决定了当前结论仍应保持 `medium-strong`，不能直接升级为 strong closed-loop。

## 8. Corrected Login Log Window Interpretation

内部 Agent 曾提到“统一登录日志 5/5 全返回 0，即使时间窗口扩大到 2024 年 7 月至今，暗示账号日志可能已被清理”。该口径不落盘为结论。

正确口径：

- 统一登录日志在线 API 按约 7 天可靠窗口处理。
- 超出可靠窗口的查询返回 0 / no_data / `totalCount=0`，不代表历史无登录。
- 超出可靠窗口的查询返回 0 / no_data / `totalCount=0`，不能推断日志被清理。
- 对 `2024 年 7 月至今` 这类超长时间窗查询，应标记：
  - `invalid_over_window_query`
  - `login_log_window_incomplete`
  - `offline_hive_required`
- 后续内部 Agent 在调用统一登录日志前必须做 `reliable_window_precheck`。
- 如果 event_time 超过近 7 天，默认不要调用在线统一登录日志做验证；只在说明窗口缺口后建议 DataAgent / Hive 或离线日志补查。
- 不得将 over-window no_data / `totalCount=0` 写入 counter evidence。
- 不得将 over-window no_data / `totalCount=0` 写成 log cleanup evidence。

区分边界：

- profile cleanup / 头像昵称重置是档案中心负向标签、actionBan、三层封禁等资料治理证据。
- login log cleanup 是另一类日志存储 / 日志可见性假设，本轮没有证据支持。
- 不得用统一登录日志 over-window `totalCount=0` 推断 login log cleanup。

## 9. Evidence Strength

| evidence | strength | calibration |
|---|---|---|
| 简介 + 外部联系方式原始同构 | strong | 原始样本中 `一起互动 + 薇[redacted]` 是导流小号矩阵强证据 |
| 用户名 / 昵称模板化 | medium-strong | 数字 + emoji + 近似字符组合支持批次化账号模板 |
| 头像昵称重置 / 三层封禁 | medium-strong | reviewLogs 缺失，因此不是 strong closed-loop |
| 注册 IP cohort | strong | 湖北移动 `223.104.xxx.xxx` 3 个 + 非湖北电信 2 个形成 cohort |
| Weapon 机器小号 | strong | 设备侧强风险标签 |
| 无 SIM / WiFi / 刷粉 | medium-strong | 与小号矩阵、低成本养号、刷粉痕迹叠加 |
| 当前默认昵称 / 空简介 | cleanup aftermath / weak if alone | 可能是治理后资料重置结果，单独不构成强证据 |
| 1:1 单设备单账号 | shape correction evidence | 不是低风险证据，也不是强风险证据 |

## 10. Conclusion

- matrix_support_level: `medium-strong`
- evidence_quality: `medium`
- primary_shape: `单设备单账号分布式养号矩阵`
- secondary_shape: `导流小号矩阵`
- is_ato: false
- not_primary_shape: `传统同设备多号群控`

结论：v2 targeted rerun 增强了 black_market_account_matrix 假设，尤其是资料三层同构被治理后重置、注册 IP cohort、Weapon 机器小号、设备/刷粉痕迹等信号。但行为链未触达、adminaction 含义未知、reviewLogs 为空，因此仍保持 medium-strong，不直接进入自动处置。

## 11. Conclusion Boundary

- 该结论只覆盖本轮 5 case targeted rerun，不推导到其他未查样本。
- medium-strong 支持来自 profile 模板同构、profile cleanup 证据、注册 IP / 时间 cohort、Weapon 机器小号、设备 / 刷粉痕迹等多信号叠加。
- 当前仍缺行为链对象聚集、adminaction 含义、reviewLogs 细节和天狮 / RCP 策略链路。
- profile cleanup / 头像昵称重置可以作为资料治理证据，但不能和 login log cleanup 混淆。
- 统一登录日志 over-window no_data / `totalCount=0` 只能作为 data gap，不作为反证，不作为日志清理证据。

## 12. Data Quality Risks

- unified_login_log_reliable_window_days≈7
- over_window_no_data_not_counter_evidence: true
- over_window_no_data_not_log_cleanup_evidence: true
- adminaction_not_exposed_by_current_platforms: true
- review_logs_empty_not_proof_of_no_audit: true

说明：

- 统一登录日志在线 API 只按近 7 天可靠窗口处理；超长窗口查询不具备历史完整性解释力。
- adminaction=2011262 当前未被档案中心 API 直接暴露含义；负向记录中的“生态审-机审”“业务安全-机审处置”不能等价解释为 adminaction。
- reviewLogs 为空只能说明当前读取路径未见审核日志明细，不能证明没有审核、没有资料清理动作或没有触发原因。

## 13. Next Step

1. 优先确认 adminaction=2011262 含义。
2. 触达行为链：关注 / 粉丝 / 点赞 / 评论 / 私信对象聚集。
3. 天狮 / RCP 2FA 恢复后查策略命中链路。
4. 需要离线长周期登录 / 注册聚合时，再转 DataAgent / Hive。
5. 后续调用统一登录日志前必须执行 reliable_window_precheck。

## 14. Boundary

- 不调用真实平台。
- 不调用 DataAgent。
- 不修改 release/dist。
- 不输出敏感明文。
- 不把统一登录日志 over-window no_data / `totalCount=0` 写成 counter evidence。
- 不把 over-window no_data / `totalCount=0` 写成 log cleanup evidence。
- 不自动处置，不自动封禁。
