# Normalized Evidence Schema v1

## 0. 定位

`normalized_evidence` 是 Dennis 风控 Agent 消费 Data Agent 返回结果的标准证据对象。

它只表达“证据支持程度”，不直接替代 Dennis 风控 Agent 的最终判断。

## 1. 标准结构

```yaml
normalized_evidence:
  evidence_id: "<adapter 生成的证据标识>"
  source_query_intent_id: "<query_intent.intent_id>"
  source_dataagent_request_id: "<dataagent_request.request_id>"
  status: "<success | partial | failed | no_permission | timeout | empty_result | ambiguous_result | data_quality_risk | permission_limited>"
  evidence_type: "<target_evidence 或归一化证据类型>"
  applicable_skill:
    primary: "<主控 Skill>"
    auxiliary:
      - "<辅助 Skill>"
  evidence_summary: "<简要证据摘要，不含敏感明细>"
  key_findings:
    - finding: "<发现摘要>"
      finding_type: "<metric | trend | distribution | sample_summary | lineage | quality | permission | counter_evidence>"
      evidence_strength: "<strong | medium | weak | counter | missing>"
      caveat: "<解释限制>"
  strong_evidence:
    - "<强证据摘要>"
  medium_evidence:
    - "<中证据摘要>"
  weak_evidence:
    - "<弱证据摘要>"
  counter_evidence:
    - "<反证或业务合理解释>"
  missing_evidence:
    - "<缺失证据>"
  quality_risks:
    - "<口径、延迟、覆盖、样本偏差、join 风险、权限限制>"
  freshness_notes:
    expected: "<query_intent.freshness_expectation>"
    actual: "<未来平台返回的新鲜度语义>"
    impact: "<对结论的影响>"
  permission_notes:
    boundary: "<query_intent.permission_boundary>"
    access_status: "<allowed | permission_limited | no_permission | pending_approval | unknown>"
    restricted_evidence:
      - "<受限证据类型>"
  conclusion_support:
    level: "<明确判断 | 高度疑似 | 证据不足 | 反向排除/暂不支持>"
    reason: "<为什么当前证据最多支持该等级>"
    cannot_upgrade_because:
      - "<不能升档的原因>"
  next_query_intent:
    intent_type: "<下一步 query_intent_type>"
    target_evidence: "<下一步要补的证据>"
    reason: "<为什么需要下一步>"
  manual_review_required: "<true | false | 待平台判断>"
  raw_result_reference:
    reference_id: "<内部引用 id，不外泄敏感明细>"
    retention_policy: "<未来平台补充>"
    sensitive_detail_export_allowed: false
```

## 2. status 取值

- `success`：Data Agent 完成任务并返回可解释结果。
- `partial`：只返回部分结果，关键证据或反证有缺失。
- `failed`：任务失败。
- `no_permission`：无权限访问所需数据或资产。
- `timeout`：执行超时。
- `empty_result`：返回空结果，需要解释原因。
- `ambiguous_result`：结果方向不清或多种解释并存。
- `data_quality_risk`：数据口径、延迟、覆盖、join 或样本风险严重。
- `permission_limited`：部分数据可见，关键证据受限。

## 3. evidence_strength 规则

### 3.1 strong_evidence

只有同时满足以下条件，才能进入强证据：

- 与 `target_evidence` 直接相关。
- 与 `conclusion_threshold.must_combine_with` 中的关键证据形成闭环。
- 关键反证已返回且被排除。
- 质量风险不影响主结论。

### 3.2 medium_evidence

适用于：

- 多个信号同向，但缺少一两个闭环证据。
- 反证尚未完全排除。
- 数据质量可接受但仍有解释限制。

### 3.3 weak_evidence

适用于：

- 单点异常。
- 单一数据域信号。
- 画像、策略命中、指标波动、趋势异常。
- 查询计划、SQL 草案、表摘要等非结果型返回。

### 3.4 counter_evidence

适用于：

- 业务上下文能解释异常。
- 埋点缺失、口径差异、权限缺失、数据延迟可解释。
- 合法矩阵、授权工具、正常社交、自然传播、活动目标等反证成立。

## 4. conclusion_support 规则

`normalized_evidence.conclusion_support` 只表达“数据证据支持到什么程度”，不是 Dennis Agent 最终判断。

若存在以下任一情况，`level` 不得为 `明确判断`：

- `missing_evidence` 中包含关键闭环证据。
- `counter_evidence` 中存在未排除的关键反证。
- `status` 为 `partial`、`failed`、`no_permission`、`timeout`、`ambiguous_result`、`data_quality_risk` 或 `permission_limited`。
- 返回类型只是 `sql`、`table_summary`、`profile_tags` 或 `audience_package`。
- 只有风险画像或策略命中。
- 只有单点指标波动。

## 5. raw_result_reference 边界

`raw_result_reference` 只做内部引用：

- 不在 Dennis Agent 对用户的普通回答中外泄。
- 不包含真实用户、账号、设备、token、手机号或其他敏感明细。
- 不替代审计系统。
- 真实保留周期、脱敏规则和权限控制由未来内部平台补充。

## 6. 与 Dennis Agent 的关系

Dennis Agent 使用 `normalized_evidence` 做三件事：

1. 解释强/中/弱证据、反证和缺失证据。
2. 判断当前最多能支持的结论等级。
3. 生成下一步补证和治理建议。

Dennis Agent 不能把 `normalized_evidence` 直接当作处罚、冻结、扣除或策略上线指令。
