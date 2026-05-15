# DataAgent Parser Calibration - Complex Full-spec Examples

## 0. 校准边界

本文件基于 3 个 complex full-spec 模拟样例做 parser 增量校准：

- 样例 7：complex success full spec
- 样例 8：complex partial full spec
- 样例 9：complex no_permission full spec

这些样例只用于 parser 规则校准，不代表真实 Data Agent 查询结果。不调用真实 Data Agent，不编造真实 API、真实表名、真实字段名、真实 SQL。

## 1. 样例 7：complex success full spec

### parser 应识别的 status

`success`

### returned_type

`complex_table + full_spec_analysis`

### key_findings

- 多数据域联合取证返回了后端请求、前端行为、设备 / SDK / 指纹、策略引擎、用户信息、风险画像等数据摘要。
- 存在“前端无匹配 + 后端有请求”的异常链路线索。
- 设备 / SDK / 指纹域存在破解包或 SDK 异常强线索。
- 策略引擎存在 BLOCK / CHALLENGE / MONITOR 不同处置记录。
- 关联网络域或合法矩阵授权域仍存在缺口或部分未覆盖。

### strong_evidence

- 破解包绕 SDK / 绕采集路径如有明确设备指纹、SDK 缺失、包类型异常和请求链路一致支持，可进入 strong_evidence。
- 前后端链路在明确 join 口径下持续不一致，可进入 strong_evidence。

### medium_evidence

- 策略引擎 `BLOCK`：较强处置证据，但策略命中不等于风险事实。
- 策略引擎 `CHALLENGE`：中等风险 / 验证证据。
- 风险画像或用户风险标签：辅助证据，不等于事实标签。

### weak_evidence

- 策略引擎 `MONITOR`：观察证据，不能作为强打击证据。
- Data Agent 的“高度疑似协议攻击”等结论性文字：只能进入 provider_conclusion_hint。
- 模型推测和未验证假设。

### counter_evidence

- 官方包埋点缺失。
- 前后端 join 口径问题。
- 合法自动化 / 授权工具。
- 群控真机。
- 破解包指纹误判或旧版本 SDK 采集差异。

### missing_evidence

- 若关联网络域未完整覆盖：群控真机排查缺口。
- 若合法矩阵授权域未完整覆盖：授权工具白名单缺口。
- 若精确 join 口径仍待验证：口径缺口。
- 若实时日志 / 实时指纹未接入：Data Agent-only 实时补证缺口。

### quality_risks

- complex success 不等于最终明确判断。
- Data Agent-only 是离线 / 数据平台证据，不等于实时链路闭合。
- 策略命中不等于风险事实。
- 反证排除状态若存在 P0 未排除，结论上限受限。

### provider_limitations

- `dataagent_markdown_not_structured`
- `dataagent_offline_not_realtime`
- `missing_realtime_log_provider`
- `missing_device_fingerprint_provider`，如实时指纹未接入
- `missing_relation_graph_provider`，如关系图未覆盖
- `missing_manual_review_provider`，如授权白名单需要人工确认

### conclusion_support.level

`highly_suspicious_support`

### conclusion_support.reason

即使 success 样例有多域数据和强线索，只要 P0 关键反证仍有未排除 / 部分排除 / 待验证，Data Agent-only 阶段不得升级为明确判断。

### recommended_next_provider

由 Router / Dennis Agent 生成，常见为：

- `realtime_log_provider`
- `device_fingerprint_provider`
- `risk_engine_provider`
- `relation_graph_provider`
- `manual_review_provider`

### manual_review_required

true。P0 反证或授权边界未完全闭合时必须人工复核。

### raw_result_reference 使用方式

`queryId + sessionId + 本地保存路径或内部引用`，弱引用，不作为可回放证据。

### 是否符合 Data Agent-only 结论上限

符合。complex success 只到高度疑似，不自动明确判断。

## 2. 样例 8：complex partial full spec

### parser 应识别的 status

`partial`

### returned_type

`complex_partial_table + analysis`

### key_findings

