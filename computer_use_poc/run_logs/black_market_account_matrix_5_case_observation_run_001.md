# Black Market Account Matrix 5-case Observation Run 001

## 1. Batch 基础信息

- sample_set_id: `black_market_account_matrix_sample_set`
- sample_set_type: `black_market_account_matrix`
- is_ato: false
- run_id: `black_market_account_matrix_5_case_observation_run_001`
- run_type: `readonly_batch_observation_summary`
- source: `internal_dennis_sub_agent_returned_observation`
- batch_scope:
  - case_001: `5247058312`
  - case_002: `5239767360`
  - case_003: `5239608274`
  - case_004: `5144733991`
  - case_005: `5142005372`

本轮只总结黑产账号矩阵 / 导流小号矩阵 readonly observation，不属于 ATO 主线，不套用华为 quickLogin / byToken/logined 改密模板。

## 2. 执行边界

- readonly_only: true
- platform_write_action: false
- dataagent_called: false
- no_sensitive_plaintext: true
- full_ip_output: false
- cookie_token_session_header_output: false
- release_package_updated: false
- auto_disposition: false

本 run log 不包含完整 IP、手机号、cookie、token、session、header 或完整原始响应。IP 只保留脱敏网段。

## 3. 平台访问状态

| platform_or_hand | status | note |
|---|---|---|
| 档案中心 | success | profile / account status / relation summary 可读 |
| Weapon | success | device risk / relation signal 可读 |
| 统一登录日志 | success | login network / device activity summary 可读 |
| 天司/天狮 | 2FA blocked | 本轮不作为 no_data，不纳入反证 |
| 行为链 | not_reached | 行为链证据缺失，进入 missing_evidence |

## 4. 逐案摘要

| case_id | user_id_ref | profile_pattern | device_pattern | network_or_registration_pattern | key_risk_signal | case_level_judgement |
|---|---|---|---|---|---|---|
| case_001 | `5247058312` | 系统默认昵称 `快手用户+数字串`，空简介 | 单设备单账号 | 注册 IP 落在湖北移动 `223.104.xxx.xxx`，注册时间集中于 2026-01-06~10 窗口 | 与 case_002~003 存在注册 IP / 时间窗口聚集 | 支持分布式养号矩阵候选 |
| case_002 | `5239767360` | 系统默认昵称，空简介；昵称与 case_005 完全一致：`快手用户1775035732028` | 单设备单账号 | 注册 IP 落在湖北移动 `223.104.xxx.xxx`，注册时间集中于 2026-01-06~10 窗口 | Weapon 标注“机器小号” | 强支持小号矩阵候选 |
| case_003 | `5239608274` | 系统默认昵称，空简介 | 单设备单账号 | 注册 IP 落在湖北移动 `223.104.xxx.xxx`，注册时间集中于 2026-01-06~10 窗口 | WiFi 批量命名规则 `WIFI157`，IP 维度设备聚集异常 | 强支持分布式矩阵候选 |
| case_004 | `5144733991` | 系统默认昵称，空简介 | 单设备单账号 | 注册时间集中于 2025-11-12~14 窗口 | 与 case_005 形成另一注册时间 cohort | 中等支持小号矩阵候选 |
| case_005 | `5142005372` | 系统默认昵称，空简介；昵称与 case_002 完全一致：`快手用户1775035732028` | 单设备单账号 | 注册时间集中于 2025-11-12~14 窗口 | 无 SIM + WiFi 名 `BB4` + 刷粉特征 | 强支持导流 / 互动小号矩阵候选 |

## 5. Batch-level Findings

- total_cases: 5
- profile_read_success_count: 5
- device_resolution_success_count: 5
- login_log_read_success_count: 5
- strategy_hit_read_success_count: 0
- strategy_hit_blocked_reason: `2FA_blocked`
- behavior_chain_reached: false
- original_profile_three_layer_isomorphism_signal:
  - 用户补充截图显示，这批账号在原始样本侧存在用户名 / 昵称 / 简介三层同构。
  - 用户名 / 昵称呈现明显模板化：数字 + emoji + “茨 / 佰 / 四 / 五 / 六 / 三”等近似字符组合。
  - 简介高度一致：`一起互动 + 薇[redacted]`。
  - 该模式与 adminaction、注册天数、日期集中和 UID 号段聚集共同构成账号矩阵证据。
