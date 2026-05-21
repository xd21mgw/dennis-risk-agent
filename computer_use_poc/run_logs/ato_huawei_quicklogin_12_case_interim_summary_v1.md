# ATO Huawei QuickLogin 12-case Interim Summary v1

## 1. 12 case 总体进展

- sample_set_id: `ato_huawei_quicklogin_xiaomi_reset_20260520`
- summary_type: `interim_summary`
- completed_cases: `ato_001_to_ato_012`
- completed_count: 12
- remaining_cases: `ato_013_to_ato_020`
- remaining_count: 8
- readonly_only: true
- dataagent_called: false
- platform_write_action: false
- release_package_updated: false
- full_20_case_conclusion_generated: false

## 2. 12 case 总体发现

- 12/12 完整 login → reset 闭环。
- 12/12 存在登录 IP 到改密 IP 的网段切换。
- 12/12 存在 did 混用。
- 12/12 reset 侧 reported_phone_model = `Xiaomi(MI 8 Lite)`。
- 12/12 phoneModel 与真实硬件不一致或 Weapon 无设备画像。
- 12/12 在 2026-05-21 14:09 左右批量推被盗 / token 吊销。

## 3. 当前攻击模板命名

- attack_template_identified: true
- template_name: `华为鸿蒙 token/quickLogin → 8.136 网段 byToken/logined 改密 → 伪造 Xiaomi(MI 8 Lite)`

模板口径：

- 不要写成“小米设备改密”。
- 正确口径是：改密侧统一上报 `Xiaomi(MI 8 Lite)`，但真实硬件不一致或 Weapon 无设备画像。
- `Xiaomi(MI 8 Lite)` 是 reported_phone_model，不是可信硬件画像。

## 4. 当前 TOP cases

| case_id | top_reason | evidence_boundary |
|---|---|---|
| ato_003 | 改密后 50+ 次 `changeOption` 操控 | TOP case 只代表已观察 12 case 中最强行为操控样本之一 |
| ato_007 | 风控踢登录态后攻击者继续 iOS token 接管 | token 不输出明文，只记录链路摘要 |
| ato_008 | 改密后伪造 Nokia X6 修改私信设置 | 后续操控行为需要继续在剩余 case 中验证 |
| ato_010 | 改密后 3 个不同设备/IP 试图接管 | IP 只保留脱敏网段，不输出完整 IP |

## 5. Evidence Quality

- interim_evidence_quality: `high`
- reason:
  - 12/12 完整闭环。
  - 12/12 IP 切换。
  - 12/12 did 混用。
  - 12/12 phoneModel 与真实硬件不一致或 Weapon 无设备画像。
  - 12/12 有批量推被盗 / token 吊销。

## 6. ATO Support Level

- interim_ato_batch_support_level: `strong`
- scope: `ato_001_to_ato_012`
- boundary:
  - strong 只针对已完成的 12 case。
  - 不推断剩余 8 个已成立。
  - 不输出处置结论。
  - 不自动上线策略。

## 7. 是否建议继续扩 ato_013~ato_020

- should_continue_to_ato_013_020: true
- reason: 第一批 5/5 和第二批 7/7 均复现攻击模板，累计 12/12 支持继续扩量。
- next_scope: `ato_013_to_ato_020`

## 8. 下一步观察重点

继续扩 ato_013~ato_020 时，重点观察：

1. 是否仍 8/8 完整 login → reset 闭环。
2. 是否仍出现登录 IP 到改密 IP 网段切换。
3. 是否仍出现 did 混用。
4. 是否仍统一 reported_phone_model = `Xiaomi(MI 8 Lite)`。
5. 是否仍出现真实硬件不一致或 Weapon 无设备画像。
6. 是否仍在 05-21 14:09 左右出现批量推被盗 / token 吊销。
7. 是否存在 ato_003 / ato_007 / ato_008 / ato_010 类后续操控 TOP case。

## 9. 禁止扩展结论

禁止输出：

- “剩余 8 个也已经成立。”
- “20/20 已确认。”
- “所有都是小米设备改密。”
- “reset_login_type=99 必然盗号。”
- “可以直接处置。”
- “可以直接上线策略。”

允许输出：

- “12/12 已完成样本支持继续扩量。”
- “当前攻击模板在 12 case 中高度稳定。”
- “剩余 8 case 需要继续只读 observation 验证。”
