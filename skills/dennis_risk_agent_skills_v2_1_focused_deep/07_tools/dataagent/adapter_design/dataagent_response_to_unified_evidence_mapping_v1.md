# DataAgent Response to Unified Evidence Mapping v1

## 0. 目标

本文件定义 Data Agent 返回内容如何映射到 `unified_normalized_evidence`。

Data Agent 是 evidence provider，不是 final judgement owner。

## 1. 字段流转

```text
Data Agent markdown
→ parser
→ unified_normalized_evidence
→ Router / Dennis Agent
→ dennis_final_judgement
```

## 2. 映射结构

```yaml
unified_normalized_evidence:
  provider: dataagent_provider
  provider_response_id: queryId
  status:
  returned_type:
  evidence_summary:
  key_findings:
  strong_evidence:
  medium_evidence:
  weak_evidence:
  counter_evidence:
  missing_evidence:
  quality_risks:
  provider_limitations:
  provider_conclusion_hint:
  conclusion_support:
    level:
    reason:
  recommended_next_provider:
    generated_by: router_or_dennis_agent
    basis:
      - missing_evidence
      - provider_limitations
  manual_review_required:
  raw_result_reference:
  dennis_final_judgement:
    generated_by: Dennis 主 Agent
    filled_by_dataagent: false
    filled_by_parser: false
```

## 3. provider_conclusion_hint

`provider_conclusion_hint` 用于承接 Data Agent markdown 中的结论性文字。

进入该字段的内容：

- “高度疑似”
- “可能是”
- “建议判断为”
- “当前看更像”
- “数据上支持某路径”
- “无法判断”
- “证据不足”

约束：

- 只能作为 provider hint。
- 不得进入 `dennis_final_judgement`。
- 不得直接进入治理动作。
- 不得覆盖 missing evidence。
- 不得绕过 counter evidence。
- 不得把 markdown 推测变成事实。

## 4. dennis_final_judgement

`dennis_final_judgement` 不得由 Data Agent 直接填充。

生成方：

- Dennis 主 Agent。

生成依据：

- normalized evidence。
- Skill 判断规则。
- 反证和误判风险。
- 业务上下文。
- 人工复核。

## 5. recommended_next_provider

`recommended_next_provider` 由 Router / Dennis Agent 生成。

Data Agent 可以输出：

- 缺少实时日志。
- 缺少策略引擎记录。
- 缺少群控标签。
- 缺少授权工具白名单。
- 缺少口径验证。

Router / Dennis Agent 再映射为：

- `realtime_log_provider`
- `risk_engine_provider`
- `relation_graph_provider`
- `manual_review_provider`
- `device_fingerprint_provider`

Data Agent 原文中的“下一步建议”只能作为 missing evidence 或 next action hint 的参考。

## 6. 典型映射

| Data Agent 返回内容 | parser 映射字段 | 注意 |
|---|---|---|
| 数据表格 / 数据摘要 | key_findings / evidence | 需检查口径和覆盖范围 |
| SQL-only | weak_evidence 或 query_plan_hint | 不等于已查数 |
| “高度疑似协议” | provider_conclusion_hint | 不得作为 final judgement |
| “缺少策略引擎” | missing_evidence | Router 决定是否推荐 risk_engine_provider |
| “无权限” | permission_notes / quality_risks | 必须降级 |
| “返回 0 行” | status=empty_result | 不等于无风险 |
| “可能是 join 口径问题” | counter_evidence / quality_risks | 反证未闭合 |

## 7. 禁止映射

- 禁止把 Data Agent 的结论性文字映射为 `dennis_final_judgement`。
- 禁止让 Data Agent 原文直接决定 `recommended_next_provider`。
- 禁止把 SQL-only 映射为 strong evidence。
- 禁止把 empty_result 映射为无风险。
- 禁止把 no_permission 映射为证据排除。