- profile_cleanup_hypothesis:
  - 后续内部 Agent observation 中出现默认昵称 + 空简介，可能是系统治理后清理资料或账号状态变化导致。
  - 该解释目前只能标记为 hypothesis / needs_verification，不能写成已确认事实。
  - 需要审核日志、adminaction 明细、资料变更记录或原始资料 before/after diff 进一步确认。
- nickname_template_match_count: 5
- intro_empty_or_pattern_match_count: 5
- single_device_single_account_count: 5
- shared_device_count: 0
- registration_ip_cluster_signal:
  - case_001~case_003 聚集在湖北移动 `223.104.xxx.xxx` 网段。
- registration_time_cluster_signal:
  - case_001~case_003 集中在 2026-01-06~10。
  - case_004~case_005 集中在 2025-11-12~14。
- duplicate_nickname_signal:
  - case_002 与 case_005 昵称完全一致：`快手用户1775035732028`。
- device_risk_overlap_signal:
  - case_002 Weapon “机器小号”。
  - case_003 WiFi 批量命名规则 + IP 维度设备聚集异常。
  - case_005 无 SIM + WiFi 名 + 刷粉特征。

## 6. Evidence Strength Calibration

### 6.1 强证据 / Strong Evidence

1. 原始样本简介高度一致：`一起互动 + 薇[redacted]`。简介一致且包含外部联系方式，是导流小号矩阵的强证据。
2. case_001~003 注册 IP 同属湖北移动 `223.104.xxx.xxx` 网段，且注册时间集中，支持同批次注册 / 养号 cohort。
3. case_002 被 Weapon 标注“机器小号”，是设备侧强风险标签。

### 6.2 中强证据 / Medium-strong Evidence

1. 原始样本用户名 / 昵称模板化相似：数字 + emoji + “茨 / 佰 / 四 / 五 / 六 / 三”等近似字符组合，支持账号批次化生成。
2. case_002 与 case_005 后续昵称完全一致：`快手用户1775035732028`，支持账号模板化生成或资料重置后的重复状态。
3. case_004~005 注册时间形成独立小 cohort，支持批次化样本线索。
4. case_003 WiFi 批量命名规则 `WIFI157` + IP 维度设备聚集异常。
5. case_005 无 SIM + WiFi 名 `BB4` + 刷粉特征。

### 6.3 弱辅助 / 背景特征

1. 5/5 系统默认昵称 `快手用户+数字串`。
2. 5/5 空简介。

校准说明：

- `快手用户+数字串` 是平台注册后的正常默认昵称，不能单独作为黑产强证据。
- 空简介同样只能作为弱辅助 / 背景特征。
- 默认昵称和空简介保留为账号批次化、低成本养号的辅助特征，但必须和注册 IP / 时间 cohort、同昵称精确重复、Weapon 机器小号、WiFi 命名规则、无 SIM、刷粉 / 被取消关注、行为对象聚集等信号叠加后才有判断价值。
- 如果默认昵称 + 空简介是系统治理后清理资料或账号状态变化导致，则它属于后置状态，不应反向覆盖原始样本中的用户名 / 昵称 / 简介三层同构证据。
- 该清理解释需要 profile_change_history、adminaction reason、审核日志或原始资料 before/after diff 验证。

### 6.4 形态修正证据

1. 5/5 单设备单账号，说明这批样本不是传统同设备多账号群控。
2. 1:1 单设备单账号不是低风险证据，也不是强风险证据；它主要用于修正攻击形态，提示可能是分布式养号矩阵。

## 7. Counter Evidence

- shared_device_count=0：未观察到传统“同设备多账号”群控特征。
- 天司/天狮 2FA blocked：缺少策略命中补证，不能用策略无命中作为反证。
- 行为链未触达：尚未直接读取互动、导流、关注、私信等行为序列。
- 5 case 样本规模较小：只能支持 medium-strong hypothesis，不应直接外推为全量结论。

## 8. Missing Evidence

