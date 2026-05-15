# Evidence Tool Router Mock Regression - 10 Case

## 0. 回归边界

本轮只验证 Evidence Tool Router 的工具选择、`provider_request` 摘要生成、mock `provider_response` 归一化为 `unified_normalized_evidence` 的链路。

- 不调用真实工具。
- 不修改核心 Skill。
- 不编造真实 API、真实表名、真实字段名、真实 SQL。
- mock response 只用于验证解释能力，不代表真实查询结果。

## Case 1：前端无日志 + 后端有请求

1. 用户问题：一批请求后端存在，但前端无日志，是否协议攻击？
2. query_intent 摘要：验证前后端链路一致性、SDK 覆盖、join 口径和协议反证。
3. 目标证据：前端事件、后端请求、SDK 覆盖、NG 请求、join 口径、破解包 / 埋点缺失 / 合法自动化反证。
4. 应选择 provider：`realtime_log_provider`、`device_fingerprint_provider`。
5. 不应选择 provider：不应只选 `dataagent_provider`。
6. 选择理由：前后端链路和 SDK 覆盖是实时 / 准实时证据，Data Agent 只能做离线复盘。
7. provider_request 摘要：
   - `realtime_log_provider`：查询前端事件、后端请求、NG 请求、时间窗对齐和接口序列。
   - `device_fingerprint_provider`：查询 SDK 状态、实时指纹、设备上下文和版本 / 渠道线索。
8. mock provider_response 摘要：
   - `realtime_log_provider`：`partial`，返回后端请求存在、前端事件覆盖不足，但提示部分前端日志可能延迟。
   - `device_fingerprint_provider`：`success`，返回 SDK 覆盖异常线索，但不能排除官方包采集缺失。
9. unified_normalized_evidence 摘要：
   - evidence_type：链路一致性证据 + 设备证据。
   - medium_evidence：后端请求与前端事件不一致、SDK 覆盖异常。
   - counter_evidence：前端日志延迟、埋点缺失、官方包采集问题、合法自动化未闭合。
   - conclusion_support：`insufficient_support`。
10. 是否需要 fallback provider：需要，`dataagent_provider` 做离线复盘，`manual_review_provider` 确认埋点 / 授权工具。
11. 是否需要人工确认：需要，强结论或处置前必须人工确认。
12. 不能直接下结论的原因：前端无日志可能来自破解包、埋点缺失、join 口径问题或合法自动化。
13. 是否符合 `tool_selection_rules_v1.md`：符合。
14. 如果不符合，需要回写哪个 router 文件：不需要。

## Case 2：后端有请求 + SDK 缺失

1. 用户问题：后端请求存在，但 SDK 日志缺失，是否破解包或协议？
2. query_intent 摘要：检查 SDK 状态、实时指纹、app 版本 / 签名、前后端链路。
3. 目标证据：SDK 覆盖、实时指纹、设备画像、后端请求、官方版本采集反证。
4. 应选择 provider：`device_fingerprint_provider`、`realtime_log_provider`。
5. 不应选择 provider：不应只选 `risk_engine_provider`。
6. 选择理由：SDK 缺失必须由设备和日志证据解释，策略命中不能证明采集缺失原因。
7. provider_request 摘要：
   - `device_fingerprint_provider`：查询 SDK 状态、实时指纹、设备环境、版本 / 签名抽象线索。
   - `realtime_log_provider`：查询后端请求与端侧事件是否存在可对齐链路。
8. mock provider_response 摘要：
   - `device_fingerprint_provider`：`ambiguous_result`，SDK 缺失存在，但版本差异和采集延迟未排除。
   - `realtime_log_provider`：`success`，后端请求存在，前端链路不完整。
9. unified_normalized_evidence 摘要：
   - evidence_type：设备证据 + 链路证据。
   - medium_evidence：SDK 缺失与后端请求并存。
   - quality_risks：SDK 采集延迟、版本差异、官方包埋点缺失。
   - conclusion_support：`insufficient_support`。
10. 是否需要 fallback provider：需要，`dataagent_provider` 做版本 / 渠道离线趋势，`manual_review_provider` 确认官方采集变更。
11. 是否需要人工确认：需要。
12. 不能直接下结论的原因：SDK 缺失也可能是版本差异、采集延迟或埋点问题。
13. 是否符合 `tool_selection_rules_v1.md`：符合。
14. 如果不符合，需要回写哪个 router 文件：不需要。

