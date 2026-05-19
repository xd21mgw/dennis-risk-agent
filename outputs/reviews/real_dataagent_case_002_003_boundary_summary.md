# Real DataAgent Case 002 / 003 Boundary Summary

## 1. Case 002 是否通过

通过。

Case 002 验证了 SQL-only 返回：

- `status = sql_only`
- `returned_type = sql_only`
- SQL 只作为待执行查询计划。
- 不进入 strong / medium / weak evidence。
- `dennis_final_judgement = 证据不足`。
- next_action 为执行 SQL / 获取真实 Data Agent 查询结果 / 补充可查数据源。

## 2. Case 003 是否通过

通过。

Case 003 验证了 no_permission / partial 返回：

- 权限不足和部分覆盖被正确识别。
- 后端请求聚集和部分 SDK 异常只作为中弱证据。
- 缺失前端行为域、策略引擎域、关联网络域、授权运营域时，不能明确协议攻击。
- `dennis_final_judgement = 证据不足`，并标注局部疑点。

## 3. SQL-only 是否被阻止进入证据链

是。

SQL-only 被标记为：

- `sql_only`
- `pending_execution`
- `zero_reliable_data`

没有进入：

- strong_evidence
- medium_evidence
- weak_evidence

Data Agent 的“如果执行后可能支持协议疑点”只进入 `provider_conclusion_hint`。

## 4. no_permission / partial 是否正确降级

是。

降级原因：

- 前端行为域无权限或仅聚合口径。
- 策略引擎域无权限。
- 关联网络域无权限。
- 授权运营域无权限。
- 设备 / SDK / 指纹域仅部分覆盖。
- 关键反证未覆盖。

结论上限：

- 局部高度疑似可以作为路径提示。
- 整体为证据不足。
- 不得明确协议攻击。

## 5. provider_conclusion_hint 与 dennis_final_judgement 是否分离

是。

字段归属：

- Data Agent 结论性文字 -> `provider_conclusion_hint`
- Parser -> normalized evidence
- Router / Dennis Agent -> `recommended_next_provider`
- Dennis 主 Agent -> `dennis_final_judgement`

## 6. recommended_next_provider 是否由 Router / Dennis Agent 生成

是。

Case 002：

- 优先 next_action：执行 SQL / 获取真实查询结果。
- 如真实结果仍缺实时链路，再由 Router / Dennis Agent 推荐 provider。

Case 003：

- `permission_request`
- `realtime_log_provider`
- `risk_engine_provider`
- `relation_graph_provider`
- `manual_review_provider`

均由 Router / Dennis Agent 基于 missing_evidence 和 provider_limitations 生成。

## 7. 是否修改核心 Skill

否。本轮只新增回归输出文件。

