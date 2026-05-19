# Router Mock Regression Cases v1

## 0. 目标

本文件设计 Evidence Tool Router 层 mock 回归，用于验证工具选择是否合理。当前不调用真实工具，不编造真实结果。

## Case 1：前端无日志 + 后端有请求

- 用户问题：一批请求后端存在，但前端无日志，是否协议攻击？
- query_intent 摘要：验证前后端链路一致性、SDK 覆盖、join 口径和协议反证。
- 应选择 provider：`realtime_log_provider`、`device_fingerprint_provider`
- 不应选择 provider：不应只选 `dataagent_provider`
- 选择理由：实时链路和 SDK 覆盖需要日志与设备证据；Data Agent 只做离线复盘。
- fallback provider：`dataagent_provider`、`manual_review_provider`
- 归一化证据类型：链路一致性证据、设备证据、反证缺口
- 是否需要人工确认：强结论或处置前需要
- 不能直接下结论的原因：前端无日志可能来自破解包、埋点缺失、join 口径问题或合法自动化。

## Case 2：后端有请求 + SDK 缺失

- 用户问题：后端请求存在，但 SDK 日志缺失，是否破解包或协议？
- query_intent 摘要：检查 SDK 状态、实时指纹、app 版本 / 签名、前后端链路。
- 应选择 provider：`device_fingerprint_provider`、`realtime_log_provider`
- 不应选择 provider：不应只选 `risk_engine_provider`
- 选择理由：SDK 缺失必须由设备和日志证据解释。
- fallback provider：`dataagent_provider`、`manual_review_provider`
- 归一化证据类型：设备证据、链路证据、质量风险
- 是否需要人工确认：需要，尤其涉及官方版本缺陷或破解包判断
- 不能直接下结论的原因：SDK 缺失也可能是版本差异、采集延迟或埋点问题。

## Case 3：接口高频 + token/device/ip/ua 冲突

- 用户问题：接口高频且 token/device/ip/ua 不一致，是否协议攻击或 token 泄露？
- query_intent 摘要：验证请求级一致性、策略命中、设备环境和接口序列。
- 应选择 provider：`realtime_log_provider`、`risk_engine_provider`、`device_fingerprint_provider`
- 不应选择 provider：不应只选 `dataagent_provider`
- 选择理由：请求级冲突需要实时日志、策略和设备上下文。
- fallback provider：`dataagent_provider`
- 归一化证据类型：链路证据、策略证据、设备证据
- 是否需要人工确认：冻结、处罚或扣除前需要
- 不能直接下结论的原因：高频本身不足以证明攻击，需排除合法自动化和多端正常场景。

## Case 4：活动低质但无黑产证据

- 用户问题：活动低钱效用户很多，是否黑产？
- query_intent 摘要：检查活动参与、留存、付费、奖励、设备和关系聚集。
- 应选择 provider：`dataagent_provider`、`relation_graph_provider`
- 不应选择 provider：不应只选 `risk_engine_provider`
- 选择理由：活动质量和收益结果偏离线，关系图用于补团组。
- fallback provider：`structured_sql_or_feature_provider`、`manual_review_provider`
- 归一化证据类型：离线分析证据、关系证据
- 是否需要人工确认：扣除奖励或处罚前需要
- 不能直接下结论的原因：低钱效不等于黑产，可能只是低质用户或业务投放问题。

## Case 5：渠道 CTIT 异常

- 用户问题：某渠道 CTIT 异常，是否点击注入或归因抢量？
- query_intent 摘要：分析曝光、点击、激活、CTIT、自然量跷跷板、新客真实性和后验质量。
- 应选择 provider：`dataagent_provider`
- 不应选择 provider：不应只选 `realtime_log_provider`
- 选择理由：渠道归因更适合离线 / 准实时趋势和归因分析。
- fallback provider：`structured_sql_or_feature_provider`、`manual_review_provider`
- 归一化证据类型：渠道归因证据、质量风险
- 是否需要人工确认：投放扣量或结算调整前需要
- 不能直接下结论的原因：CTIT 异常也可能来自投放策略、预算、品牌活动或归因窗口变化。