## Case 3：接口高频 + token/device/ip/ua 冲突

1. 用户问题：接口高频且 token/device/ip/ua 不一致，是否协议攻击或 token 泄露？
2. query_intent 摘要：验证请求级一致性、策略命中、设备环境和接口序列。
3. 目标证据：接口频次、接口序列、token / device / ip / ua 一致性、策略命中、设备环境、合法自动化反证。
4. 应选择 provider：`realtime_log_provider`、`risk_engine_provider`、`device_fingerprint_provider`。
5. 不应选择 provider：不应只选 `dataagent_provider`。
6. 选择理由：请求级冲突需要实时日志、策略和设备上下文共同解释。
7. provider_request 摘要：
   - `realtime_log_provider`：查询请求序列、频次、token / device / ip / ua 一致性。
   - `risk_engine_provider`：查询策略命中、风险分、处置链路。
   - `device_fingerprint_provider`：查询设备指纹和环境一致性。
8. mock provider_response 摘要：
   - `realtime_log_provider`：`success`，返回请求高频和上下文冲突摘要。
   - `risk_engine_provider`：`success`，返回策略命中和处置结果摘要。
   - `device_fingerprint_provider`：`partial`，设备环境异常但部分指纹缺失。
9. unified_normalized_evidence 摘要：
   - evidence_type：链路证据 + 策略证据 + 设备证据。
   - strong_evidence：请求级上下文冲突、接口序列异常。
   - medium_evidence：策略命中、设备环境异常。
   - counter_evidence：合法自动化、多端正常场景、设备指纹缺失未闭合。
   - conclusion_support：`highly_suspicious_support`。
10. 是否需要 fallback provider：需要，`dataagent_provider` 做离线聚合趋势和样本复盘。
11. 是否需要人工确认：需要，冻结、处罚或扣除前必须确认。
12. 不能直接下结论的原因：高频本身不足以证明攻击，且合法自动化和多端场景未完全排除。
13. 是否符合 `tool_selection_rules_v1.md`：符合。
14. 如果不符合，需要回写哪个 router 文件：不需要。

## Case 4：活动低质但无黑产证据

1. 用户问题：活动低钱效用户很多，是否黑产？
2. query_intent 摘要：检查活动参与、留存、付费、奖励、设备和关系聚集。
3. 目标证据：活动参与路径、奖励 / 提现、留存 / 付费后验、设备 / 用户团组、任务化反证。
4. 应选择 provider：`dataagent_provider`、`relation_graph_provider`。
5. 不应选择 provider：不应只选 `risk_engine_provider`。
6. 选择理由：活动质量和收益结果偏离线，关系图用于补团组和扩散结构。
7. provider_request 摘要：
   - `dataagent_provider`：生成离线活动质量、奖励、留存和付费复盘问题。
   - `relation_graph_provider`：查询用户团组、设备关联和邀请 / 收益关系。
8. mock provider_response 摘要：
   - `dataagent_provider`：`success`，返回低钱效和低留存摘要。
   - `relation_graph_provider`：`empty_result`，未返回明确团组，但覆盖范围未知。
9. unified_normalized_evidence 摘要：
   - evidence_type：离线分析证据 + 关系证据。
   - weak_evidence：低钱效、低留存。
   - missing_evidence：任务平台、收益链、团组关系、提现聚集。
   - conclusion_support：`insufficient_support`。
10. 是否需要 fallback provider：需要，`structured_sql_or_feature_provider` 或人工补证。
11. 是否需要人工确认：扣除奖励或处罚前需要。
12. 不能直接下结论的原因：低钱效不等于黑产，可能是低质用户或业务投放问题。
13. 是否符合 `tool_selection_rules_v1.md`：符合。
14. 如果不符合，需要回写哪个 router 文件：不需要。

## Case 5：渠道 CTIT 异常

1. 用户问题：某渠道 CTIT 异常，是否点击注入或归因抢量？
2. query_intent 摘要：分析曝光、点击、激活、CTIT、自然量跷跷板、新客真实性和后验质量。
3. 目标证据：曝光 → 点击 → 激活链路、CTIT 分布、自然量 / 渠道量变化、新客真实性、后验质量、投放策略反证。
4. 应选择 provider：`dataagent_provider`。
5. 不应选择 provider：不应只选 `realtime_log_provider`。
6. 选择理由：渠道归因更适合离线 / 准实时趋势和归因分析。
7. provider_request 摘要：
   - `dataagent_provider`：生成渠道归因、CTIT、自然量跷跷板和后验质量分析问题。