- 后端请求域可查，目标接口存在请求聚集。
- 设备 / SDK / 指纹域可查，存在 SDK 缺失、低版本或指纹异常线索。
- 前端行为域仅部分覆盖或只有离线聚合口径。
- 策略引擎域、关联网络域、授权运营域存在未覆盖。

### strong_evidence

通常为空；如局部破解包路径有明确设备 / SDK 数据，可作为局部 strong_evidence，但不能代表整体。

### medium_evidence

- 后端请求聚集。
- SDK 缺失 / 指纹异常线索。

### weak_evidence

- 前端无日志仅有离线聚合口径。
- Data Agent 的“局部高度疑似”文字，只能是 provider_conclusion_hint。

### counter_evidence

- 官方包埋点缺失。
- join 口径偏差。
- 合法自动化 / 授权工具。
- 群控真机。
- 采集延迟或版本差异。

### missing_evidence

- 实时前端日志。
- NG 网关明细。
- 策略引擎命中。
- 群控标签 / 关系网络。
- 授权运营白名单。
- 样本工件或实时指纹。

### quality_risks

- 前端离线聚合不等于实时无日志。
- SDK 缺失原因未闭合。
- 关键反证路径未覆盖。
- Data Agent-only 缺实时 provider。

### provider_limitations

- `dataagent_offline_not_realtime`
- `missing_realtime_log_provider`
- `missing_risk_engine_provider`
- `missing_relation_graph_provider`
- `missing_manual_review_provider`

### conclusion_support.level

局部：`highly_suspicious_support`  
整体：`insufficient_support`

### conclusion_support.reason

可查域产生的数据发现支持局部协议 / 破解包疑点；但前端、策略、关系、授权等关键域缺失，整体证据不足。

### recommended_next_provider

由 Router / Dennis Agent 生成：

- `realtime_log_provider`
- `device_fingerprint_provider`
- `risk_engine_provider`
- `relation_graph_provider`
- `manual_review_provider`

### manual_review_required

true。存在 P0 缺口。

### raw_result_reference 使用方式

弱引用，仅用于定位 Data Agent markdown 摘要；不能作为可回放证据。

### 是否符合 Data Agent-only 结论上限

符合。partial 能表达“局部高度疑似 + 整体证据不足”。

## 3. 样例 9：complex no_permission full spec

### parser 应识别的 status

`no_permission`

### returned_type

`complex_permission_blocked`

### key_findings

- 后端请求域可见目标接口请求聚集。
- 部分设备 / SDK / 包类型存在异常线索。
- 前端行为域无权限。
- 策略引擎域无权限。
- 关联网络域无权限。
- 授权运营域无权限。

### strong_evidence

通常为空。权限不足导致关键链路和反证无法闭合。

### medium_evidence

- 后端请求聚集。
- 部分设备异常线索。

### weak_evidence

- SDK / 包类型异常原因未闭合。
- Data Agent “局部疑点”文字，只能作为 provider_conclusion_hint。

### counter_evidence

- 官方包埋点缺失。
- join 口径偏差。
- 采集延迟。
- 群控真机。
- 合法自动化 / 授权工具。

### missing_evidence

- 前端行为域明细。
- 前后端精确 join 口径。
- 策略引擎命中 / 处置链路。
- 关联网络 / 群控标签。
- 授权运营白名单。
- 破解包样本工件。

### quality_risks

- 核心数据域无权限。
- 关键反证无法排除。
- 后端请求和设备异常不能单独支持协议攻击。
- no_permission 必须降级。

### permission_notes

- 前端行为域无权限：无法确认前端是否真实无日志。
- 策略引擎域无权限：无法确认 BLOCK / CHALLENGE / MONITOR / 放行。
- 关联网络域无权限：无法排除群控真机。
- 授权运营域无权限：无法排除合法自动化 / 授权工具。

### provider_limitations

- `permission_limited`
- `dataagent_offline_not_realtime`
- `missing_realtime_log_provider`
- `missing_risk_engine_provider`
- `missing_relation_graph_provider`
- `missing_manual_review_provider`

### conclusion_support.level

`insufficient_support`

### conclusion_support.reason

核心数据域无权限，无法确认前端真实缺失，也无法排除群控真机、合法自动化、join 口径和策略链路问题。

