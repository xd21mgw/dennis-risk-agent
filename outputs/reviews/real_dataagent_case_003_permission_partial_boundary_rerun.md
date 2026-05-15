# Real DataAgent Case 003 Boundary Rerun - No Permission / Partial

## 0. 回归目标

验证 Data Agent 返回 no_permission / partial 时，权限不足和关键数据域缺失能被正确降级，Data Agent 结论性文字只进入 `provider_conclusion_hint`，最终判断由 Dennis 主 Agent 生成。

约束：

- 不调用真实 Data Agent。
- 不编造真实 API、真实表名、真实字段名、真实 SQL。
- 不修改核心 Skill。

## 1. 用户问题

后端有请求、前端日志缺失，是否支持协议攻击嫌疑？

## 2. 模拟 Data Agent 返回摘要

```yaml
provider: dataagent_provider
status: no_permission
returned_type: partial_table + permission_blocked
result: error
queryId: mock_q_case_003_permission_partial
sessionId: mock_sess_case_003_permission_partial
streamEnd: true
error_msg: 权限不足：前端行为域、策略引擎域、关联网络域、授权运营域部分数据不可访问。
visible_domains:
  - 后端请求域部分聚合
  - 设备 / SDK / 指纹域部分聚合
blocked_or_partial_domains:
  - 前端行为域无权限或仅聚合口径
  - 策略引擎域无权限
  - 关联网络域无权限
  - 授权运营域无权限
markdown_summary:
  - 后端请求域可见部分聚集。
  - 设备 / SDK / 指纹域仅部分覆盖。
  - Data Agent 原文提示“存在协议攻击疑点”。
  - 多个关键反证路径无权限或未覆盖。
```

模拟 markdown 片段：

```text
查询理解：
用户希望判断后端有请求、前端日志缺失是否支持协议攻击嫌疑。

数据发现：
后端请求域可见目标业务动作存在请求聚集。
设备 / SDK / 指纹域仅部分覆盖，可见少量 SDK 状态异常线索。

权限限制：
前端行为域明细不可访问，只能看到部分聚合口径。
策略引擎域无权限，无法确认命中、拦截、放行或灰度。
关联网络域无权限，无法排除群控真机。
授权运营域无权限，无法排除合法自动化或授权工具。

数据侧提示：
从已查后端请求和部分 SDK 异常看，存在协议攻击疑点。

重要说明：
由于关键域无权限，无法确认前端真实无日志，也无法排除官方埋点缺失、join 口径、合法自动化和群控真机。不能强结论。
```

## 3. parser 抽取结果

```yaml
parser_result:
  status: no_permission
  returned_type: partial_table + permission_blocked
  key_findings:
    - 后端请求域可见目标业务动作存在请求聚集。
    - 设备 / SDK / 指纹域仅部分覆盖，存在少量 SDK 状态异常线索。
    - 前端行为域无权限或仅聚合口径。
    - 策略引擎域无权限。
    - 关联网络域无权限。
    - 授权运营域无权限。
  strong_evidence: []
  medium_evidence:
    - 后端请求聚集。
    - 部分 SDK 状态异常线索。
  weak_evidence:
    - Data Agent 原文“存在协议攻击疑点”仅为 provider hint。
  counter_evidence:
    - 官方包埋点缺失。
    - 前后端 join 口径偏差。
    - 合法自动化 / 授权工具。
    - 群控真机。
  missing_evidence:
    - 前端行为域明细。
    - 策略引擎命中 / 处置链路。
    - 关联网络 / 群控标签。
    - 授权运营白名单。
    - 精确 join 口径验证。
  quality_risks:
    - 权限不足。
    - 前端口径不完整。
    - 关键反证未覆盖。
    - Data Agent-only 缺 realtime / risk engine / relation graph。
```

## 4. provider_conclusion_hint

```yaml
provider_conclusion_hint:
  text: 从已查后端请求和部分 SDK 异常看，存在协议攻击疑点。
  source_section: 数据侧提示
  confidence_words:
    - 疑点
  conflicts_with_missing_evidence: true
  conflicts_with_counter_evidence: true
  boundary_note: 该提示受权限不足和关键反证缺失影响，不是最终判断。
```

检查结果：通过。Data Agent 结论性文字只进入 provider hint。

## 5. unified_normalized_evidence

