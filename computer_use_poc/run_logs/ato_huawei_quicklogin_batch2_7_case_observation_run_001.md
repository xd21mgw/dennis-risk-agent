# ATO Huawei QuickLogin Batch2 7-case Observation Run 001

## 1. Batch 基础信息

- sample_set_id: `ato_huawei_quicklogin_xiaomi_reset_20260520`
- run_id: `ato_huawei_quicklogin_batch2_7_case_observation_run_001`
- run_type: `readonly_batch_observation_summary`
- source: `internal_dennis_sub_agent_returned_observation`
- batch_scope:
  - ato_006: `4540329365`
  - ato_007: `2384142803`
  - ato_008: `237419164`
  - ato_009: `5501335684`
  - ato_010: `3469247246`
  - ato_011: `5121621748`
  - ato_012: `5439409930`
- previous_completed_scope: `ato_001_to_ato_005`
- cumulative_completed_scope: `ato_001_to_ato_012`
- full_20_case_conclusion_generated: false

## 2. 执行边界

- readonly_only: true
- platform_write_action: false
- dataagent_called: false
- no_sensitive_plaintext: true
- full_ip_output: false
- cookie_token_session_header_output: false
- release_package_updated: false

本 run log 只落盘内部 Dennis 子 Agent 返回的第二批 7 case readonly observation 摘要，不包含完整 IP、cookie、token、session、header 或完整原始响应。

## 3. ato_006~ato_012 逐案摘要

| case_id | user_id | initial_login_observed | reset_event_observed | chain_closed | ip_switch | did_mixing | reported_phone_model | hardware_or_weapon_status | post_reset_behavior | support_level |
|---|---:|---|---|---|---|---|---|---|---|---|
| ato_006 | 4540329365 | true | true | true | true | true | Xiaomi(MI 8 Lite) | hardware_mismatch_or_weapon_gap | observed | strong |
| ato_007 | 2384142803 | true | true | true | true | true | Xiaomi(MI 8 Lite) | protocol_forged_ios_uuid_or_weapon_no_data | attack_continued_after_kick | strong |
| ato_008 | 237419164 | true | true | true | true | true | Xiaomi(MI 8 Lite) | hardware_mismatch_or_weapon_gap | forged_nokia_x6_private_message_setting_change | strong |
| ato_009 | 5501335684 | true | true | true | true | true | Xiaomi(MI 8 Lite) | hardware_mismatch_or_weapon_gap | observed | strong |
| ato_010 | 3469247246 | true | true | true | true | true | Xiaomi(MI 8 Lite) | hardware_mismatch_or_weapon_gap | three_device_ip_takeover_attempts_after_reset | strong |
| ato_011 | 5121621748 | true | true | true | true | true | Xiaomi(MI 8 Lite) | hardware_mismatch_or_weapon_gap | observed | strong |
| ato_012 | 5439409930 | true | true | true | true | true | Xiaomi(MI 8 Lite) | hardware_mismatch_or_weapon_gap | observed | strong |

逐案补充：

- ato_006: 第二批中继续复现 login → reset 闭环、IP 网段切换、did 混用、reported_phone_model 与真实硬件画像不一致或 Weapon 数据缺口。
- ato_007: 出现攻防对抗行为；风控踢登录态后，攻击者继续 iOS token 接管，且存在协议伪造 iOS UUID / Weapon 无数据现象。
- ato_008: 改密后观察到伪造 Nokia X6 修改私信设置，说明 reset 后存在继续操控行为。
- ato_009: 复现统一上报 Xiaomi(MI 8 Lite) 和链路闭环，真实硬件不一致或 Weapon 画像缺口仍需模板字段承载。
- ato_010: 改密后 3 个不同设备/IP 试图接管，是第二批中后续控制权争夺最明显的样本之一。
- ato_011: 复现第二批核心模板，后续风控相关信号存在。
- ato_012: 复现第二批核心模板，支持继续扩量验证。

## 4. 第二批 batch_level_findings

- total_cases: 7
- initial_login_observed_count: 7
- reset_event_observed_count: 7
- complete_login_to_reset_chain_count: 7
- ip_switch_count: 7
- did_mixing_count: 7
- phone_model_mismatch_or_weapon_no_data_count: 7
- reported_phone_model_all: `Xiaomi(MI 8 Lite)`
- wind_control_or_stolen_mark_observed: `observed_in_batch`
- post_reset_behavior_observed: true
- attack_template_reproduced_count: 7

## 5. 第二批新增发现

### 5.1 协议伪造 iOS UUID / Weapon 无数据现象

- observed_in: `ato_007`
- finding: 存在协议伪造 iOS UUID 或 Weapon 无设备画像现象。
- interpretation: 这类现象说明 reported device / protocol identity 与 Weapon 可识别硬件画像之间存在缺口，需在模板中保留 `weapon_no_data_or_protocol_forged_identity` 语义。
- boundary: Weapon 无数据不等于无设备风险，也不等于无异常。

### 5.2 ato_008 / ato_010 改密后操控行为

- ato_008: 改密后伪造 Nokia X6 修改私信设置。
- ato_010: 改密后 3 个不同设备/IP 试图接管。
- interpretation: reset 后不是静态事件，存在后续控制权争夺或配置修改行为。
- boundary: 不输出完整 IP，只记录脱敏网段和行为摘要。

### 5.3 ato_007 攻防对抗行为

- observed_in: `ato_007`
- finding: 风控踢登录态后，攻击者继续 iOS token 接管。
- interpretation: 说明攻击者并非一次性改密后退出，而可能持续尝试维持或恢复控制权。
- boundary: token 只记录存在性和链路摘要，不输出明文。

## 6. evidence_quality

- batch2_evidence_quality: `high`
- reason: 7/7 样本均观察到 initial login、reset event、完整 login → reset 闭环、IP 切换、did 混用、reported_phone_model 为 Xiaomi(MI 8 Lite)，且均存在真实硬件不一致或 Weapon 无数据现象。

## 7. ato_batch_support_level

- batch2_ato_support_level: `strong`
- reason: 第二批 7 case 中攻击模板 7/7 复现，并新增协议伪造 iOS UUID / Weapon 无数据、改密后操控、攻防对抗等强化证据。
- boundary:
  - strong 只针对 ato_006~ato_012。
  - 不推断 ato_013~ato_020 已成立。

## 8. Expansion Decision

- whether_should_continue_to_ato_013_020: true
- reason: 第一批 5/5 与第二批 7/7 均复现攻击模板，累计 12/12 支持继续对剩余 8 case 做只读 observation。

## 9. 禁止扩展结论

禁止输出：

- “20 个 case 已全部成立。”
- “小米设备改密。”
- “Weapon 无数据就是无风险。”
- “可以直接处置。”
- “可以直接上线策略。”

允许输出：

- “第二批 7/7 复现攻击模板。”
- “累计 12/12 支持继续扩量到 ato_013~ato_020。”
- “改密侧统一上报 Xiaomi(MI 8 Lite)，但真实硬件不一致或 Weapon 无数据。”
