# ATO Huawei QuickLogin Hive Expansion Questions v1

## 1. 查询目标

- sample_set_id: `ato_huawei_quicklogin_xiaomi_reset_20260520`
- source_summary: 20 case final summary + closure summary
- query_plan_type: `dataagent_hive_expansion_question_list`
- real_platform_called: false
- dataagent_called: false
- release_package_updated: false

目标是从 20 case 样本扩展到全量数据，确认该攻击模板的规模、时间分布、变体和误伤风险。

已完成的 20 case 样本攻击模板：

`华为鸿蒙 token/quickLogin → 8.136 网段 byToken/logined 改密 → 伪造 Xiaomi(MI 8 Lite)`

本文件只定义 DataAgent / Hive 取数问题和字段建议，不生成 SQL，不调用 DataAgent，不直接输出策略结论。

## 2. 核心扩量条件

建议先从严格条件开始，再逐层放宽观察变体。

### 2.1 严格复现条件

- `p_date = 20260520`
- `reset_path = /rest/n/user/reset/byToken/logined`
- `reset_login_type = 99`
- `reset_ip LIKE '8.136%'`
- `reset reported_phone_model = 'Xiaomi(MI 8 Lite)'`
- reset 前 10 分钟存在 HUAWEI/HARMONY quickLogin 或 login/token
- `login_ip LIKE '183.206%'`
- 存在 HARMONY did 与 ANDROID/iOS did 混用

### 2.2 变体观察条件

- reset_path 固定为 `/rest/n/user/reset/byToken/logined`，但 reset_ip 不限于 `8.136%`。
- reset_ip 固定为 `8.136%`，但 phoneModel 放宽到其他 Xiaomi 或异常上报机型。
- initial_login_path 放宽到其他 HUAWEI/HARMONY 登录链路。
- initial_to_reset_interval 从 10 分钟放宽到 30 分钟、60 分钟观察衰减。
- did_mixing_signal 缺失时保留为待复核，不直接排除。

## 3. 必问问题

1. 全量命中用户数是多少？
2. 命中是否集中在 `20260520`，还是前后多日都有？
3. `reset_ip = 8.136%` 网段下还有哪些 phoneModel 伪造模板？
4. 是否还有非 `Xiaomi(MI 8 Lite)` 的变体？
5. reset 前 10 分钟 HUAWEI/HARMONY 登录占比是多少？
6. login_ip 是否稳定聚集在 `183.206%` 网段？
7. HARMONY did 与 ANDROID/iOS did 混用比例是多少？
8. 命中用户后续是否集中出现 token revoke / stolen mark？
9. 是否存在 `changeOption` / 私信设置修改 / 多设备接管等 post-reset 行为？
10. 是否存在正常用户误伤特征？
11. initial_to_reset_interval 的分布是否集中在短时间窗口内？
12. reset 侧 reported_phone_model 与设备硬件画像不一致的比例是多少？
13. 是否存在同 reset did / 同 reset_ip / 同 reported_phone_model 关联多个用户的聚集？
14. 命中用户是否存在被盗申诉、风控踢登录态、CreatePassword 或 UserBitDbWriteRpc 等后续事件？

## 4. 分层统计建议

| dimension | purpose | suggested_output |
|---|---|---|
| 日期 | 判断攻击是否集中爆发或持续多日 | p_date, user_count, event_count |
| reset_ip 网段 | 判断改密出口是否聚集 | reset_ip_prefix, user_count, distinct_did_count |
| login_ip 网段 | 判断登录入口是否聚集 | login_ip_prefix, user_count, reset_match_count |
| reset_phone_model | 识别 reported_phone_model 伪造模板 | reset_phone_model, user_count, mismatch_rate |
| initial_login_path | 判断前置登录链路类型 | initial_login_path, user_count, ratio |
| initial_to_reset_interval | 判断登录到改密的时序强度 | interval_bucket, user_count |
| did_mixing_signal | 判断跨端 did 混用程度 | did_mixing=true/false, user_count |
| stolen_mark / token_revoke | 判断后续风控识别集中度 | signal_type, user_count, event_time_distribution |
| post-reset 行为 | 判断账号控制权被夺取后的操控行为 | behavior_type, user_count, event_count |
| hardware mismatch | 判断上报机型与真实硬件冲突 | mismatch_type, user_count, evidence_quality |