- behavior_chain_observation: 互动、关注、私信、导流路径未触达。
- strategy_hit_observation: 天司/天狮 2FA blocked。
- adminaction_batch_confirmation: adminaction / 社交封禁 / 导流标签需要扩量复核。
- intro_history: 当前为空简介，缺少历史简介变更轨迹。
- profile_change_history: 需要确认用户名 / 昵称 / 简介从原始模板化资料变成默认昵称 / 空简介的时间和原因。
- adminaction_reason_detail: 需要确认 adminaction `2011262` 的具体原因和是否触发资料清理。
- audit_log_for_profile_cleanup: 需要审核日志确认是否存在系统治理后清理昵称 / 简介 / 外部联系方式。
- original_profile_snapshot_or_before_after_diff: 需要原始资料截图或 before/after diff 固化三层同构证据。
- cross_case_content_or_relation: 尚未读取作品、关注对象、粉丝关系或共同目标。
- hive_scale_query: 未调用 DataAgent / Hive 做举一返三。

## 9. Matrix Support Level

- matrix_support_level: `medium-strong`
- evidence_quality: `medium`

判断：本轮 5 case medium-strong 支持 `black_market_account_matrix` 假设，更像“单设备单账号分布式养号矩阵 + 导流小号矩阵”，不是传统同设备多账号群控。

证据强度校准：该结论不是由默认昵称或空简介单独支撑，而是由原始用户名 / 昵称 / 简介三层同构、简介一致 + 外部联系方式、注册 IP / 时间 cohort、同昵称精确重复、Weapon 机器小号、WiFi 命名规则、无 SIM、刷粉等多信号叠加支撑。

边界：该判断只覆盖本轮 5 个已观察 case，不代表自动处置结论，不代表全量黑产账号池已确认。

## 10. 形态判断

- primary_shape: `单设备单账号分布式养号矩阵`
- secondary_shape: `导流小号矩阵`
- not_primary_shape: `传统同设备多账号群控`

解释：

- 1:1 单设备单账号不应被当作低风险反证。
- 在黑产养号矩阵中，单账号单设备可能是为了规避同设备聚集特征。
- 本轮关键不是设备共享，而是原始用户名 / 昵称 / 简介三层同构、注册 IP / 时间 cohort、设备风险标签和后续导流/互动补证的组合。

## 11. 扩量锚点

建议后续 DataAgent / Hive 举一返三优先围绕以下锚点：

1. 同昵称精确匹配：例如 `快手用户1775035732028`。
2. 同注册 IP 网段：湖北移动 `223.104.xxx.xxx`。
3. 同注册时间窗口：2026-01-06~10、2025-11-12~14。
4. WiFi 命名规则：如 `WIFI157`、`BB4` 等批量命名痕迹。
5. 设备风险标签组合：机器小号、无 SIM、IP 维度设备聚集、刷粉特征。
6. adminaction / 社交封禁 / 导流标签。
7. 原始用户名 / 昵称 / 简介三层同构：数字 + emoji + 近似中文字符组合，以及 `一起互动 + 薇[redacted]`。
8. 系统默认昵称 `快手用户+数字串` + 空简介 + 单设备单账号组合仅作为弱辅助和形态修正特征，需要与强/中强信号叠加使用。

## 12. 下一步建议

1. 不直接处置，不直接封禁。
2. 先做 DataAgent / Hive 举一返三，确认同昵称、同注册 IP 网段、同注册时间窗口和设备风险标签组合的规模。
3. 补行为链 observation，确认是否存在导流、互粉、互动、私信、刷粉或共同目标关系。
4. 补策略 / adminaction / 社交封禁 / 导流标签批量分布。
5. 再做策略评估候选规则卡，包含误伤风险、正常反证、灰度指标和查杀分离建议。

## 13. 输出边界

- 不误标为 ATO。
- 不套用华为 quickLogin / byToken/logined 改密模板。
- 不把 1:1 单设备单账号当作低风险。
- 不输出完整 IP、手机号、cookie、token、session、header。
- 不做自动处置。
- 不更新 release 包。
- 不调用真实平台。
- 不调用 DataAgent。
