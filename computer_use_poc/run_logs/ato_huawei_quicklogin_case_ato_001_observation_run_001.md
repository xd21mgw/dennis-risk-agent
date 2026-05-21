# ATO Huawei QuickLogin Case ato_001 Observation Run 001

## 1. Case 基础信息

- sample_set_id: `ato_huawei_quicklogin_xiaomi_reset_20260520`
- case_id: `ato_001`
- user_id: `4910098437`
- observation_type: `single_case_readonly_observation`
- observation_status: `completed_for_single_case`
- batch_summary_generated: false
- full_20_case_conclusion_generated: false

## 2. 执行边界

- readonly_only: true
- platform_write_action: false
- dataagent_called: false
- no_sensitive_plaintext: true
- cookie_token_session_header_output: false
- full_ip_output: false
- release_package_updated: false

本 run log 只沉淀内部 Agent 返回的只读观察摘要，不包含完整 IP、cookie、token、session、header 或完整原始响应。

## 3. initial_login_observed 摘要

- observed: true
- event_time_approx: `2026-05-20 17:56`
- initial_phone_model_reported: `HUAWEI(BLK-AL00)`
- initial_path: `/rest/n/user/login/huawei/quickLogin`
- initial_login_type: `16`
- token_or_session_activity: `token_issued_present_redacted`
- ip_summary_redacted: `183.206.xxx.xxx`
- evidence_summary: 华为 quickLogin 链路在 17:56 左右出现 token 下发。
- evidence_boundary: token 字段只记录存在性和链路摘要，不输出明文。

## 4. reset_event_observed 摘要

- observed: true
- event_time: `2026-05-20 18:00:02`
- reset_path: `/rest/n/user/reset/byToken/logined`
- reset_login_type: `99`
- reported_phone_model: `Xiaomi(MI 8 Lite)`
- hardware_reported_model: `OPPO(PDYM20)`
- reset_device_id_ref: `ANDROID_38c50f76b874e6e0`
- ip_summary_redacted: `8.136.xxx.xxx`
- evidence_summary: 18:00:02 发生 byToken/logined 改密，reset 侧日志 reported_phone_model 为 Xiaomi(MI 8 Lite)，但 Weapon 硬件画像显示 OPPO(PDYM20)。
- evidence_boundary: reported_phone_model 不等于真实硬件画像；必须与 hardware_reported_model 分开记录。

## 5. chain_analysis 摘要

- initial_to_reset_interval: `about_3m45s`
- same_user_confirmed: true
- login_type_16_observed: true
- reset_login_type_99_observed: true
- quicklogin_to_reset_chain_observed: true
- ip_switch_signal: true
- ip_switch_summary_redacted: `183.206.xxx.xxx -> 8.136.xxx.xxx`
- did_mixing_signal: true
- phone_model_spoofing_or_mismatch_signal: true
- reported_to_hardware_model_mismatch: `Xiaomi(MI 8 Lite) reported vs OPPO(PDYM20) hardware`
- normal_recovery_flow_possible: `not_ruled_out`
- counter_evidence_present: `not_observed_in_summary`
- chain_summary: ato_001 中观察到华为 quickLogin/token 下发后约 3 分 45 秒发生 byToken/logined 改密，伴随 IP 网段突变、did 混用、reset 侧 reported_phone_model 与硬件画像不一致。

## 6. related_evidence 摘要

- reset_device_relation_summary:
  - device_ref: `ANDROID_38c50f76b874e6e0`
  - related_user_count: 4
  - banned_user_count: 2
  - social_ban_user_count: 1
  - abnormal_status_user_count: 3
- post_reset_token_activity: present
- stolen_mark: present
- wind_control_kick: present
- wind_control_summary: 后续存在风控踢登录态和风控推被盗事件。
- device_risk_boundary: 设备关联用户和封禁/异常状态是强补证线索，不单独等于最终 ATO 定性。

## 7. missing_evidence

- full_token_session_link_detail_redacted_or_not_persisted
- normal_recovery_flow_countercheck
- user_usual_device_and_ip_baseline
- full_login_timeline_before_17_56
- full_post_reset_action_timeline
- manual_review_of_reported_phone_model_vs_hardware_model_semantics

## 8. evidence_quality

- evidence_quality: `medium`
- reason: 已观察到关键登录与改密链路、时间间隔、IP 突变、did 混用、设备画像不一致和后续风控事件；但仍缺正常找回流程反证、完整 token/session 链路细节和常用设备/IP baseline。

## 9. ato_chain_support_level

- ato_chain_support_level: `strong`
- reason: 单 case 中 quickLogin/token 下发、短时间 byToken/logined 改密、IP 网段突变、did 混用、reported_phone_model 与硬件画像不一致、reset 侧设备多用户异常关联、后续风控踢登录态和被盗事件共同支持 ATO 候选链路。
- boundary: strong 表示 ato_001 单 case 链路支持强，不代表 20 个 case 全量结论。

## 10. Expansion Decision

- should_expand_to_5_cases: true
- expansion_scope: `ato_002_to_ato_005`
- batch_summary_allowed_now: false
- full_20_case_conclusion_allowed_now: false

扩展理由：

- ato_001 证明当前 observation template 能承载核心链路。
- 字段暴露出 reported_phone_model 与硬件画像分离的必要性。
- 需要用 ato_002~ato_005 验证 did 混用、IP 突变、reset 侧设备多用户关联、reported/hardware model mismatch 是否为共性。

## 11. 本次关键纠偏

- `Xiaomi(MI 8 Lite)` 是 reset 日志中的 `reported_phone_model`，不一定是真实硬件。
- Weapon 硬件画像显示 reset 侧设备为 `OPPO(PDYM20)`。
- 后续模板必须区分：
  - `reported_phone_model`
  - `hardware_reported_model`
  - `phone_model_consistency`
- 不能再把 reset 侧 reported_phone_model 直接写成真实硬件机型。

## 12. 下一步建议

1. 扩展 ato_002~ato_005。
2. 重点验证 did 混用是否重复出现。
3. 重点验证 IP 网段突变是否重复出现。
4. 重点验证 reset 侧设备多用户关联是否重复出现。
5. 重点验证 `reported_phone_model` 与 `hardware_reported_model` 不一致是否重复出现。
6. 仍不做 5 case batch summary，直到 ato_002~ato_005 均完成 observation。
7. 不推断全量 20 case 结论。
