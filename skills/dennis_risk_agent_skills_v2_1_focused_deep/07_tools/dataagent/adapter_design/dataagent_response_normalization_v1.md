# DataAgent Response Normalization v1

## 0. 定位

本文件说明未来 `dataagent_response` 如何标准化为 Dennis 风控 Agent 可解释的 `normalized_evidence`。

当前阶段不调用真实 Data Agent，不模拟真实结果，不编造真实表名、字段名、SQL、API、看板、实验或画像标签。

## 1. 输入与输出

输入：

```yaml
dataagent_response:
  request_meta:
  returned_type:
  status:
  result_summary:
  quality_and_limits:
  interpretation_hints:
  recommended_next_queries:
```

输出：

```yaml
normalized_evidence:
  evidence_id:
  source_query_intent_id:
  source_dataagent_request_id:
  status:
  evidence_type:
  evidence_summary:
  strong_evidence:
  medium_evidence:
  weak_evidence:
  counter_evidence:
  missing_evidence:
  quality_risks:
  conclusion_support:
  next_query_intent:
```

## 2. 支持的 returned_type

必须覆盖：

- `sql`
- `table_summary`
- `dashboard_analysis`
- `dataset_analysis`
- `abtest_analysis`
- `profile_tags`
- `audience_package`
- `error`
- `partial`
- `no_permission`

## 3. success 处理

当 `status: success`：

1. 将结果摘要转成 `evidence_summary`。
2. 按 `query_intent.interpretation_notes` 分桶为强证据、中证据、弱证据和反证。
3. 将 Data Agent 返回的口径、覆盖率、延迟、权限、样本偏差写入 `quality_risks`。
4. 按 `query_intent.conclusion_threshold` 生成 `conclusion_support`。
5. 即使成功返回，也不能自动给出 Dennis Agent 最终判断。

成功返回仅表示“数据侧完成了查询或分析任务”，不表示风险成立。

## 4. partial 处理

当 `status: partial`：

- 必须保留已返回证据。
- 必须显式记录未返回证据。
- `conclusion_support.level` 最高只能到 `高度疑似`，如果关键反证或关键闭环缺失，应为 `证据不足`。
- 必须生成 `next_query_intent` 或人工补证动作。
- 不得进入自动处罚、冻结、扣除或策略上线。

## 5. failed 处理

当 `status: failed`：

- `evidence_summary` 只描述失败原因。
- `strong_evidence`、`medium_evidence` 应为空。
- 可保留失败前已知的弱信号，但必须标注不可用于强结论。
- `conclusion_support.level` 必须为 `证据不足`。
- 必须给出下一步：重试、补输入、换 task_type、人工查数或权限排查。

## 6. no_permission 处理

当 `status: no_permission`：

- 不得解释为“无风险”。
- 不得解释为“查无异常”。
- `conclusion_support.level` 必须为 `证据不足`。
- `permission_notes` 必须说明受限数据域或证据类型。
- 必须保留原 `query_intent`，供授权后重放。
- 是否需要人工确认应为 `true` 或 `待平台判断`。

## 7. empty_result 处理

空结果不等于无风险。

`empty_result` 需要区分：

- 查询条件过窄。
- 时间窗口错误。
- 数据延迟。
- 数据域选择错误。
- 权限过滤后为空。
- 真实没有记录。

只有当数据覆盖、权限、时间窗口、口径和样本范围均确认无误时，才可作为反向证据的一部分；仍需 Dennis Agent 结合业务反证解释。

## 8. returned_type 解释边界

### 8.1 sql

返回 SQL 或查询草案只说明“可以怎么查”，不代表已经查到结果。

归一化规则：

- 放入 `weak_evidence` 或 `missing_evidence`。
- `conclusion_support.level` 不得超过 `证据不足`。
- 下一步应为执行查询或获取真实结果。

### 8.2 table_summary

返回表或资产摘要只说明“可能有哪些数据来源”，不代表风险事实。

归一化规则：

- 写入 `evidence_summary` 和 `quality_risks`。
- 不应生成强证据。
- 下一步通常是 `data_query` 或 `dataset_analysis`。

### 8.3 dashboard_analysis

返回看板趋势不等于风险事实。

归一化规则：

- 趋势、波动、分布写入弱/中证据。
- 若只有指标异常，不能下黑产或作弊结论。
- 必须保留业务上下文、数据质量、实验、版本、策略反证。

### 8.4 dataset_analysis

返回数据集分析可支持分布、占比、后验质量和漏斗证据。

归一化规则：

- 若有风险链路和反证闭合，可成为中强证据。
- 若只有低质、低钱效或单点异常，最多弱证据或中证据。

### 8.5 abtest_analysis

AB 结果说明实验影响，不直接说明攻击。

归一化规则：

- 实验干扰可作为反证。
- 推全建议必须由 Dennis Agent 结合风险和业务边界解释。
- 实验差异不得直接触发风控处罚。

### 8.6 profile_tags

风险画像不等于事实标签。

归一化规则：

- 画像标签最多作为分层证据。
- 必须与行为、链路、收益或敏感动作结合。
- 单独画像标签不得给明确判断。

### 8.7 audience_package

人群圈选结果不等于处置人群。

归一化规则：

- 可作为候选样本或灰度分层。
- 不得直接进入处罚、冻结、扣除、封禁。
- 必须经过人工确认和治理策略评估。

### 8.8 error / partial / no_permission

这三类必须进入降级策略：

- `error`：证据不足。
- `partial`：按缺失证据降级。
- `no_permission`：证据不足并保留重放。

## 9. 关键解释禁令

- 返回 SQL 不等于已经查到结果。
- 返回看板趋势不等于风险事实。
- 返回风险画像不等于事实标签。
- 返回策略命中不等于风险真实发生。
- `empty_result` 不能直接解释为无风险。
- `partial`、`failed`、`no_permission` 不得支持明确判断。
- 缺少关键反证时，不得给强结论。
