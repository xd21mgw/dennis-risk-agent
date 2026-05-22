# ATO Huawei QuickLogin 20-case Closure Summary v1

## 1. 样本集背景

- sample_set_id: `ato_huawei_quicklogin_xiaomi_reset_20260520`
- sample_set_type: `ato`
- closure_type: `batch_ato_analysis_closure_summary`
- case_scope: `ato_001_to_ato_020`
- total_cases: 20
- readonly_only: true
- dataagent_called: false
- platform_write_action: false
- release_package_updated: false

该样本集围绕一条明确的 ATO 假设展开：

`HUAWEI / Harmony quickLogin 或 token 登录 → login_type=16 → byToken/logined 改密 → reset_login_type=99 → 改密侧上报 Xiaomi(MI 8 Lite)`

本 closure summary 只总结该 20 case 样本集内的 observation 闭环，不推导到其他未查样本，不构成自动处置或自动策略上线依据。

## 2. 执行路径

| stage | artifact | purpose | result |
|---|---|---|---|
| case table | `computer_use_poc/case_sets/ato_huawei_quicklogin_xiaomi_reset_20260520_case_table.md` | 固化 20 个 ATO 样本台账和初始假设 | 20 个 case 均进入 `pending_observation` |
| single case | `computer_use_poc/run_logs/ato_huawei_quicklogin_case_ato_001_observation_run_001.md` | 先跑通 ato_001 单 case 链路，验证字段口径 | 单 case 支持 ATO 链路，暴露 reported/hardware model 口径差异 |
| 5 case batch | `computer_use_poc/run_logs/ato_huawei_quicklogin_5_case_batch_observation_run_001.md` | 扩到 ato_001~ato_005，验证攻击模板是否可复现 | 5/5 复现完整 login → reset 闭环 |
| 12 case interim | `computer_use_poc/run_logs/ato_huawei_quicklogin_12_case_interim_summary_v1.md` | 汇总 ato_001~ato_012 中期进展 | 12/12 复现完整 ATO 闭环 |
| 20 case final | `computer_use_poc/run_logs/ato_huawei_quicklogin_20_case_final_summary_v1.md` | 汇总 ato_001~ato_020 最终样本集结论 | 20/20 形成完整 ATO 闭环 |

## 3. 最终攻击模板

- attack_template_identified: true
- final_template_name: `华为鸿蒙 token/quickLogin → 8.136 网段 byToken/logined 改密 → 伪造 Xiaomi(MI 8 Lite)`

模板口径：

- `Xiaomi(MI 8 Lite)` 是改密侧 reported_phone_model / fake phone model，不是可信硬件画像。
- 不要写成“小米设备改密”。
- 正确表达是：改密侧统一上报 `Xiaomi(MI 8 Lite)` 或同类 Xiaomi 伪造参数，但真实硬件不一致或 Weapon 无设备画像。

## 4. 最终证据链

| evidence_item | observed_count | evidence_meaning | boundary |
|---|---:|---|---|
| login → reset 闭环 | 20/20 | 支持同一类 ATO 链路复现 | 仅覆盖本 sample_set |
| IP 切换 | 20/20 | 登录 IP `183.206.xxx.xxx` → 改密 IP `8.136.xxx.xxx` | 只保留脱敏网段 |
| did 混用 | 20/20 | HARMONY did 与 ANDROID/iOS did 混用 | 需要结合登录和改密链路解释 |
| Xiaomi(MI 8 Lite) 上报 | 20/20 | 改密侧统一上报 Xiaomi 或同类伪造参数 | 不是硬件真实型号 |
| 真实硬件不一致或 Weapon 无数据 | 20/20 | 支持 protocol forged device / reported model mismatch | Weapon 无数据不能单独解释为无设备 |
| 批量推被盗 / token 吊销 | 20/20 | 支持后续风控识别与被盗链路处理 | 不等于自动处置依据 |

## 5. TOP Cases

| case_id | why_top_case | evidence_value |
|---|---|---|
| ato_003 | 改密后 50+ 次 `changeOption` 操控 | 最强 post-reset 操控样本 |
| ato_007 | 风控踢登录态后攻击者继续 iOS token 接管 | 展示攻防对抗和登录态争夺 |
| ato_010 | 改密后 3 个不同设备/IP 试图接管 | 展示多设备/IP 接管尝试 |
| ato_014 | 多次 ATO / 多次改密 | 展示重复控制权争夺 |
| ato_016 | 伪造模板升级，从真实 Redmi 到统一 Xiaomi 伪造模板 | 展示 reported_phone_model 模板演进 |
| ato_019 | 攻防对抗最激烈，5+ 设备/IP 接管，风控密集踢登录态 | 展示强对抗与持续接管尝试 |