## 5. 输出字段建议

### 5.1 明细字段

- user_id
- first_login_time
- initial_login_path
- initial_phone_model
- initial_did
- initial_ip_masked
- reset_time
- reset_path
- reset_phone_model
- reset_did
- reset_ip_masked
- interval_seconds
- did_mixing_signal
- phone_model_mismatch_signal
- token_revoke_signal
- stolen_mark_signal
- post_reset_behavior_signal

### 5.2 聚合字段

- p_date
- user_count
- distinct_initial_did_count
- distinct_reset_did_count
- login_ip_prefix_count
- reset_ip_prefix_count
- reset_phone_model_distribution
- initial_login_path_distribution
- interval_bucket_distribution
- did_mixing_rate
- token_revoke_rate
- stolen_mark_rate
- post_reset_behavior_rate
- phone_model_mismatch_rate

## 6. 查询分层建议

### P0: 严格模板复现

目标：先确认与 20 case 完全一致的攻击模板规模。

条件组合：

- `p_date=20260520`
- `reset_path=/rest/n/user/reset/byToken/logined`
- `reset_login_type=99`
- `reset_ip LIKE '8.136%'`
- reset reported_phone_model = `Xiaomi(MI 8 Lite)`
- reset 前 10 分钟存在 HUAWEI/HARMONY quickLogin 或 login/token
- login_ip LIKE `183.206%`

输出：

- 命中用户数。
- 命中用户的 did_mixing_rate。
- token revoke / stolen mark 后续比例。
- post-reset 操控行为比例。

### P1: 模板变体扩展

目标：确认是否存在同一攻击链路的变体。

放宽项：

- phoneModel 放宽到其他 Xiaomi / Redmi / Nokia / iOS UUID 伪造参数。
- reset_ip 从 `8.136%` 扩展到同 ASN / 同云厂商 / 同地域出口。
- initial_to_reset_interval 放宽到 30 分钟或 60 分钟。

输出：

- 变体 phoneModel 分布。
- 变体 reset_ip 网段分布。
- 变体样本与严格模板的 overlap。

### P2: 误伤风险与反证

目标：识别正常用户可能命中的边界，避免策略过拟合。

反证方向：

- 用户历史长期稳定设备，且 reset 设备与历史设备一致。
- reset 前后 IP、did、phoneModel 无明显突变。
- 无 stolen mark / token revoke / 风控踢登录态。
- 无 post-reset changeOption / 私信设置 / 多设备接管。
- reset 行为与用户常用登录链路、常用设备、常用 IP 一致。

输出：

- 误伤候选用户数。
- 误伤候选的共性。
- 需要人工复核的边界样本。

## 7. DataAgent / Hive 交付建议

建议 DataAgent 输出两类结果：

1. 聚合表：用于判断规模、集中度、变体和误伤风险。
2. 脱敏样本表：用于 Dennis Agent 后续抽样观察和 evidence card 生成。

脱敏要求：

- IP 只输出网段或 masked 形式，如 `183.206.xxx.xxx`、`8.136.xxx.xxx`。
- user_id 可按内部合规要求输出引用 ID 或脱敏 ID。
- 不输出手机号、cookie、token、session、header、完整请求参数。
- 原始日志只保留安全引用，不进入普通分析文档。

## 8. 边界

- 这只是查询问题清单，不直接下策略结论。
- DataAgent 主要用于 Hive / 数仓取数分析，不要泛化为全能风控执行器。
- 不输出完整 IP、手机号、cookie、token、session、header。
- 需要脱敏和聚合展示。
- 命中该模板不等于自动封禁结论。
- 策略方向需要人工审核、灰度验证、误伤评估和查杀分离。
- 本文件未调用真实平台、未调用 DataAgent、未更新 release 包。