## Case 6：DAU/DNU 单日异常

- 用户问题：DAU/DNU 单日异常，是否作弊？
- query_intent 摘要：结合指标时间序列和业务上下文做异常归因。
- 应选择 provider：`dataagent_provider`，使用 `metric_anomaly_business_context_join`
- 不应选择 provider：不应直接选协议或群控 provider 下强结论
- 选择理由：指标异常需排查渠道、活动、实验、版本、策略、数据质量和用户分群变化。
- fallback provider：`manual_review_provider`
- 归一化证据类型：指标异常归因证据
- 是否需要人工确认：涉及策略或业务解释时需要
- 不能直接下结论的原因：单日指标波动不能直接等同作弊。

## Case 7：群控真机爬取

- 用户问题：一批真机疑似群控爬取内容资产。
- query_intent 摘要：检查设备团组、统一调度、接口访问、行为路径和资产目标。
- 应选择 provider：`device_fingerprint_provider`、`relation_graph_provider`、`realtime_log_provider`
- 不应选择 provider：不应只选 `dataagent_provider`
- 选择理由：群控真机需要设备、图关系和实时行为共同闭合。
- fallback provider：`dataagent_provider`
- 归一化证据类型：设备证据、关系证据、链路证据
- 是否需要人工确认：强处置前需要
- 不能直接下结论的原因：设备聚集不等于群控，需看到统一调度和目标收益。

## Case 8：直播间截流 / 站外添加

- 用户问题：直播间用户被站外添加，是否反爬或协议？
- query_intent 摘要：检查信息暴露入口、搜索 / 关注 / 私信链路、站外承接和账号矩阵。
- 应选择 provider：`realtime_log_provider`、`relation_graph_provider`、`dataagent_provider`
- 不应选择 provider：不应默认 `protocol_attack_expert_skill` 或只选 Data Agent
- 选择理由：截流需要触达日志、矩阵关系和离线复盘。
- fallback provider：`manual_review_provider`
- 归一化证据类型：导流截流证据、关系证据、离线复盘证据
- 是否需要人工确认：需要，涉及正常社交和授权运营边界
- 不能直接下结论的原因：站外添加不等于爬虫或协议，可能是正常社交、用户主动外联或授权运营。

## Case 9：策略命中后误伤复盘

- 用户问题：某策略命中后，怎么评估误伤和效果？
- query_intent 摘要：检查策略命中、处置链路、后验风险、业务指标、申诉和客诉。
- 应选择 provider：`risk_engine_provider`、`dataagent_provider`
- 不应选择 provider：不应只选 `risk_engine_provider`
- 选择理由：策略命中走 risk_engine，后验效果和业务指标走 Data Agent。
- fallback provider：`structured_sql_or_feature_provider`、`manual_review_provider`
- 归一化证据类型：策略证据、后验证据、误伤证据
- 是否需要人工确认：策略调整前必须
- 不能直接下结论的原因：策略命中不等于风险事实，需要后验和对照。

## Case 10：合法矩阵 / MCN 接口化运营

- 用户问题：商家 / 达人 / MCN 批量登录或接口化运营，是否群控或协议？
- query_intent 摘要：检查授权主体、账号范围、工具来源、操作人、敏感动作、收益主体和历史违规。
- 应选择 provider：`dataagent_provider`、`structured_sql_or_feature_provider`、`manual_review_provider`
- 不应选择 provider：不应直接选群控或协议 provider 下拦截结论
- 选择理由：合法矩阵边界依赖业务登记、授权范围、结构化数据和人工确认。
- fallback provider：`risk_engine_provider`
- 归一化证据类型：合法矩阵证据、人工证据、策略证据
- 是否需要人工确认：需要
- 不能直接下结论的原因：批量行为不等于黑产，有授权但超范围也应局部治理。