8. mock provider_response 摘要：
   - `dataagent_provider`：`partial`，返回 CTIT 分布异常摘要，但投放策略和预算变化未覆盖。
9. unified_normalized_evidence 摘要：
   - evidence_type：渠道归因证据。
   - medium_evidence：CTIT 异常和部分新客质量异常。
   - counter_evidence：投放策略、预算变化、品牌活动、归因窗口未排除。
   - conclusion_support：`insufficient_support`。
10. 是否需要 fallback provider：需要，`structured_sql_or_feature_provider` 补专题特征，`manual_review_provider` 确认投放背景。
11. 是否需要人工确认：投放扣量或结算调整前需要。
12. 不能直接下结论的原因：CTIT 异常也可能来自投放策略、预算、品牌活动或归因窗口变化。
13. 是否符合 `tool_selection_rules_v1.md`：符合。
14. 如果不符合，需要回写哪个 router 文件：不需要。

## Case 6：DAU/DNU 单日异常

1. 用户问题：DAU/DNU 单日异常，是否作弊？
2. query_intent 摘要：结合指标时间序列和业务上下文做异常归因。
3. 目标证据：指标时间序列、渠道变化、活动变化、实验变化、版本发布、策略变化、数据质量、用户分群。
4. 应选择 provider：`dataagent_provider`，使用 `metric_anomaly_business_context_join`。
5. 不应选择 provider：不应直接选协议或群控 provider 下强结论。
6. 选择理由：指标异常需先做业务上下文归因，而不是直接进入攻击定性。
7. provider_request 摘要：
   - `dataagent_provider`：生成指标异常归因问题，要求按业务上下文 join 检查渠道、活动、实验、版本、策略和数据质量。
8. mock provider_response 摘要：
   - `dataagent_provider`：`success`，返回单日异常和多个业务上下文候选解释摘要。
9. unified_normalized_evidence 摘要：
   - evidence_type：指标异常归因证据。
   - medium_evidence：指标异常存在。
   - counter_evidence：业务上下文变化可解释部分波动。
   - conclusion_support：`reverse_or_exclusion_support`，暂不支持黑产定性。
10. 是否需要 fallback provider：需要，若业务上下文无法解释，再转风险证据补证 provider。
11. 是否需要人工确认：涉及策略或业务解释时需要。
12. 不能直接下结论的原因：单日指标波动不能直接等同作弊。
13. 是否符合 `tool_selection_rules_v1.md`：符合。
14. 如果不符合，需要回写哪个 router 文件：不需要。

## Case 7：群控真机爬取

1. 用户问题：一批真机疑似群控爬取内容资产。
2. query_intent 摘要：检查设备团组、统一调度、接口访问、行为路径和资产目标。
3. 目标证据：设备环境、强关联、用户团组、同批启动 / 停止、接口访问序列、资产目标、收益或目标聚集。
4. 应选择 provider：`device_fingerprint_provider`、`relation_graph_provider`、`realtime_log_provider`。
5. 不应选择 provider：不应只选 `dataagent_provider`。
6. 选择理由：群控真机需要设备、图关系和实时行为共同闭合。
7. provider_request 摘要：
   - `device_fingerprint_provider`：查询设备环境、指纹相似和设备画像。
   - `relation_graph_provider`：查询强设备关联和用户团组。
   - `realtime_log_provider`：查询同批行为、接口访问和资产目标。
8. mock provider_response 摘要：
   - `device_fingerprint_provider`：`success`，返回设备相似和部分异常环境摘要。
   - `relation_graph_provider`：`success`，返回强关联团组摘要。
   - `realtime_log_provider`：`partial`，返回部分同批行为，但资产目标链路不完整。
9. unified_normalized_evidence 摘要：
   - evidence_type：设备证据 + 关系证据 + 链路证据。
   - strong_evidence：设备相似、强关联团组。
   - medium_evidence：部分同批行为。
   - missing_evidence：完整资产访问路径和收益目标。
   - conclusion_support：`highly_suspicious_support`。
