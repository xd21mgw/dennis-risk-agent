# Provider Response Normalization Contract v1

## 0. 目标

本文件定义不同 provider 返回如何统一转为 `normalized_evidence`。当前阶段只定义归一化原则，不调用真实 provider，不编造返回结果。

## 1. 通用归一化流程

1. 识别 provider 和 response status。
2. 判断返回是否可解析。
3. 提取 key findings。
4. 提取 strong / medium / weak evidence。
5. 提取 counter evidence。
6. 提取 missing evidence。
7. 提取 quality risks。
8. 提取 freshness notes 和 permission notes。
9. 写入 provider limitations。
10. 生成 conclusion support，但不替代 Dennis Agent 最终判断。

## 2. dataagent_provider

输入可能包括：

- SSE markdown。
- SQL。
- table markdown。
- error_msg。
- queryId / sessionId。

处理规则：

- 经过 markdown parser。
- 提取 key findings。
- 提取 missing evidence。
- 提取 counter evidence。
- 提取 quality risks。
- 记录 queryId / sessionId 为弱引用。
- 不能把 SQL 当结果。
- 不能把 markdown 推测当事实。
- partial markdown 需要降级。
- 无权限或空结果不得解释为无风险。

## 3. realtime_log_provider

输入可能包括：

- 结构化日志结果。
- 命中明细。
- 聚合结果。
- 无结果。
- 超时。
- 权限错误。

处理规则：

- 标准化为链路一致性、请求序列、日志缺失、接口异常等证据。
- 记录日志延迟、采样、join 口径风险。
- 无前端日志不得直接转为协议强证据。
- 后端有请求但前端无日志时，必须保留破解包、埋点缺失、join 口径问题等反证缺口。

## 4. risk_engine_provider

输入可能包括：

- 策略命中。
- 风险分。
- 处置动作。
- 灰度分组。
- 返回码。
- 命中规则链路。

处理规则：

- 标准化为策略证据。
- 标明“策略命中不等于风险事实”。
- 风险分和处置动作只说明策略决策发生。
- 需要结合后验结果、行为证据或人工复核。

## 5. device_fingerprint_provider

输入可能包括：

- 指纹结果。
- SDK 状态。
- 设备画像。
- app 版本 / 签名。
- 环境异常。

处理规则：

- 标准化为设备证据。
- 标明采集延迟和 SDK 风险。
- SDK 缺失不能直接判破解包。
- 设备画像异常不能直接判群控。
- 实时指纹与异步 SDK 不一致时必须保留质量风险。

## 6. relation_graph_provider

输入可能包括：

- 团组。
- 强关联。
- 关系边。
- 聚集指标。
- 扩散路径。

处理规则：

- 标准化为关系证据。
- 标明“关联不等于作恶”。
- 只有关系边不得输出强结论。
- 必须结合行为、收益、敏感动作或人工确认。

## 7. structured_sql_or_feature_provider

输入可能包括：

- 结构化表格。
- JSON。
- SQL result。
- feature result。

处理规则：

- 直接映射到 normalized evidence。
- 仍需要质量检查。
- 空结果不等于无风险。
- feature 过期或 schema 变化必须记录。

## 8. manual_review_provider

输入可能包括：

- 人工判断。
- 业务确认。
- 证据附件。
- 权限审批结果。
- 误伤复核意见。

处理规则：

- 标准化为人工证据。
- 记录人工判断依据。
- 记录复核人、复核时间和审计引用。
- 人工证据可以提高结论支持，但仍需 Dennis Agent 汇总解释。

## 9. 统一禁止

- 不得把 provider 原始文本硬解释成证据。
- 不得忽略 counter evidence。
- 不得把 no_permission、timeout、empty_result 转为无风险。
- 不得用单一 provider 结果替代最终风控判断。

