# ATO Huawei QuickLogin / Xiaomi Reset Single-case Plan v1

## 1. Run Log Metadata

- run_log_id: `ato_huawei_quicklogin_single_case_plan_v1`
- sample_set_id: `ato_huawei_quicklogin_xiaomi_reset_20260520`
- run_type: `planning_only`
- readonly_only: true
- dataagent_called: false
- platform_query_executed: false
- platform_write_action: false
- release_package_updated: false

## 2. Current Hypothesis

待验证链路：

HUAWEI / Harmony quickLogin 或 token 登录  
→ `login_type=16`  
→ Xiaomi(MI 8 Lite)  
→ `/rest/n/user/reset/byToken/logined`  
→ `reset_login_type=99`

该链路当前只是 ATO 假设，不是事实结论。

## 3. Why Start From Single Case

先从单 case 跑起的原因：

1. 验证 observation template 是否能表达完整链路。
2. 验证 initial login 与 reset event 的字段是否足够区分。
3. 避免 20 个 case 同时进入观察时，把字段缺口误当成模式结论。
4. 先发现路径、login_type、reset_login_type、device model 字段是否存在解释歧义。
5. 降低隐私和安全风险，避免未验证前批量扩散。

单 case 需要回答：

- 是否真实观察到 HUAWEI / Harmony quickLogin 或 token 登录。
- 是否真实观察到 `login_type=16`。
- 是否真实观察到 Xiaomi(MI 8 Lite) reset event。
- 是否真实观察到 `/rest/n/user/reset/byToken/logined`。
- 是否真实观察到 `reset_login_type=99`。
- initial login 与 reset event 是否能在时间、用户、token/session、device 关系上连接。
- 是否存在正常找回流程或本人操作反证。

## 4. Then Expand To 5 Cases

单 case template 可用后，再扩到 5 个 case。

5 case 目标：

- 验证字段是否在不同 case 中稳定出现。
- 检查 `login_type=16` 与 `reset_login_type=99` 是否一致。
- 检查 HUAWEI / Harmony → Xiaomi(MI 8 Lite) 是否是重复链路，还是单 case 偶然现象。
- 初步识别 missing evidence 是否共性化。
- 评估 observation 成本和人工 review 成本。

5 case 仍不能输出全量结论：

- 只能输出 partial pattern summary。
- 只能给候选 ATO chain support。
- 不做自动处置。
- 不做策略上线建议。

## 5. Then Expand To Full 20 Cases

满足以下条件后再扩到 20 个 case：

- 单 case observation template 已验证可用。
- 5 case 中字段稳定性可接受。
- 未发现关键字段解释冲突。
- 未出现明显隐私、权限或脱敏问题。
- 已明确 no_data / missing / permission_blocked 的解释规则。

20 case 目标：

- 聚合链路复现率。
- 聚合 missing evidence。
- 区分 strong_support / partial_support / insufficient_support / counter_evidence_present。
- 识别是否存在共性 ATO 链路。
- 输出候选补证方向，而不是自动策略。

## 6. Evidence Boundary

禁止表达：

- “HUAWEI 到 Xiaomi 就是盗号。”
- “login_type=16 必然异常。”
- “reset_login_type=99 必然异常。”
- “20 个 user_id 都确认 ATO。”
- “可以直接上线拦截。”

允许表达：

- “当前样本集存在一条待验证的 ATO 候选链路。”
- “需要先从单 case 验证 initial login 与 reset event 是否真实存在。”
- “只有当登录态 / token / session / device 关系能连接时，才支持 ATO 链路。”
- “如果存在正常找回流程或本人常用设备反证，需要降级。”

## 7. Next Step

建议下一步：

1. 从 ATO 样本台账中选择 1 个 case。
2. 选 1 个 case 使用 `ato_single_case_observation_template.yaml` 做只读 observation。
3. 如果字段完整，再抽 5 个 case。
4. 如果 5 个 case 结果稳定，再扩到 20 个。
5. 全程不调用 DataAgent，不做写操作，不自动上线策略。