```yaml
unified_normalized_evidence:
  provider: dataagent_provider
  provider_response_id: mock_q_case_003_permission_partial
  status: no_permission
  returned_type: partial_table + permission_blocked
  evidence_summary: Data Agent 仅能看到后端请求部分聚集和部分 SDK 异常，多个核心域无权限。
  key_findings:
    - 后端请求域可见目标业务动作存在请求聚集。
    - 设备 / SDK / 指纹域仅部分覆盖。
    - 前端行为域无权限或仅聚合口径。
    - 策略引擎域、关联网络域、授权运营域无权限。
  strong_evidence: []
  medium_evidence:
    - evidence: 后端请求聚集
      reason: 支持存在请求异常线索，但不证明协议攻击。
    - evidence: 部分 SDK 状态异常
      reason: 支持采集异常线索，但原因未闭合。
  weak_evidence:
    - evidence: provider_conclusion_hint 中的协议疑点
      reason: Data Agent 数据侧提示，不是事实证据。
  counter_evidence:
    - 官方包埋点缺失
    - 前后端 join 口径偏差
    - 合法自动化 / 授权工具
    - 群控真机
  missing_evidence:
    - 前端行为域明细
    - 实时前端日志
    - NG 网关明细
    - 策略引擎命中 / 处置链路
    - 关联网络 / 群控标签
    - 授权运营白名单
    - 精确 join 口径验证
  quality_risks:
    - no_permission
    - 前端口径不完整
    - 关键反证未覆盖
    - 权限不足导致结论强度受限
  provider_limitations:
    - dataagent_markdown_not_structured
    - dataagent_offline_not_realtime
    - permission_limited
    - missing_realtime_log_provider
    - missing_risk_engine_provider
    - missing_relation_graph_provider
    - missing_authorization_data
  provider_conclusion_hint:
    text: 存在协议攻击疑点
    boundary_note: provider hint only; not final judgement.
  conclusion_support:
    level: insufficient_support
    reason: no_permission / partial，关键反证未覆盖，不能确认协议攻击。
  recommended_next_provider:
    generated_by: router_or_dennis_agent
    providers:
      - permission_request
      - realtime_log_provider
      - risk_engine_provider
      - relation_graph_provider
      - manual_review_provider
  manual_review_required: true
  raw_result_reference:
    provider: dataagent_provider
    queryId: mock_q_case_003_permission_partial
    sessionId: mock_sess_case_003_permission_partial
    reference_strength: weak
    replay_supported: false
```

`unified_normalized_evidence` 不包含 `dennis_final_judgement`。

## 6. dennis_final_judgement

```yaml
dennis_final_judgement:
  generated_by: Dennis 主 Agent
  judgement_level: 证据不足
  local_path_hint: 局部存在协议 / SDK 异常疑点，但整体证据不足
  one_sentence_judgement: 当前只能说明后端请求和部分 SDK 异常存在疑点，因前端、策略、关系和授权域无权限，不能明确协议攻击。
  reason:
    - 后端请求聚集不是协议攻击充分条件。
    - 部分 SDK 异常可能来自官方埋点缺失、版本差异或采集延迟。
    - 前端行为域无权限，无法确认前端真实无日志。
    - 策略引擎域无权限，无法确认命中 / 拦截 / 放行。
    - 关联网络和授权运营无权限，无法排除群控真机和合法自动化。
    - Data Agent 的协议疑点只属于 provider_conclusion_hint。
  governance_boundary:
    - 不处罚
    - 不冻结
    - 不扣除
    - 不上线策略
```

## 7. recommended_next_provider / next_action

由 Router / Dennis Agent 生成：

```yaml
recommended_next_provider:
  - permission_request
  - realtime_log_provider
  - risk_engine_provider
  - relation_graph_provider
  - manual_review_provider
next_action:
  - 申请前端行为域、策略引擎域、关联网络域、授权运营域只读权限。
  - 权限补齐后重跑 Data Agent 取证。
  - 接入 realtime_log_provider 补实时前后端链路和 NG 明细。
  - 接入 risk_engine_provider 补策略命中和处置链路。
  - 接入 relation_graph_provider 补群控真机和关系网络。
  - 人工确认授权工具 / 合法自动化边界。
```

## 8. 是否正确降级

通过。

no_permission / partial 被降级为证据不足；局部疑点没有升级为明确协议。

## 9. 是否有任何越界问题

未发现越界：

- Data Agent hint 未进入 final judgement。
- `unified_normalized_evidence` 不包含 `dennis_final_judgement`。
- recommended_next_provider 由 Router / Dennis Agent 生成。
- 缺权限和 partial 没有被强行解释为协议攻击。

## 10. 是否需要回写 parser / mapping / overlay 文档

暂不需要。现有边界规则已覆盖 no_permission / partial。

