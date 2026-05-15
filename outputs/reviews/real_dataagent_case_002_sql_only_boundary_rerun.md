# Real DataAgent Case 002 Boundary Rerun - SQL-only

## 0. 回归目标

验证 Data Agent 只返回 SQL / 查询逻辑、没有真实执行结果时，SQL-only 不进入证据链，最终由 Dennis 主 Agent 输出“证据不足”。

约束：

- 不调用真实 Data Agent。
- 不编造真实 API、真实表名、真实字段名、真实 SQL。
- 不修改核心 Skill。

## 1. 用户问题

后端有请求、前端日志缺失，是否支持协议攻击嫌疑？

## 2. 模拟 Data Agent 返回摘要

```yaml
provider: dataagent_provider
status: success
returned_type: sql_only
result: success
queryId: mock_q_case_002_sql_only
sessionId: mock_sess_case_002_sql_only
streamEnd: true
error_msg: null
markdown_summary:
  - 仅返回查询 SQL / 查询逻辑。
  - 未返回真实执行结果。
  - 未返回数据发现。
  - 未返回样本统计。
  - 未返回覆盖数据域结果。
  - markdown 中有“可用以下查询逻辑验证前端缺失与后端请求关系”的结论性提示。
```

模拟 markdown 片段：

```text
查询理解：
用户希望判断后端有请求、前端日志缺失是否支持协议攻击嫌疑。

查询计划：
以下仅为脱敏伪 SQL / 查询逻辑，用于后续人工执行验证，不代表已查数结果。

SQL 参考：
-- 脱敏伪 SQL，仅展示逻辑结构，不代表真实表名、字段名或真实执行结果。
SELECT {抽象字段类型}
FROM {后端请求日志族}
LEFT JOIN {前端行为日志族}
  ON {抽象 join key}
WHERE {抽象时间窗与业务动作条件};

数据侧提示：
如果该查询执行后发现大量后端请求无前端匹配，可能支持协议攻击疑点。

重要说明：
SQL 不等于已查数结果。当前未执行查询，零数据证据。
```

## 3. parser 抽取结果

```yaml
parser_result:
  status: sql_only
  returned_type: sql_only
  key_findings: []
  strong_evidence: []
  medium_evidence: []
  weak_evidence: []
  missing_evidence:
    - SQL 未执行
    - 无真实查询结果
    - 无样本统计
    - 无数据域覆盖结果
    - 无破解包 / 官方埋点 / join 口径 / 合法自动化 / 群控真机反证
  quality_risks:
    - SQL-only 不等于已查数结果
    - 查询逻辑未经执行验证
    - markdown 中假设性分析可能误导判断
  raw_result_reference:
    provider: dataagent_provider
    queryId: mock_q_case_002_sql_only
    sessionId: mock_sess_case_002_sql_only
    reference_strength: weak
    replay_supported: false
```

## 4. provider_conclusion_hint

```yaml
provider_conclusion_hint:
  text: 如果该查询执行后发现大量后端请求无前端匹配，可能支持协议攻击疑点。
  source_section: 数据侧提示
  confidence_words:
    - 如果
    - 可能
  boundary_note: 该提示基于未执行 SQL 的假设推理，不是数据发现，也不是最终判断。
```

检查结果：通过。provider hint 未进入证据链。

## 5. unified_normalized_evidence

```yaml
unified_normalized_evidence:
  provider: dataagent_provider
  provider_response_id: mock_q_case_002_sql_only
  status: sql_only
  returned_type: sql_only
  evidence_summary: Data Agent 仅返回脱敏查询逻辑，未返回真实执行结果。
  key_findings: []
  strong_evidence: []
  medium_evidence: []
  weak_evidence: []
  counter_evidence: []
  missing_evidence:
    - 查询未执行
    - 无真实数据发现
    - 无前端行为覆盖结果
    - 无后端请求统计结果
    - 无设备 / SDK / 指纹结果
    - 无策略引擎结果
    - 无关联网络和授权运营反证
  quality_risks:
    - dataagent_sql_not_result
    - sql_only_pending_execution
    - zero_reliable_data
  provider_limitations:
    - dataagent_sql_not_result
    - dataagent_markdown_not_structured
    - dataagent_offline_not_realtime
  provider_conclusion_hint:
    text: 如果执行后发现大量后端请求无前端匹配，可能支持协议攻击疑点。
    boundary_note: provider hint only; not evidence.
  conclusion_support:
    level: insufficient_support
    reason: SQL 未执行，零真实数据证据。
  recommended_next_provider:
    generated_by: router_or_dennis_agent
    providers: []
  next_action:
    generated_by: router_or_dennis_agent
    actions:
      - 执行 SQL 或让 Data Agent 返回真实查询结果。
      - 补充可查数据源覆盖范围。
      - 获得真实数据后再进入 parser 解析。
  manual_review_required: true
  raw_result_reference:
    provider: dataagent_provider
    queryId: mock_q_case_002_sql_only
    sessionId: mock_sess_case_002_sql_only
    reference_strength: weak
    replay_supported: false
```

`unified_normalized_evidence` 不包含 `dennis_final_judgement`。

## 6. dennis_final_judgement

```yaml
dennis_final_judgement:
  generated_by: Dennis 主 Agent
  judgement_level: 证据不足
  one_sentence_judgement: 当前只有 SQL 查询计划，没有真实数据结果，不能支持协议攻击判断。
  reason:
    - SQL-only 不等于已查数结果。
    - 没有 key_findings。
    - 没有 strong / medium / weak evidence。
    - 没有反证排除。
    - Data Agent 的“可能支持协议疑点”只是 provider_conclusion_hint。
  governance_boundary:
    - 不处罚
    - 不冻结
    - 不扣除
    - 不上线策略
```

## 7. recommended_next_provider / next_action

本 case 不优先切 provider，优先执行查询计划或获取真实 Data Agent 查询结果。

```yaml
next_action:
  generated_by: Router / Dennis Agent
  actions:
    - 执行 SQL / 获取真实 Data Agent 查询结果。
    - 补充 Data Agent 可查询数据源覆盖情况。
    - 若后续需要实时链路，再转 realtime_log_provider。
```

## 8. 是否正确降级

通过。

SQL-only 被标记为 `sql_only / pending_execution`，没有进入证据链，最终判断为证据不足。

## 9. 是否有任何越界问题

未发现越界：

- Data Agent hint 未进入 final judgement。
- SQL 未进入 strong / medium / weak evidence。
- recommended_next_provider / next_action 由 Router / Dennis Agent 生成。
- 没有自动治理建议。

## 10. 是否需要回写 parser / mapping / overlay 文档

暂不需要。现有边界规则已覆盖 SQL-only。

