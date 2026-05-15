# Protocol Attack Real DataAgent Read-only Pilot Runbook v1

## 0. 边界声明

本文件用于 v2.4 真实 Data Agent 只读试点准备。

- 当前阶段不调用真实 Data Agent。
- 当前阶段不定义真实 API、真实表名、真实字段名、真实 SQL。
- 当前阶段只验证 Dennis Agent 生成的 `query_intent_schema_v2` 能否被内部平台转换、执行、解释和回放。
- 本试点只做补证和研判，不做自动处罚、冻结、扣除、策略上线或自动治理。

## 1. 试点目标

验证协议攻击补证链路是否可以从 Dennis Agent 的风险问题出发，经由 `query_intent_schema_v2`、Data Agent adapter、Data Agent 只读查询结果，最终形成 Dennis Agent 可解释的 `normalized_evidence`。

核心问题：

前端无日志、后端有请求时，是否支持协议攻击判断。

必须同时排除：

- 破解包绕 SDK / 绕采集。
- 官方包埋点缺失。
- 前后端 join 口径问题。
- 合法自动化 / 授权工具。
- 群控真机。

## 2. 只读边界

试点允许：

- 生成 `query_intent_schema_v2`。
- 由内部平台把 query intent 转成只读 dataagent request。
- 接收 Data Agent 的只读结果摘要。
- 标准化为 `normalized_evidence`。
- 输出证据强度、反证、缺口、结论等级和下一步补证建议。
- 记录审计与回放材料。

试点禁止：

- 自动处罚、冻结、扣除、限权、封禁。
- 自动上线策略或调整线上规则。
- 输出可直接复用的真实 SQL、真实 API、真实表名、真实字段名。
- 因前端无日志直接判协议攻击。
- 因 Data Agent 返回空结果直接判无风险。
- 因策略命中直接当作风险事实。

## 3. 适用问题

- 是否协议攻击。
- 是否前后端链路不一致。
- 是否 SDK 缺失 / 绕采集。
- 是否 token / device / ip / ua 冲突。
- 是否接口序列固化。
- 是否需要从协议攻击转交破解包、群控或合法矩阵判断。

## 4. 不适用问题

- 需要直接处置线上账号、设备、商家、达人或机构。
- 只有业务指标波动，缺少接口、端侧、设备、账号输入。
- 主要问题是站外导流、直播间截流、私信骚扰。
- 主要问题是活动低质、渠道归因、DAU/DNU 指标异常。
- 需要访问 HRBI 或其他明确不支持的数据域。
- 用户要求绕过权限、导出敏感明细或自动圈选处置人群。

## 5. 输入信息

最小输入：

- `user_id` 或 `device_id`。
- `api_name` 或业务动作。
- `time_window`。

可选输入：

- `app_version`。
- `channel`。
- `token_id`。
- `risk_event_id`。
- 业务场景。
- 触发策略或告警来源。
- 是否存在商家 / 达人 / MCN / 机构运营可能。

输入不足时：

- 不生成强结论。
- 先输出缺失输入清单。
- 只生成可执行的第一轮补证 query intent。

## 6. 首批 3 个真实 Case

### RP-AC-001：前端无日志 + 后端有请求

目标：

- 验证前端行为域与后端数据域能否完成链路一致性补证。
- 排除前端埋点缺失、join 口径问题、破解包绕采集。

关键问题：

- 后端请求是否真实存在。
- 对应时间窗内是否存在前端事件。
- 是否存在 SDK 日志覆盖。
- 前后端 join key 和时间窗是否一致。
- 官方版本是否也存在相同前端缺失。

### RP-AC-002：后端请求存在 + SDK 缺失

目标：

- 验证 SDK 缺失是否更接近破解包、采集异常、官方版本问题或协议攻击。

关键问题：

- SDK 缺失是否集中在特定 app version / channel / app signature 类型。
- 实时指纹是否存在。
- 设备画像是否异常。
- 官方包同版本是否存在相同缺失。
- 是否存在端侧行为但 SDK 不完整。

### RP-AC-003：接口高频 + token/device/ip/ua 异常

目标：

- 验证高频接口调用叠加 token / device / ip / ua 冲突时，是否支持协议攻击高度疑似或明确判断。