10. 是否需要 fallback provider：需要，`dataagent_provider` 做离线资产访问和收益复盘。
11. 是否需要人工确认：强处置前需要。
12. 不能直接下结论的原因：设备聚集不等于群控，需看到统一调度和目标收益闭合。
13. 是否符合 `tool_selection_rules_v1.md`：符合。
14. 如果不符合，需要回写哪个 router 文件：不需要。

## Case 8：直播间截流 / 站外添加

1. 用户问题：直播间用户被站外添加，是否反爬或协议？
2. query_intent 摘要：检查信息暴露入口、搜索 / 关注 / 私信链路、站外承接和账号矩阵。
3. 目标证据：信息暴露入口、搜索添加、关注 / 私信触达、站外承接、账号矩阵、正常社交和授权运营反证。
4. 应选择 provider：`realtime_log_provider`、`relation_graph_provider`、`dataagent_provider`。
5. 不应选择 provider：不应默认 `protocol_attack_expert_skill` 或只选 Data Agent。
6. 选择理由：截流需要触达日志、矩阵关系和离线复盘。
7. provider_request 摘要：
   - `realtime_log_provider`：查询搜索、关注、私信和触达路径。
   - `relation_graph_provider`：查询导流账号矩阵和扩散关系。
   - `dataagent_provider`：做投诉、举报、触达趋势离线复盘。
8. mock provider_response 摘要：
   - `realtime_log_provider`：`success`，返回触达链路摘要。
   - `relation_graph_provider`：`partial`，账号关系存在但矩阵边界不完整。
   - `dataagent_provider`：`success`，返回离线投诉趋势摘要。
9. unified_normalized_evidence 摘要：
   - evidence_type：导流截流证据 + 关系证据 + 离线复盘证据。
   - medium_evidence：站内触达链路和投诉趋势。
   - missing_evidence：站外承接证据、正常社交 / 授权触达反证。
   - conclusion_support：`highly_suspicious_support`，但不能转协议或反爬强结论。
10. 是否需要 fallback provider：需要，`manual_review_provider` 补站外承接和正常社交边界。
11. 是否需要人工确认：需要。
12. 不能直接下结论的原因：站外添加不等于爬虫或协议，可能是正常社交、用户主动外联或授权运营。
13. 是否符合 `tool_selection_rules_v1.md`：符合。
14. 如果不符合，需要回写哪个 router 文件：不需要。

## Case 9：策略命中后误伤复盘

1. 用户问题：某策略命中后，怎么评估误伤和效果？
2. query_intent 摘要：检查策略命中、处置链路、后验风险、业务指标、申诉和客诉。
3. 目标证据：策略命中、处置动作、灰度分组、后验风险、业务指标、申诉 / 客诉、对照差异。
4. 应选择 provider：`risk_engine_provider`、`dataagent_provider`。
5. 不应选择 provider：不应只选 `risk_engine_provider`。
6. 选择理由：策略命中走 risk engine，后验效果和业务指标走 Data Agent。
7. provider_request 摘要：
   - `risk_engine_provider`：查询策略命中、处置链路、灰度和返回码。
   - `dataagent_provider`：查询后验指标、业务影响、申诉 / 客诉聚合和趋势。
8. mock provider_response 摘要：
   - `risk_engine_provider`：`success`，返回策略命中和处置链路摘要。
   - `dataagent_provider`：`partial`，后验指标返回，但申诉口径未覆盖。
9. unified_normalized_evidence 摘要：
   - evidence_type：策略证据 + 后验证据 + 误伤证据。
   - medium_evidence：策略命中和业务影响存在。
   - missing_evidence：申诉 / 客诉、人工复核样本、对照组。
   - conclusion_support：`insufficient_support`。
10. 是否需要 fallback provider：需要，`structured_sql_or_feature_provider` 或 `manual_review_provider` 补误伤样本。
11. 是否需要人工确认：策略调整前必须人工确认。
12. 不能直接下结论的原因：策略命中不等于风险事实，需要后验和对照。
13. 是否符合 `tool_selection_rules_v1.md`：符合。
14. 如果不符合，需要回写哪个 router 文件：不需要。

## Case 10：合法矩阵 / MCN 接口化运营