## 6. 本轮方法论沉淀

本次 ATO 主线形成了一个可复用的 Dennis Agent 批量 ATO 分析样板：

1. 单 case 先跑通：先用 `ato_001` 验证登录、改密、设备、风控后续事件是否能形成闭环。
2. 用真实 observation 修模板：发现 `reported_phone_model` 与 `hardware_reported_model` 必须分开，避免误把上报机型当真实硬件。
3. 再扩 5 个：验证攻击模板在小批量中是否稳定复现。
4. 再扩 12 个：做中期总结，识别 TOP case 和新增异常形态。
5. 最后扩 20 个：确认本 sample_set 内攻击模板 20/20 复现。
6. Codex 负责落盘和模板修正：不直接调用平台，不替代内部 observation 执行层。
7. 内部 Dennis 子 Agent 负责真实只读观察：读取真实平台 observation，并将脱敏摘要返回给 Codex 落盘。

关键经验：

- 先不要直接全量总结，必须先跑通单 case。
- 批量分析不能只看字段相似，要形成 login → reset → post-reset control → wind-control follow-up 的证据链。
- 后置行为是补证，不是 ATO 本质；ATO 主线仍是账号控制权异常。
- reported device 与真实硬件画像必须分开，否则容易把协议伪造误读成真实设备迁移。

## 7. 可转化方向

### 7.1 DataAgent / Hive 扩量查询问题

以下是候选离线取数问题，不代表本轮已调用 DataAgent：

1. 在 `p_date=20260520` 上，查询 `reset_path=/rest/n/user/reset/byToken/logined` 且 reset_ip like `8.136%` 的用户规模。
2. 查询这些用户在 reset 前 10 分钟是否存在 HUAWEI/HARMONY quickLogin 或 login/token。
3. 查询 reset 侧 reported_phone_model 是否集中为 `Xiaomi(MI 8 Lite)` 或同类 Xiaomi 参数。
4. 查询登录 IP 是否集中在 `183.206%`。
5. 查询是否存在 2026-05-21 14:09 左右批量 token revoke / stolen mark。
6. 查询是否存在改密后 `changeOption`、私信设置修改、多设备接管等 post-reset 操控行为。

DataAgent / Hive 边界：

- DataAgent 只作为 Hive / 数仓取数分析能力。
- 本轮未调用 DataAgent。
- 扩量查询需要单独授权、审计和脱敏输出。

### 7.2 策略评估候选规则卡

以下只能作为策略评估候选，不是自动上线结论：

| rule_card | candidate_signal | risk_value | required_review |
|---|---|---|---|
| byToken/logined 前置登录卡 | 改密前短时间出现 HUAWEI/HARMONY quickLogin 或 login/token | 区分正常改密与异常登录态接管 | 误伤评估、时间窗口灰度 |
| IP 跨网段切换卡 | 登录 IP `183.206.xxx.xxx` → 改密 IP `8.136.xxx.xxx` | 支持远端接管或代理链路 | 网段稳定性、正常用户迁移反证 |
| 伪造机型卡 | reset reported Xiaomi，但硬件画像不一致或 Weapon 无数据 | 支持协议伪造设备 | 正常设备上报异常反证 |
| did 混用卡 | HARMONY did + ANDROID/iOS did 混用 | 支持跨端登录态复用或伪造 | did 采集缺口复核 |
| post-reset 操控卡 | 改密后 changeOption / 私信设置 / 多设备接管 | 支持账号控制权被夺取后的操控 | 用户本人改设置反证 |

### 7.3 Dennis Agent batch ATO workflow 样板

本样本集可作为后续 Dennis Agent 批量 ATO workflow 的参考：

- case table 固化样本输入。
- single-case observation 校正模板。
- batch observation 累计关键计数。
- interim summary 抽出 TOP case 和新增发现。
- final summary 固化攻击模板。
- closure summary 固化方法论和后续转化方向。

## 8. 边界

- 不自动处置。
- 不直接封禁。
- 不输出封禁结论。
- 不更新 release 包。
- 不调用真实平台。
- 不调用 DataAgent。
- 不推导到本 sample_set 以外的未查样本。
- 策略方向只作为候选，需要人工策略评审、灰度验证、误伤评估。
- 不输出完整 IP、cookie、token、session、header。
- IP 只保留脱敏网段，例如 `183.206.xxx.xxx`、`8.136.xxx.xxx`。

## 9. Closure Assessment

- closure_status: `completed_for_sample_set`
- batch_evidence_quality: `high`
- ato_batch_support_level: `strong`
- methodology_reusable: true
- ready_for_hive_scale_query_design: true
- ready_for_strategy_review_draft: true
- no_release_update: true
- no_platform_call_by_codex: true
- no_dataagent_call_by_codex: true
