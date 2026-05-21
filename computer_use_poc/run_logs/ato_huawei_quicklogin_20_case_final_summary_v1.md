# ATO Huawei QuickLogin 20-case Final Summary v1

## 1. 20 case 总体结论

- sample_set_id: `ato_huawei_quicklogin_xiaomi_reset_20260520`
- summary_type: `final_summary_for_sample_set`
- completed_cases: `ato_001_to_ato_020`
- completed_count: 20
- readonly_only: true
- dataagent_called: false
- platform_write_action: false
- release_package_updated: false
- auto_disposition: false
- auto_strategy_launch: false

结论：本 sample_set 内 20/20 case 均形成完整 ATO 闭环，攻击模板高度稳定。

边界：该结论只覆盖本次 20 个已观察 case，不推导到其他未查样本，不构成自动处置或自动上线依据。

## 2. 20 case 关键发现

- 20/20 完整 login → reset 闭环。
- 20/20 登录 IP `183.206.xxx.xxx` → 改密 IP `8.136.xxx.xxx`。
- 20/20 did 混用。
- 20/20 reported_phone_model = `Xiaomi(MI 8 Lite)` 或同类 Xiaomi 伪造参数。
- 20/20 phoneModel 与真实硬件不一致或 Weapon 无设备画像。
- 20/20 在 2026-05-21 14:09 左右批量推被盗 / token 吊销。

## 3. 最终攻击模板名

- attack_template_identified: true
- final_template_name: `华为鸿蒙 token/quickLogin → 8.136 网段 byToken/logined 改密 → 伪造 Xiaomi(MI 8 Lite)`

模板口径：

- 不要写成“小米设备改密”。
- 正确口径是：改密侧统一上报 `Xiaomi(MI 8 Lite)` 或同类 Xiaomi 伪造参数，但真实硬件不一致或 Weapon 无设备画像。
- `Xiaomi(MI 8 Lite)` 是 reported_phone_model / fake phone model，不是可信硬件画像。

## 4. 最终 TOP cases

| case_id | top_reason | evidence_boundary |
|---|---|---|
| ato_003 | 改密后 50+ 次 `changeOption` 操控 | 支持 post-reset 操控链路 |
| ato_007 | 风控踢登录态后攻击者继续 iOS token 接管 | 说明攻击者持续争夺登录态 |
| ato_010 | 改密后 3 个不同设备/IP 试图接管 | 支持多设备/IP 接管尝试 |
| ato_014 | 多次 ATO / 多次改密 | 支持重复控制权争夺 |
| ato_016 | 伪造模板升级，从真实 Redmi 到统一 Xiaomi 伪造模板 | 支持 reported_phone_model 模板演进 |
| ato_019 | 攻防对抗最激烈，5+ 设备/IP 接管，风控密集踢登录态 | 支持强对抗样本 |

## 5. 攻击模板稳定特征

| feature | observed |
|---|---|
| p_date | 20260520 |
| initial path | huawei quickLogin 或 login/token |
| reset_path | `/rest/n/user/reset/byToken/logined` |
| reset_login_type | 99 |
| login_ip_cluster | `183.206.xxx.xxx` |
| reset_ip_cluster | `8.136.xxx.xxx` |
| reported_phone_model | `Xiaomi(MI 8 Lite)` 或同类 Xiaomi 伪造参数 |
| did pattern | HARMONY did + ANDROID/iOS did 混用 |
| hardware consistency | phoneModel 与 Weapon 硬件画像不一致或 Weapon 无数据 |
| post events | CreatePassword / UserBitDbWriteRpc / token revoke / stolen mark |
| post-reset behavior | changeOption / 私信设置修改 / 多设备接管 |

## 6. 可转策略评估方向

以下仅为策略评估候选，不是自动上线结论：

1. byToken/logined 改密前短时间华为/Harmony 登录。
2. 登录 IP 与改密 IP 短时间跨网段切换。
3. reset 侧上报 Xiaomi(MI 8 Lite) 但硬件画像不一致。
4. HARMONY did 与 ANDROID/iOS did 混用。
5. reset 侧设备多用户关联 / 封禁 / 异常状态。
6. 改密后 changeOption / 私信设置修改 / 多设备接管。

策略评估边界：

- 需要人工审核。
- 需要灰度验证。
- 需要误伤评估。
- 需要查杀分离。
- 不能由该 summary 直接转处置。

## 7. 可转 DataAgent / Hive 扩量查询问题

以下是候选离线取数问题，不代表本轮已调用 DataAgent：

1. 在 `p_date=20260520` 上，查询 `reset_path=/rest/n/user/reset/byToken/logined` 且 reset_ip like `8.136%` 的用户规模。
2. 查询这些用户在 reset 前 10 分钟是否存在 HUAWEI/HARMONY quickLogin 或 login/token。
3. 查询 reset phoneModel 是否集中为 `Xiaomi(MI 8 Lite)`。
4. 查询登录 IP 是否集中在 `183.206%`。
5. 查询是否存在同日 05-21 14:09 批量 token revoke / stolen mark。
6. 查询是否有 changeOption / 私信设置修改等 post-reset 操控行为。

DataAgent / Hive 边界：

- DataAgent 只作为 Hive / 数仓取数分析能力。
- 本轮未调用 DataAgent。
- 上述问题需要单独授权、审计和脱敏输出。

## 8. 处置与输出边界

- 不做自动处置。
- 不直接输出封禁结论。
- 处置建议只作为策略评估候选。
- 需要人工审核 / 灰度验证 / 误伤评估。
- 不输出完整 IP、cookie、token、session、header。
- IP 只保留脱敏网段，例如 `183.206.xxx.xxx`、`8.136.xxx.xxx`。
- 不推导到本 sample_set 以外的未查样本。

## 9. Final Assessment

- final_sample_set_evidence_quality: `high`
- final_sample_set_ato_support_level: `strong`
- full_20_cases_confirmed: true
- attack_template_stability: `high_within_sample_set`
- next_stage: `strategy_evaluation_candidate_and_hive_scale_query_design`
- no_release_update: true
- no_platform_write: true
- no_dataagent_call: true
