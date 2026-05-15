# Tool Selection Rules v1

## 0. 目标

本文件定义 Evidence Tool Router 如何基于 `query_intent_schema_v2` 选择 provider。核心原则是：先判断证据需求，再选择工具；不要默认把 query intent 发给 Data Agent。

## 1. 选择优先级

Router 选择 provider 时，按以下因素排序：

1. 证据时效要求：实时、准实时、离线、复盘。
2. 证据类型：链路、设备、策略、图关系、收益、渠道、AB、画像、人工确认。
3. 数据域：前端行为、后端数据、设备信息、策略引擎、关联网络、活动、渠道、用户信息、风险画像。
4. 是否需要结构化输出。
5. 是否需要实时性。
6. 是否涉及权限敏感。
7. 是主证据还是反证。
8. provider 可用性。
9. 成本和查询范围。

## 2. 基本规则

- 实时前后端链路、NG、service 明细：优先 `realtime_log_provider`。
- Hive / BI / 看板 / AB / 画像标签：优先 `dataagent_provider`。
- 策略命中、处置链路：优先 `risk_engine_provider`。
- 实时指纹、异步 SDK、设备画像：优先 `device_fingerprint_provider`。
- 强设备关联、用户团组、团伙扩散：优先 `relation_graph_provider`。
- 已有专题 API / 结构化特征：优先 `structured_sql_or_feature_provider`。
- 缺权限、证据冲突、业务合理性判断：转 `manual_review_provider`。

## 3. 不要默认 Data Agent

Data Agent 不是所有证据的默认 provider。

只有当证据适合以下类型时，才优先选择 `dataagent_provider`：

- Hive / 离线取数。
- BI / 看板 / 多维分析。
- 数据集分析。
- SQL 生成。
- 表检索 / 表结构 / 字段口径。
- AB 实验分析。
- 画像标签 / 人群圈选。
- 离线复盘、趋势分析、归因分析。

以下场景不应默认选择 Data Agent：

- 低延迟前后端链路补证。
- NG 网关请求级明细。
- 策略引擎实时决策。
- 风控实时指纹。
- 设备画像在线查询。
- 强设备关联 / 用户团组图在线查询。
- 结构化 feature service。

## 4. 多 Provider 组合

Router 支持一个 query intent 拆成多个 provider request。

### 协议攻击

- `realtime_log_provider`：查前后端链路、NG 请求、接口序列。
- `device_fingerprint_provider`：查 SDK / 指纹 / 设备环境。
- `risk_engine_provider`：查策略命中和处置链路。
- `dataagent_provider`：做离线复盘和聚合趋势。
- `manual_review_provider`：合法自动化或授权工具边界不清时介入。

### 群控真机

- `device_fingerprint_provider`：查设备环境和指纹相似。
- `relation_graph_provider`：查强关联和用户团组。
- `realtime_log_provider`：查同批启动 / 停止和行为序列。
- `dataagent_provider`：查收益聚集和离线复盘。

### 渠道归因劫持

- `dataagent_provider`：查曝光、点击、激活、CTIT、自然量跷跷板、后验质量。
- `structured_sql_or_feature_provider`：如已有专题特征，补充低延迟结构化结果。
- `manual_review_provider`：投放策略、预算、品牌活动口径需业务确认时介入。

### 导流截流

- `realtime_log_provider`：查搜索、关注、私信、触达路径。
- `relation_graph_provider`：查账号矩阵和扩散关系。
- `dataagent_provider`：做离线复盘、投诉聚合、趋势分析。
- `manual_review_provider`：站外承接证据和正常社交边界需要人工确认。

## 5. Fallback 规则

- `realtime_log_provider` 不可用：降级为 Data Agent 离线复盘，但不能支持实时强结论。
- `dataagent_provider` 返回 markdown partial：需要 parser + 人工确认。
- `risk_engine_provider` 只有策略命中：不能直接当风险事实。
- `relation_graph_provider` 只有关联：不能直接当作恶事实。
- `device_fingerprint_provider` 只有 SDK 缺失：不能直接判破解包。
- `structured_sql_or_feature_provider` 返回空：不能直接解释为无风险。
- `manual_review_provider` 超时：保持证据不足，不自动升级结论。
- 所有 provider 都失败：输出证据不足和人工补证任务。

## 6. 强结论保护规则

以下情况不得输出强结论：

- provider 无权限。
- provider 超时。
- provider partial。
- provider empty result 但覆盖范围未知。
- provider 结果冲突且未解释。
- parser 失败。
- 关键反证未闭合。
- 只有策略命中、只有设备聚集、只有风险画像、只有前端无日志、只有低钱效。

