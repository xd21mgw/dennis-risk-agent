# ATO Huawei QuickLogin 5-case Batch Observation Run 001

## 1. Batch 基础信息

- sample_set_id: `ato_huawei_quicklogin_xiaomi_reset_20260520`
- run_id: `ato_huawei_quicklogin_5_case_batch_observation_run_001`
- run_type: `readonly_batch_observation_summary`
- source: `internal_dennis_sub_agent_returned_observation`
- batch_scope:
  - ato_001: `4910098437`
  - ato_002: `5376326876`
  - ato_003: `3635896641`
  - ato_004: `4382576023`
  - ato_005: `1705514992`
- batch_summary_generated: true
- full_20_case_conclusion_generated: false

## 2. 执行边界

- readonly_only: true
- platform_write_action: false
- dataagent_called: false
- no_sensitive_plaintext: true
- full_ip_output: false
- cookie_token_session_header_output: false
- release_package_updated: false

本 run log 只落盘内部 Dennis 子 Agent 返回的 5 case readonly observation 摘要，不包含完整 IP、cookie、token、session、header 或完整原始响应。

## 3. 逐案摘要

| case_id | user_id | initial_login_observed | reset_event_observed | chain_closed | ip_switch | did_mixing | phone_model_mismatch | post_reset_wind_control_or_stolen | evidence_quality | support_level |
|---|---:|---|---|---|---|---|---|---|---|---|
| ato_001 | 4910098437 | true | true | true | true | true | true | true | medium | strong |
| ato_002 | 5376326876 | true | true | true | true | true | true | true | high | strong |
| ato_003 | 3635896641 | true | true | true | true | true | true | true | high | strong |
| ato_004 | 4382576023 | true | true | true | true | true | true | true | high | strong |
| ato_005 | 1705514992 | true | true | true | true | true | true | true | high | strong |

逐案补充：

- ato_001: 已在单 case run log 中确认 quickLogin/token 下发后约 3 分 45 秒发生 byToken/logined 改密，存在 IP 网段突变、did 混用、reported_phone_model 与硬件画像不一致。
- ato_002: 形成完整 login → reset 闭环，观察到 IP 网段切换、did 混用、reported_phone_model 与 hardware_reported_model 不一致，后续出现风控踢登录态或风控推被盗。
- ato_003: TOP case。改密后存在 50+ 次 `changeOption` 操控行为，且越狱/代理/未插 SIM/未锁屏等设备高危标签明显。
- ato_004: 形成完整 login → reset 闭环，存在统一上报 Xiaomi(MI 8 Lite) 但真实硬件不一致，后续出现风控相关被盗/踢登录态信号。
- ato_005: 形成完整 login → reset 闭环，存在 IP 网段切换、did 混用、reported/hardware model mismatch 和后续风控信号。

## 4. batch_level_findings

- total_cases: 5
- initial_login_observed_count: 5
- reset_event_observed_count: 5
- complete_login_to_reset_chain_count: 5
- ip_switch_count: 5
- did_mixing_count: 5
- phone_model_mismatch_count: 5
- reset_device_multi_user_count: `observed_in_batch`
- wind_control_or_stolen_mark_count: 5
- reported_phone_model_all: `Xiaomi(MI 8 Lite)`
- hardware_reported_model_distribution: `OPPO / vivo / iPhone / HUAWEI`
- post_reset_behavior_observed: true

## 5. cross_case_key_insight

- attack_template_identified: true
- template_name: `华为鸿蒙 token/quickLogin → 8.136 网段 byToken/logined 改密 → 伪造 Xiaomi(MI 8 Lite)`
- shared_login_ip_cluster: `login_ip_cluster_redacted`
- shared_reset_ip_cluster: `8.136.xxx.xxx`
- fake_phone_model: `Xiaomi(MI 8 Lite)`
- did_pattern: `did_mixing_observed_5_of_5`
- phone_model_pattern: `reported_phone_model_all_xiaomi_but_hardware_mismatch_5_of_5`
- timing_distribution: `login_to_reset_short_interval_observed`
- concurrent_events:
  - post_reset_wind_control_kick_or_stolen_mark
  - post_reset_behavior_present

关键洞察：

- 不应写成“小米设备改密”。
- 正确口径是：改密侧统一上报 `Xiaomi(MI 8 Lite)`，但 Weapon 真实硬件均不一致，分别落在 OPPO、vivo、iPhone、HUAWEI 等硬件画像。
- 这更像 reported_phone_model 伪造 / 上报不一致，而不是一批真实小米设备统一改密。

## 6. TOP case

- top_case_id: `ato_003`
- user_id: `3635896641`
- reason:
  - 改密后存在 50+ 次 `changeOption` 操控行为。
  - 设备高危标签明显，包括越狱/代理/未插 SIM/未锁屏等。
  - 该 case 对“改密后持续操控”链路的支持最强。
- boundary:
  - TOP case 只代表本 5 case 样本内最强样例。
  - 不代表 20 case 全量都具备相同强度。

## 7. missing_evidence

- full_token_session_link_detail_redacted_or_not_persisted
- exact_full_ip_not_persisted_by_policy
- normal_recovery_flow_countercheck
- user_usual_device_and_ip_baseline
- complete_post_reset_behavior_timeline_for_all_cases
- admin_or_audit_context_for_reset_login_type_99
- hardware_reported_model_semantics_review

## 8. evidence_quality

- batch_evidence_quality: `high`
- reason: 5/5 样本均观察到 initial login、reset event、完整 login → reset 闭环、IP 网段切换、did 混用、reported/hardware phone model mismatch，以及后续风控踢登录态或被盗事件。

## 9. ato_batch_support_level

- ato_batch_support_level: `strong`
- reason: 5 case 样本内攻击模板高度一致，且多个强区分信号共现。
- boundary:
  - strong 只针对本轮 5 case batch scope。
  - 不推断全量 20 case 已全部成立。
  - 需要 ato_006~ato_020 继续只读 observation 验证。

## 10. Expansion Decision

- should_expand_to_20: true
- expansion_scope: `ato_006_to_ato_020`
- reason: 5/5 样本已支持攻击模板存在，且模板信号稳定，适合扩展验证是否 20/20 复现。

## 11. 下一步建议

1. 内部 Agent 扩到 ato_006~ato_020。
2. 验证攻击模板是否 20/20 复现。
3. 重点观察 `login_ip_cluster`。
4. 重点观察 `reset_ip_cluster`。
5. 重点观察 `did_mixing`。
6. 重点观察 `phone_model_mismatch`。
7. 重点观察 `stolen_mark_batch`。
8. 重点观察 `post_reset_behavior`，尤其是否存在持续 `changeOption` 或其他控制权后续操作。

## 12. 禁止扩展结论

本 run log 不允许输出：

- “20 个 case 全部成立。”
- “所有 Xiaomi(MI 8 Lite) 都是真实硬件。”
- “reset_login_type=99 必然盗号。”
- “可以直接上线策略。”
- “可以自动处置账号。”

允许输出：

- “5/5 样本支持扩到 20。”
- “5 case batch 内观察到稳定攻击模板。”
- “改密侧统一上报 Xiaomi(MI 8 Lite)，但真实硬件画像不一致。”