### recommended_next_provider

由 Router / Dennis Agent 生成：

- `permission_request`
- `dataagent_provider`，权限开通后重查
- `realtime_log_provider`
- `device_fingerprint_provider`
- `risk_engine_provider`
- `relation_graph_provider`
- `manual_review_provider`

### manual_review_required

true。无权限域影响结论。

### raw_result_reference 使用方式

`queryId + sessionId + 本地保存路径或内部引用`，弱引用，只能证明存在一次权限受限返回。

### 是否符合 Data Agent-only 结论上限

符合。no_permission 正确降级，不能强结论。

## 4. parser 新增 / 强化规则

已写入 `dataagent_markdown_response_parser_v1.md`：

1. complex success 也不能自动升级为明确判断。只要存在 P0 级关键反证未排除，结论上限不能超过高度疑似。
2. parser 必须识别并区分数据发现、模型推测、假设性分析。
3. 数据发现可以进入 `key_findings / evidence`；模型推测只能进入 `weak_evidence / quality_risks / speculation_notes`；假设性分析不得进入 strong_evidence。
4. parser 必须解析反证路径排除状态表，支持已排除、部分排除、未排除、未查、无权限、待验证。
5. 协议攻击 P0 反证未排除或无权限时不得明确判断。
6. parser 必须识别 P0 / P1 / P2 / P3 下一步，并把 P0 缺口写入 missing_evidence 和 Router / Dennis 的 next provider 依据。
7. parser 必须区分策略引擎 `BLOCK / CHALLENGE / MONITOR` 的证据强度。
8. parser 必须识别 Data Agent-only provider limitations。
9. no_permission 中无权限域必须进入 permission_notes；对结论有影响的无权限域必须进入 missing_evidence。
10. partial 中可查域的数据发现可以进入 evidence，未查关键域必须进入 missing_evidence，结论支持“局部高度疑似 + 整体证据不足”。

## 5. complex success 是否会被过度强判

不会。

规则明确：complex success 不自动等于明确判断；只要 P0 反证未闭合，结论上限不能超过高度疑似。Data Agent-only 阶段仍需 Dennis Agent 和人工复核。

## 6. partial 是否能表达“局部高度疑似 + 整体证据不足”

能。

parser 支持局部 / 整体拆分：

- 局部可查路径：可进入 medium / strong evidence。
- 整体判断：若关键域缺失，仍为 insufficient_support。

## 7. no_permission 是否能正确降级

能。

无权限域进入：

- `permission_notes`
- `missing_evidence`
- `quality_risks`

结论不得强于证据不足 / 局部高度疑似。

## 8. P0 缺口是否能限制结论上限

能。

P0 缺口包括：

- 破解包绕 SDK / 绕采集
- 官方包埋点缺失
- 前后端 join 口径问题
- 合法自动化 / 授权工具
- 群控真机

任一 P0 缺口未排除、未查、无权限、待验证，结论不得明确判断，`manual_review_required = true`。

## 9. 策略引擎 BLOCK / CHALLENGE / MONITOR 是否能区分证据强度

能。

- `BLOCK`：较强处置证据，但策略命中不等于风险事实。
- `CHALLENGE`：中等风险 / 验证证据。
- `MONITOR`：观察证据，不能作为强打击证据。

## 10. 是否还需要真实 Data Agent response 样例

需要。建议补充：

- 真实 complex success markdown。
- 真实反证排除状态表样式。
- 真实 P0 / P1 / P2 / P3 表达样式。
- 真实策略引擎 BLOCK / CHALLENGE / MONITOR 文字。
- 真实 no_permission 错误文本和权限提示格式。
- parser 输出与人工复核一致性样本。

## 11. 是否可以进入第一个真实只读 case

可以进入，但成功标准仍应是：

- question 是否被 Data Agent 理解。
- markdown 是否能被 parser 稳定解析。
- P0 缺口是否限制结论上限。
- provider hint 是否与 Dennis final judgement 分离。
- no_permission / partial / sql_only / empty / failed 是否正确降级。

不应把“明确协议攻击”作为第一个真实只读 case 的成功标准。