关键问题：

- 高频是否超过业务正常上限。
- token 与 device / ip / ua 是否出现不一致或跨环境复用。
- 接口序列是否固化。
- 是否存在合法自动化或授权工具反证。
- 是否存在群控真机统一调度反证。

## 7. query_intent 生成流程

1. Dennis Agent 识别主控 Skill：`protocol_attack_expert_skill`。
2. 识别辅助 Skill：
   - `cracked_app_expert_skill`：排除破解包绕 SDK。
   - `group_control_expert_skill`：排除群控真机。
   - `legal_operation_matrix_playbook_v2_3`：排除合法自动化 / 授权工具。
   - `account_security_expert_skill`：排查 token 复用或登录态异常。
3. 生成 `query_intent_schema_v2`，必须包含：
   - `intent_id`
   - `risk_question`
   - `target_evidence`
   - `applicable_skill`
   - `minimum_inputs`
   - `required_data_domains`
   - `optional_data_domains`
   - `field_types_needed`
   - `join_paths_needed`
   - `query_dimensions`
   - `time_window`
   - `expected_outputs`
   - `interpretation_notes`
   - `conclusion_threshold`
   - `quality_checks`
   - `freshness_expectation`
   - `permission_boundary`
   - `manual_review_required`
   - `safety_boundary`
   - `next_query_intent_when_insufficient`

## 8. dataagent_request 生成流程

内部平台 adapter 将 `query_intent_schema_v2` 转换为未来 Data Agent 只读请求。

转换原则：

- `risk_question` 转为自然语言问题。
- `target_evidence` 转为取证目标。
- `required_data_domains` 转为数据域约束。
- `field_types_needed` 只保留抽象字段类型。
- `join_paths_needed` 只保留抽象 join path。
- `quality_checks`、`freshness_expectation`、`permission_boundary`、`safety_boundary` 原样传递。
- 不生成真实 API、真实 SQL、真实表名、真实字段名。

推荐 task type：

- `data_query`
- `table_search`
- `table_summary`
- `permission_or_lineage_check`

## 9. dataagent_response 接收流程

内部平台接收 Data Agent 返回后，只把可审计摘要交给 Dennis Agent。

允许状态：

- `success`
- `partial`
- `failed`
- `no_permission`
- `timeout`
- `empty_result`
- `ambiguous_result`
- `data_quality_risk`
- `permission_limited`

接收要求：

- 返回 SQL 不等于已经查到结果。
- 返回空结果不等于无风险。
- 返回策略命中不等于风险事实。
- 返回风险画像不等于事实标签。
- `partial`、`no_permission`、`timeout`、`empty_result`、`ambiguous_result` 必须触发降级或补证。

## 10. normalized_evidence 生成流程

adapter 将 dataagent response 标准化为 `normalized_evidence`。

必须输出：

- 证据摘要。
- 关键发现。
- 强证据。
- 中证据。
- 弱证据。
- 反证。
- 缺失证据。
- 质量风险。
- 时效说明。
- 权限说明。
- 结论支持等级。
- 下一步 query intent。
- 是否需要人工确认。
- 内部 raw result reference。

约束：

- `normalized_evidence` 只能表达证据支持程度。
- `normalized_evidence` 不替代 Dennis Agent 最终判断。
- 缺失关键反证时，不得给“明确协议”。
- raw result reference 只做内部引用，不外泄敏感明细。

## 11. Dennis Agent 解释流程

Dennis Agent 基于 `normalized_evidence` 做解释：

1. 判断证据链是否完整。
2. 将证据拆成强 / 中 / 弱。
3. 明确反证是否闭合。
4. 判断是否存在质量风险或权限限制。
5. 输出四档结论等级。
6. 给出下一步补证动作。
7. 给出只读阶段可执行的治理建议，不触发自动处置。

解释重点：

- 前端无日志不是协议攻击的充分条件。
- SDK 缺失不是破解包的充分条件。
- 高频访问不是群控或协议的充分条件。
- 接口化调用不是协议攻击的充分条件。
- 合法矩阵不代表无风险，只代表应先做授权和范围判断。

## 12. 四档结论等级

### 明确协议

条件：

