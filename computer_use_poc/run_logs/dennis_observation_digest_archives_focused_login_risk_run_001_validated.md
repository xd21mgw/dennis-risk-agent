# Dennis Observation Digest Archives Focused Login Risk Run 001

## 1. 测试目标

验证 Dennis Agent 是否能消化内部 Agent 返回的档案中心 `focused_login_risk` observation，并输出证据总结、风险线索、证据强弱、证据缺口和下一步平台建议。

## 2. 输入

```yaml
input_observation_source: archives_center focused_login_risk risk_event_scan
observation_status: validated
source_type: single_source
```

## 3. 输出章节

Dennis Agent 已输出：

- `evidence_summary`
- `risk_relevant_findings`
- `evidence_strength`
- `counter_evidence_or_downgrade_factors`
- `limitations`
- `missing_evidence`
- `next_suggested_platforms`
- `conclusion_boundary`

## 4. 验证结果

```yaml
validation_result: passed
```

通过项：

- 未直接定性盗号 / 协议上号 / 账号接管。
- 未建议处罚。
- 未输出敏感明文。
- 明确档案中心用户分析日志不能替代统一登录全量日志。
- 建议下一步优先查用户登录统一日志。
- 其次建议设备攻防平台。
- 再补用户行为细查 / 埋点。
- 保留“线索 / 证据 / 结论边界”三层区分。

## 5. 当前边界

本次仅验证单源 archives_center focused_login_risk observation digest。

不代表：

- 多源联合研判已完成。
- 自动风险定性已完成。
- Dennis Agent 可以直接操作内部平台。
- 可以跳过统一登录日志 / 设备平台补证。

