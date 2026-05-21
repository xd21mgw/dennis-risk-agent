# ATO Huawei QuickLogin Batch3 8-case Observation Run 001

## 1. Batch 基础信息

- sample_set_id: `ato_huawei_quicklogin_xiaomi_reset_20260520`
- run_id: `ato_huawei_quicklogin_batch3_8_case_observation_run_001`
- run_type: `readonly_batch_observation_summary`
- source: `internal_dennis_sub_agent_returned_observation`
- batch_scope:
  - ato_013: `628988198`
  - ato_014: `2188497621`
  - ato_015: `2678499885`
  - ato_016: `2109589440`
  - ato_017: `2810169785`
  - ato_018: `2816963455`
  - ato_019: `547061183`
  - ato_020: `3101900624`
- previous_completed_scope: `ato_001_to_ato_012`
- cumulative_completed_scope: `ato_001_to_ato_020`
- full_20_case_confirmation_generated: true

## 2. 执行边界

- readonly_only: true
- platform_write_action: false
- dataagent_called: false
- no_sensitive_plaintext: true
- full_ip_output: false
- cookie_token_session_header_output: false
- release_package_updated: false

本 run log 只落盘内部 Dennis 子 Agent 返回的第三批 8 case readonly observation 摘要，不包含完整 IP、cookie、token、session、header 或完整原始响应。

## 3. ato_013~ato_020 逐案摘要

| case_id | user_id | chain_closed | ip_switch | did_mixing | reported_phone_model | hardware_or_weapon_status | key_new_behavior | support_level |
|---|---:|---|---|---|---|---|---|---|
| ato_013 | 628988198 | true | true | true | Xiaomi(MI 8 Lite) | hardware_mismatch_or_weapon_no_data | template_reproduced | strong |
| ato_014 | 2188497621 | true | true | true | Xiaomi(MI 8 Lite) | hardware_mismatch_or_weapon_no_data | repeated_ato_and_message_setting_control | strong |
| ato_015 | 2678499885 | true | true | true | Xiaomi(MI 8 Lite) | hardware_mismatch_or_weapon_no_data | template_reproduced | strong |
| ato_016 | 2109589440 | true | true | true | Xiaomi(MI 8 Lite) | hardware_mismatch_or_weapon_no_data | template_evolution_real_redmi_to_fake_xiaomi | strong |
| ato_017 | 2810169785 | true | true | true | Xiaomi(MI 8 Lite) | hardware_mismatch_or_weapon_no_data | template_reproduced | strong |
| ato_018 | 2816963455 | true | true | true | Xiaomi(MI 8 Lite) | hardware_mismatch_or_weapon_no_data | forged_other_model_message_setting_control | strong |
| ato_019 | 547061183 | true | true | true | Xiaomi(MI 8 Lite) | OPPO_PDYM20_overlap_with_ato_001 | most_intense_countermeasure | strong |
| ato_020 | 3101900624 | true | true | true | Xiaomi(MI 8 Lite) | hardware_mismatch_or_weapon_no_data | template_reproduced | strong |

## 4. 第三批 batch_level_findings

- total_cases: 8
- initial_login_observed_count: 8
- reset_event_observed_count: 8
- complete_login_to_reset_chain_count: 8
- ip_switch_count: 8
- did_mixing_count: 8
- phone_model_mismatch_or_weapon_no_data_count: 8
- reported_phone_model_or_xiaomi_like_param_count: 8
- wind_control_or_stolen_mark_observed: `observed_in_batch`
- attack_template_reproduced_count: 8
- full_20_cases_confirmed_after_batch3: true

## 5. 第三批新增发现

### 5.1 ato_014 / ato_016 二次或多次 ATO / 改密

- observed_cases: `ato_014`, `ato_016`
- finding: 出现二次或多次 ATO / 改密信号。
- interpretation: 攻击不是单次 reset 完成后结束，部分样本存在重复控制权争夺。
- boundary: 不输出完整 IP、token 或 session，只保留链路摘要。

### 5.2 ato_016 伪造模板升级

- observed_case: `ato_016`
- finding: 出现伪造模板升级，从真实 Redmi 上报切换为统一 Xiaomi(MI 8 Lite) 伪造模板。
- interpretation: 攻击侧可能在不同阶段使用不同 reported_phone_model，最终收敛到统一 Xiaomi(MI 8 Lite) 模板。
- boundary: reported_phone_model 不是可信硬件画像。

### 5.3 ato_019 与 ato_001 同型号 OPPO PDYM20 攻击设备

- observed_cases: `ato_019`, `ato_001`
- finding: ato_019 与 ato_001 出现同型号 OPPO PDYM20 攻击设备画像。
- interpretation: 可能存在同类硬件基建或同一攻击设备池线索。
- boundary: 同型号硬件不等于同一物理设备，需要 device_id / graph / 行为链路补证。

### 5.4 ato_019 攻防对抗最激烈

- observed_case: `ato_019`
- finding: 5+ 设备/IP 试图接管，风控踢登录态 20+ 次。
- interpretation: 攻击者持续争夺控制权，风控与攻击操作多轮对抗。
- boundary: IP 只保留脱敏网段，不输出完整 IP。

### 5.5 ato_014 / ato_018 改密后号商操控行为

- observed_cases: `ato_014`, `ato_018`
- finding: 改密后存在伪造不同机型修改私信设置的号商操控行为。
- interpretation: reset 后存在账号配置/私信能力方向的后续操控。
- boundary: 后续操控是 ATO 后置行为证据，不等于新的独立风险类型。

## 6. evidence_quality

- batch3_evidence_quality: `high`
- reason: 8/8 样本均复现完整 login → reset 闭环、IP 切换、did 混用、reported Xiaomi(MI 8 Lite) 或同类 Xiaomi 伪造参数、真实硬件不一致或 Weapon 无设备画像，并新增重复 ATO、模板升级、同型号攻击设备、强攻防对抗等证据。

## 7. ato_batch_support_level

- batch3_ato_support_level: `strong`
- reason: 第三批 8/8 复现攻击模板，并补充攻击演进和攻防对抗细节。
- boundary:
  - strong 针对 ato_013~ato_020。
  - 本文件同时确认累计 20/20 已完成观察并形成闭环。

## 8. Full Scope Confirmation

- whether_full_20_cases_confirmed: true
- confirmed_scope: `ato_001_to_ato_020`
- confirmation_basis:
  - first_batch_5_of_5_reproduced
  - second_batch_7_of_7_reproduced
  - third_batch_8_of_8_reproduced
- boundary:
  - 只代表本 sample_set 20 个 case。
  - 不推导到其他未查样本。
  - 不自动处置。
  - 不自动上线策略。

## 9. 禁止表达

禁止输出：

- “小米设备改密。”
- “所有类似样本都成立。”
- “可以直接封禁。”
- “可以直接上线。”
- “Weapon 无数据就是无风险。”

允许输出：

- “第三批 8/8 复现攻击模板。”
- “累计 20/20 在本 sample_set 内形成完整 ATO 闭环。”
- “改密侧统一上报 Xiaomi(MI 8 Lite) 或同类 Xiaomi 伪造参数，但真实硬件不一致或 Weapon 无设备画像。”