1. 用户问题：商家 / 达人 / MCN 批量登录或接口化运营，是否群控或协议？
2. query_intent 摘要：检查授权主体、账号范围、工具来源、操作人、敏感动作、收益主体和历史违规。
3. 目标证据：授权主体、账号范围、工具来源、操作人、调用接口、敏感动作、收益主体、业务登记、历史违规。
4. 应选择 provider：`dataagent_provider`、`structured_sql_or_feature_provider`、`manual_review_provider`。
5. 不应选择 provider：不应直接选群控或协议 provider 下拦截结论。
6. 选择理由：合法矩阵边界依赖业务登记、授权范围、结构化数据和人工确认。
7. provider_request 摘要：
   - `dataagent_provider`：查询离线授权、历史违规和业务登记相关摘要。
   - `structured_sql_or_feature_provider`：查询结构化授权范围、工具来源和账号范围。
   - `manual_review_provider`：确认业务合理性和授权边界。
8. mock provider_response 摘要：
   - `dataagent_provider`：`success`，返回历史运营和风险摘要。
   - `structured_sql_or_feature_provider`：`no_permission`，授权范围明细不可见。
   - `manual_review_provider`：`partial`，业务侧确认存在合法运营可能，但超范围未判断。
9. unified_normalized_evidence 摘要：
   - evidence_type：合法矩阵证据 + 人工证据 + 权限风险。
   - medium_evidence：存在合法运营可能。
   - missing_evidence：授权范围、工具来源、敏感动作、收益主体闭合。
   - conclusion_support：`insufficient_support`。
10. 是否需要 fallback provider：需要，补权限或继续人工复核；可选 `risk_engine_provider` 查处置链路。
11. 是否需要人工确认：需要。
12. 不能直接下结论的原因：批量行为不等于黑产，有授权但超范围也应局部治理。
13. 是否符合 `tool_selection_rules_v1.md`：符合。
14. 如果不符合，需要回写哪个 router 文件：不需要。

## 汇总

### 1. 10 case provider 选择准确率

10 / 10。全部 case 的 provider 选择与 `router_mock_regression_cases_v1.md` 和 `tool_selection_rules_v1.md` 一致。

### 2. 哪些 provider 边界最容易混淆

- `dataagent_provider` vs `realtime_log_provider`：前后端链路、NG 请求、接口序列不能默认走 Data Agent；Data Agent 只能做离线复盘。
- `risk_engine_provider` vs 风险事实：策略命中只能证明策略决策发生，不能证明作恶事实。
- `device_fingerprint_provider` vs 破解包 / 群控结论：SDK 缺失和设备聚集都不是强结论。
- `relation_graph_provider` vs 作恶事实：强关联、团组和矩阵只说明关系，不直接说明违规。
- `manual_review_provider` vs 自动判断：授权运营、站外承接、证据冲突需要人工确认。

### 3. Data Agent 是否仍被误用为默认 provider

没有。10 个 case 中，Data Agent 只在离线复盘、趋势归因、渠道 CTIT、活动质量、指标异常、合法矩阵和后验效果场景作为主 provider 或补充 provider；实时链路、设备、策略、图关系均优先选择对应 provider。

### 4. 哪些 case 需要多 provider 组合

- Case 1：前端无日志 + 后端有请求。
- Case 2：后端有请求 + SDK 缺失。
- Case 3：接口高频 + token/device/ip/ua 冲突。
- Case 4：活动低质但无黑产证据。
- Case 7：群控真机爬取。
- Case 8：直播间截流 / 站外添加。
- Case 9：策略命中后误伤复盘。
- Case 10：合法矩阵 / MCN 接口化运营。

### 5. unified_normalized_evidence_schema 是否够用

基本够用。当前 schema 能表达：

- 跨 provider 来源。
- 强 / 中 / 弱证据。
- 反证。
- 缺失证据。
- 质量风险。
- provider limitations。
- 结论支持等级。
- 下一步 provider 和人工确认。

轻微缺口：多 provider 同一 case 的 evidence merge 规则还没有单独文档化，例如多个 normalized evidence 如何合并成 case-level evidence bundle。建议后续新增 `evidence_bundle_merge_rules_v1.md`，但不阻塞首个只读试点。

### 6. 是否可以进入首个真实 provider 只读试点

可以进入最小只读试点，但建议只选一个 provider 链路先跑：

- 首选：`realtime_log_provider` 的前后端链路一致性只读试点。
- 配套：`device_fingerprint_provider` 做 SDK / 指纹补证。
- Data Agent 只做离线复盘，不作为实时强结论入口。

### 7. 是否修改了 Skill 文件

否。本轮只新增 `outputs/reviews/evidence_tool_router_mock_regression_10_case.md`。