- 后端请求存在且前端链路长期缺失。
- SDK / 指纹 / 设备上下文缺失或冲突。
- token / device / ip / ua 存在不可解释冲突。
- 接口序列固化。
- 已排除破解包、官方埋点缺失、join 口径问题、合法自动化、群控真机。

### 高度疑似协议

条件：

- 多项协议证据成立。
- 仍有关键反证未完全闭合。
- 可进入策略灰度、监控和人工复核，不直接重处置。

### 证据不足

条件：

- 只有前端缺失、后端请求或单点高频。
- Data Agent 返回 `partial`、`no_permission`、`timeout`、`empty_result` 或关键 join 不完整。
- 缺少破解包、埋点缺失、合法自动化、群控真机等反证排除。

### 反向排除 / 转其他 Skill

条件：

- 官方包同版本也缺前端日志，优先转埋点 / 口径问题。
- 包签名 / SDK / 版本异常更明显，转破解包。
- 端侧行为存在且统一调度明显，转群控。
- 授权主体、工具来源、账号范围、操作人、收益主体闭合，转合法矩阵。

## 13. 人工确认边界

必须人工确认：

- 策略上线。
- 处罚、冻结、扣除、限权、封禁。
- 大规模灰度扩大。
- 跨业务线处置。
- 影响商家 / 达人 / MCN / 机构运营的处置。
- 数据权限受限但仍需要业务判断的 case。

不需要人工确认即可记录：

- query intent。
- dataagent request 摘要。
- normalized evidence。
- 证据不足结论。
- 下一步补证建议。

## 14. 审计与回放要求

每个试点 case 必须记录：

- 原始用户问题。
- Skill 路由。
- query intent。
- dataagent request 摘要。
- dataagent response 摘要。
- normalized evidence。
- Dennis Agent 结论。
- 人工最终判断。
- 是否一致。
- 不一致原因。
- 是否需要回写 query intent schema / join path / conclusion threshold / normalized evidence schema / Skill。
- 权限和质量风险记录。
- 是否触发人工确认。

## 15. 试点成功标准

单 case 成功标准：

- 能生成完整 `query_intent_schema_v2`。
- 能生成只读 dataagent request。
- 能接收并解析 dataagent response。
- 能生成完整 `normalized_evidence`。
- 能解释强 / 中 / 弱证据、反证、缺口和质量风险。
- 能输出四档结论等级。
- `partial`、`no_permission`、`empty_result` 能正确降级。
- 不因前端无日志直接判协议。

批次成功标准：

- 首批 3 个 case 均可完成闭环或明确失败原因。
- 人工复核能确认 Dennis Agent 是否过度自信或过度保守。
- 产出可回写的 schema / join path / threshold / Skill 改进点。
- 无自动处罚、冻结、扣除或策略上线行为。

## 16. 试点失败 / 降级标准

必须降级为“证据不足”：

- `dataagent_response` 为 `partial`、`failed`、`no_permission`、`timeout`。
- 返回为空且无法确认查询覆盖范围。
- 前后端 join key 或时间窗不一致。
- SDK 日志存在采集延迟或版本差异但未排除。
- 缺少合法自动化 / 授权工具反证。
- 缺少破解包或官方埋点缺失排查。
- 缺少群控真机排查。

必须暂停试点：

- adapter 无法保留审计链路。
- normalized evidence 无法表达反证和缺失证据。
- Data Agent 返回结果无法区分查询失败、权限不足、空结果和质量风险。
- 人工复核发现 Dennis Agent 连续过度自信。

## 17. 启动 Checklist

- [ ] 当前 case 已脱敏或符合内部只读试点要求。
- [ ] 输入包含 user_id 或 device_id。
- [ ] 输入包含 api_name 或业务动作。
- [ ] 输入包含 time_window。
- [ ] 已选择主控 Skill 和辅助 Skill。
- [ ] query intent 包含反证补证路径。
- [ ] dataagent request 不包含真实 API、真实 SQL、真实表名、真实字段名。
- [ ] normalized evidence 可以表达强 / 中 / 弱证据、反证、缺失证据、质量风险。
- [ ] 人工确认边界已明确。
- [ ] 审计与回放记录已准备。
