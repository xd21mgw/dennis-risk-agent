# Evidence Tool Router Contract v1

## 0. 边界声明

本文件定义 Dennis 风控 Agent 的多工具取证路由层。当前阶段只做设计，不调用真实工具，不定义真实 API、真实表名、真实字段名或真实 SQL。

现有 `07_tools/dataagent/` 保留。Data Agent 在 Router 架构中重新定位为 Hive / BI / 看板 / 数据集 / AB / 画像标签 / 离线分析类 provider，而不是所有证据的默认取证工具。

## 1. 设计目标

Evidence Tool Router 负责把 `query_intent_schema_v2` 中的证据需求，路由到最合适的取证工具 provider。

整体链路：

```text
用户问题
→ Skill 路由
→ 证据需求
→ query_intent_schema_v2
→ evidence_tool_router
→ provider_request
→ provider_response
→ normalized_evidence
→ Dennis Agent 解释
→ 结论等级 / 治理建议 / 人工确认
```

设计目标：

- 让 query intent 先表达证据需求，而不是直接绑定 Data Agent。
- 按证据类型、时效要求、数据域、join path、权限边界选择 provider。
- 支持一个 query intent 拆成多个 provider request。
- 所有 provider 返回最终统一归一化为 `normalized_evidence`。
- 避免把离线工具误用于实时链路强判断。
- 避免因单一 provider 失败、无权限、空结果或 partial 返回产生强结论。

## 2. Router 职责

Evidence Tool Router 负责：

- 读取 `query_intent_schema_v2`。
- 识别 `target_evidence`。
- 读取 `required_data_domains`。
- 读取 `field_types_needed`。
- 读取 `join_paths_needed`。
- 判断所需证据是离线、准实时、实时、图关系、策略引擎还是画像类。
- 选择合适 provider。
- 生成 `provider_request`。
- 接收 `provider_response`。
- 调用统一归一化规则生成 `normalized_evidence`。
- 处理 provider 失败、无权限、超时、部分返回、空结果、解析失败和冲突结果。
- 记录审计和回放信息。

## 3. Router 不负责

Evidence Tool Router 不负责：

- 不做最终风控定性。
- 不替代 Dennis Agent 的风险解释。
- 不自动处罚、冻结、扣除、封禁。
- 不自动上线策略。
- 不绕过权限。
- 不编造数据。
- 不编造 provider 返回。
- 不把 provider 的技术结果直接解释为业务风险事实。

## 4. Provider 类型

### dataagent_provider

定位：

Hive / BI / 数据集 / 看板 / AB / 画像标签 / 离线分析 provider。

适合：

- 离线取数。
- 趋势分析。
- 指标归因。
- 看板解读。
- 数据集分析。
- AB 实验分析。
- 画像标签检索。
- 表检索和字段口径理解。

### realtime_log_provider

定位：

实时或准实时日志 provider。

适合：

- 实时前端日志。
- 后端 service 日志。
- NG 网关日志。
- 长链接日志。
- 拉流日志。
- 接口明细。
- 请求序列。

### risk_engine_provider

定位：

策略引擎实时决策和策略命中 provider。

适合：

- 策略命中。
- 风险分。
- 决策结果。
- 处置动作。
- 灰度分组。
- 返回码。
- 命中规则链路。

### device_fingerprint_provider

定位：

设备和指纹证据 provider。

适合：

- 风控实时指纹。
- 异步 SDK。
- 设备画像。
- 设备环境。
- 模拟器、云手机、改机线索。
- app 版本、签名、SDK 状态。

### relation_graph_provider

定位：

强设备关联、用户团组和关系网络 provider。

适合：

- 强设备关联。
- 用户团组。
- 账号共设备。
- 设备共账号。
- 邀请关系。
- 收益关系。
- 导流矩阵。

### structured_sql_or_feature_provider

定位：

未来结构化 API、实时 SQL、专题 SQL 查询或 feature service provider。

适合：

- 已有专题特征。
- 低延迟结构化查询。
- 批量样本查询。
- 标准化明细或聚合结果。

### manual_review_provider

定位：

人工补证、审批和复核 provider。

适合：

- 自动工具无权限。
- provider 结果冲突。
- 业务合理性判断。
- 合法授权确认。
- 外部证据补充。
- 误伤复核。

## 5. 当前阶段限制

- 只做设计，不调用真实工具。
- 只写 provider 类型和抽象能力，不写真 API。
- Data Agent 仍保留在 `07_tools/dataagent/`，但在 Router 中只是 provider 之一。
- provider 的真实请求协议、权限模型、返回结构、回放能力由未来内部平台补充。
- Router 输出的 normalized evidence 只表达证据支持程度，不替代 Dennis Agent 最终判断。

