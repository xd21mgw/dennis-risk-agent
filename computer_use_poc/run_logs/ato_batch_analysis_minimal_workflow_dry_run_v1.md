# ATO Batch Analysis Minimal Workflow Dry-run v1

## 1. 测试目标

验证 Dennis Agent 是否能基于 5-20 个脱敏模拟 ATO case，完成最小闭环：

`case_registry → single case evidence card → batch pattern summary → missing evidence summary → candidate strategy direction → manual review boundary`

执行边界：

- real_platform_called: false
- dataagent_called: false
- release_package_updated: false
- outputs_dist_updated: false
- sensitive_plaintext_output: false
- auto_disposition: false
- auto_strategy_launch: false

## 2. Case Registry 摘要

- batch_id: `ato_batch_minimal_workflow_dry_run_v1`
- case_count: 10
- case_id_range: `dry_ato_001` ~ `dry_ato_010`
- entity_policy: all user_id / device_id are synthetic references

### 2.1 Case 类型分布

| case_type | count | case_ids |
|---|---:|---|
| 高疑似 ATO，多来源较完整 | 3 | dry_ato_001, dry_ato_002, dry_ato_003 |
| 证据不足，只有人工输入 | 2 | dry_ato_004, dry_ato_005 |
| 登录日志窗口不足 | 1 | dry_ato_006 |
| 设备关联异常 | 2 | dry_ato_007, dry_ato_008 |
| 反证或弱反证 | 1 | dry_ato_009 |
| partial / blocked source | 1 | dry_ato_010 |

### 2.2 核心实体字段覆盖

| field | coverage | gap |
|---|---:|---|
| case_id | 10/10 | none |
| user_id_ref | 10/10 | synthetic only |
| event_time | 9/10 | dry_ato_005 缺精确时间 |
| abnormal_action | 10/10 | none |
| device_id_ref | 6/10 | dry_ato_004, dry_ato_005, dry_ato_006, dry_ato_009 缺设备 |
| available_evidence | 10/10 | source strength varies |
| evidence_source metadata | 10/10 | none |

## 3. 单 Case Evidence Card 摘要

### dry_ato_001: 高疑似 ATO，多来源完整

- conclusion_support_level: `strong_support`
- strong_evidence:
  - 异设备登录后 5 分钟内异常发布。
    - evidence_source: internal_platform_api / login_log_read
    - source_quality: fresh, success, high
  - 发布 UA 与常用客户端不一致。
    - evidence_source: internal_platform_api / publish_audit
    - source_quality: fresh, success, high
- medium_evidence:
  - 设备侧代理 / hook 风险标签。
    - evidence_source: browser_dom_read / device_risk_read
    - source_quality: current_profile, success, medium
- weak_evidence:
  - 用户称非本人操作。
    - evidence_source: manual_input / case_intake
    - source_quality: manual_input_only, low
- counter_evidence: none observed
- missing_evidence:
  - token refresh chain

### dry_ato_002: 高疑似 ATO，OAuth 授权路径

- conclusion_support_level: `strong_support`
- strong_evidence:
  - 异常 OAuth app 授权后出现非本人私信。
    - evidence_source: internal_platform_api / oauth_authorization_read
    - source_quality: fresh, success, high
  - 私信对象集中且与历史行为不一致。
    - evidence_source: dataagent_hive / behavior_aggregate
    - source_quality: batch_authorized_simulated, success, high
- medium_evidence:
  - 登录 IP 与历史 IP 段突变。
    - evidence_source: internal_platform_api / login_log_read
    - source_quality: fresh, success, medium
- weak_evidence:
  - 客服备注疑似活动页钓鱼。
    - evidence_source: manual_input
    - source_quality: low
- counter_evidence: none observed
- missing_evidence:
  - OAuth scope 使用明细

### dry_ato_003: 高疑似 ATO，改密 / 改资料链路

- conclusion_support_level: `strong_support`
- strong_evidence:
  - 新设备登录后短时间改密。
    - evidence_source: internal_platform_api / login_log_read + account_security_log
    - source_quality: fresh, success, high
  - 改密后修改头像 / 简介 / 私信设置。
    - evidence_source: internal_platform_api / profile_change_log
    - source_quality: fresh, success, high
- medium_evidence:
  - 设备与多个被盗样本共享 IP 网段。
    - evidence_source: dataagent_hive / infra_aggregate
    - source_quality: simulated_aggregate, success, medium
- weak_evidence:
  - 用户申诉账号被盗。
    - evidence_source: manual_input
    - source_quality: low
- counter_evidence: none observed
- missing_evidence:
  - passToken / token 使用链路

### dry_ato_004: 证据不足，只有用户反馈

- conclusion_support_level: `insufficient_support`
- strong_evidence: none
- medium_evidence: none
- weak_evidence:
  - 用户称账号莫名发布作品。
    - evidence_source: manual_input
    - source_quality: low, manual_input_only
- counter_evidence: none
- missing_evidence:
  - 登录日志
  - 发布审计
  - 设备风险
  - token / OAuth 使用链路
- boundary: manual_input 不能单独支撑 strong conclusion

### dry_ato_005: 证据不足，人工备注疑似钓鱼

- conclusion_support_level: `needs_evidence`
- strong_evidence: none
- medium_evidence: none
- weak_evidence:
  - 人工备注写“疑似钓鱼链接”。
    - evidence_source: manual_input
    - source_quality: low
  - model 推断可能存在 token 复用。
    - evidence_source: model_inference
    - source_quality: model_inference_only
- counter_evidence: none
- missing_evidence:
  - event_time
  - token / OAuth 链路
  - 登录日志
  - 发布审计
- boundary: model_inference 只能作为 hypothesis，不能当 raw evidence

### dry_ato_006: 登录日志窗口不足

- conclusion_support_level: `partial_support`
- strong_evidence:
  - 发布审计显示异常 UA 发布。
    - evidence_source: internal_platform_api / publish_audit
    - source_quality: fresh, success, high
- medium_evidence:
  - 用户历史行为与异常发布差异明显。
    - evidence_source: dataagent_hive / behavior_history
    - source_quality: simulated_aggregate, success, medium
- weak_evidence:
  - 用户称非本人操作。
    - evidence_source: manual_input
    - source_quality: low
- counter_evidence:
  - login_log_no_data: false_as_counter
- missing_evidence:
  - offline_hive_login_log
- freshness_risk:
  - login_log_window_incomplete: true
  - offline_hive_required: true
  - over_window_no_data_not_counter_evidence: true

### dry_ato_007: 设备关联异常

- conclusion_support_level: `partial_support`
- strong_evidence: none
- medium_evidence:
  - 同一风险设备族关联多个异常用户。
    - evidence_source: internal_platform_api / user_device_resolution
    - source_quality: current_graph, success, medium
  - 设备存在代理 / root 标签。
    - evidence_source: browser_dom_read / device_risk_read
    - source_quality: current_profile, success, medium
- weak_evidence:
  - 用户申诉非本人登录。
    - evidence_source: manual_input
    - source_quality: low
- counter_evidence: none
- missing_evidence:
  - 控制权变化动作
  - 登录成功链路
- boundary: 设备关联只能作为关联风险证据，不能直接定性作弊或盗号

### dry_ato_008: 设备关联异常 + 后置关注

- conclusion_support_level: `partial_support`
- strong_evidence: none
- medium_evidence:
  - 风险设备关联两个异常用户。
    - evidence_source: internal_platform_api / weapon_graph
    - source_quality: current_graph, success, medium
  - 异常关注对象聚集。
    - evidence_source: dataagent_hive / behavior_aggregate
    - source_quality: simulated_aggregate, success, medium
- weak_evidence:
  - model 推断可能是批量接管后关注。
    - evidence_source: model_inference
    - source_quality: model_inference_only
- counter_evidence: none
- missing_evidence:
  - 登录链路
  - token / OAuth 链路
- boundary: 后置关注不能直接等同 ATO 主因

### dry_ato_009: 反证或弱反证 case

- conclusion_support_level: `counter_evidence_present`
- strong_evidence: none
- medium_evidence: none
- weak_evidence:
  - 用户称非本人。
    - evidence_source: manual_input
    - source_quality: low
- counter_evidence:
  - 操作来自本人常用设备与常用 IP，历史行为连续。
    - evidence_source: internal_platform_api / login_log_read + profile_history
    - source_quality: fresh, success, high
  - 无关键敏感动作，只有普通浏览。
    - evidence_source: internal_platform_api / behavior_log
    - source_quality: fresh, success, high
- missing_evidence:
  - none critical
- boundary: 该 case 暂不建议按 ATO 处理

### dry_ato_010: partial / blocked source

- conclusion_support_level: `partial_support`
- strong_evidence: none
- medium_evidence:
  - 档案显示近期风险状态变化。
    - evidence_source: internal_platform_api / user_profile_read
    - source_quality: fresh, success, medium
- weak_evidence:
  - 用户申诉非本人。
    - evidence_source: manual_input
    - source_quality: low
- blocked_or_partial_sources:
  - strategy_hit_read:
      permission_status: permission_blocked
  - login_log_read:
      permission_status: partial
- missing_evidence:
  - strategy_hit_observation
  - complete_login_window
  - token / OAuth 链路
- boundary: blocked source 不能写成 no_data；结论必须降级

## 4. Batch Pattern Summary

### 4.1 Case 聚类结果

| cluster_id | cluster_name | case_ids | cluster_reason | confidence |
|---|---|---|---|---|
| cluster_1 | high_suspicion_control_change | dry_ato_001, dry_ato_002, dry_ato_003 | 多来源证据支持控制权异常和后置敏感动作 | high |
| cluster_2 | insufficient_or_manual_only | dry_ato_004, dry_ato_005 | 只有人工输入或模型推断 | low |
| cluster_3 | window_or_source_gap | dry_ato_006, dry_ato_010 | 登录窗口不足或来源 partial/blocked | medium-low |
| cluster_4 | device_relation_suspicion | dry_ato_007, dry_ato_008 | 设备关联风险明显但控制权链路未闭合 | medium |
| cluster_5 | counter_evidence | dry_ato_009 | 存在常用设备和历史连续性反证 | low_ato_support |

### 4.2 共性实体模式

- 高疑似 case 共同点：异常登录 / 授权 / 改密后短时间出现发布、私信、改资料等敏感动作。
- 设备关联 case 共同点：风险设备或设备族关联多个异常用户，但缺少控制权变化闭环。
- 证据不足 case 共同点：人工输入多，平台 / Hive / API observation 缺失。

### 4.3 共性设备 / IP / 登录模式

- 部分高疑似 case 出现 IP / UA / device 与历史习惯断裂。
- 设备关联 case 出现风险设备族聚集。
- 登录日志超窗 case 必须转 offline Hive，不使用 no_data 做反证。

### 4.4 共性行为路径

- 异常登录 / OAuth / 改密后出现发布、私信、关注、改资料。
- 后置动作需要回连到账号控制权异常，不能直接作为 ATO 主因。

### 4.5 共性缺口

- token / passToken / OAuth 使用链路。
- 离线 Hive 登录日志。
- 发布审计和行为对象聚集。
- 被 blocked 的策略命中来源。
- 设备关联是否为正常共用、回收或攻击基础设施。

### 4.6 可疑攻击路径假设

| suspected_path | likelihood | supporting_cases | missing_or_boundary |
|---|---|---|---|
| 新设备 / 异设备接管 | high | dry_ato_001, dry_ato_003 | 需要 token 链路补齐 |
| OAuth / 授权滥用 | high | dry_ato_002 | 需要 scope 使用明细 |
| token / cookie 复用 | medium | dry_ato_005, dry_ato_006 | dry_ato_005 只有推断，不能强判 |
| 设备风险关联接管 | medium | dry_ato_007, dry_ato_008 | 设备关联不是盗号定性 |
| 本人操作 / 证据不足 | medium | dry_ato_004, dry_ato_009 | dry_ato_009 反证较强 |

### 4.7 Confidence Level

- batch_confidence: `medium`
- high_suspicion_case_count: 3
- partial_support_case_count: 4
- insufficient_or_needs_evidence_count: 2
- counter_evidence_present_count: 1
- quality_risk: `source_coverage_varies`

## 5. Source Coverage Summary

| evidence_category | complete_source_cases | weak_source_only_cases | stale_or_window_risk_cases | partial_or_blocked_cases | conclusions_to_downgrade |
|---|---|---|---|---|---|
| 登录链路 | dry_ato_001, dry_ato_003, dry_ato_009 | dry_ato_004, dry_ato_005 | dry_ato_006 | dry_ato_010 | dry_ato_006, dry_ato_010 |
| OAuth / token | dry_ato_002 | dry_ato_005 | none | dry_ato_010 | dry_ato_005, dry_ato_010 |
| 发布 / 私信 / 关注 | dry_ato_001, dry_ato_002, dry_ato_003, dry_ato_008 | dry_ato_004 | none | none | dry_ato_004 |
| 设备风险 / 关联 | dry_ato_001, dry_ato_007, dry_ato_008 | none | none | none | dry_ato_007, dry_ato_008 because association is not conclusion |
| 策略命中 | none | none | none | dry_ato_010 | dry_ato_010 |

source_trace_check:

- evidence_source present: pass
- source_quality present: pass
- source_coverage_summary present: pass
- model_inference labeled: pass
- manual_input not used as strong evidence: pass
- over-window no_data not used as counter evidence: pass
- partial / blocked source visible: pass

## 6. Candidate Strategy Direction

以下只作为候选策略方向，不是自动上线结论：

1. 异设备登录 / OAuth 授权后短时间敏感动作组合监控。
   - 误伤风险：换机、正常授权、家庭共用。
   - 补证建议：token / OAuth 使用链路、发布审计、历史行为连续性。
2. 改密 / 改资料 / 私信设置变更后的后置异常动作识别。
   - 误伤风险：用户主动改资料、正常安全操作。
   - 补证建议：登录来源、设备可信度、用户历史操作模式。
3. 风险设备族关联多个异常用户的人工复核队列。
   - 误伤风险：二手设备、家庭共用、测试设备。
   - 补证建议：控制权变化链路、行为对象聚集、设备使用时间线。
4. 登录日志超窗 case 的 offline Hive 补证流程。
   - 误伤风险：在线日志缺口被误当反证。
   - 补证建议：离线登录、token、发布审计、行为日志。

AB / 查杀分离 / 人工复核建议：

- 先做 observation-only 灰度，不直接处置。
- 高疑似 cluster 进入人工复核优先队列。
- 设备关联 cluster 只做候选关联，不做自动查杀。
- 证据不足 cluster 先补 P0 evidence。
- 反证 cluster 暂不建议处置。

## 7. Manual Review Boundary

### 7.1 高优先级人工复核

- dry_ato_001
- dry_ato_002
- dry_ato_003

原因：多来源证据完整，存在控制权异常与后置敏感动作。

### 7.2 需要补数据后再判断

- dry_ato_004
- dry_ato_005
- dry_ato_006
- dry_ato_010

原因：manual/model/window/permission gap 明显。

### 7.3 暂不建议处置

- dry_ato_007
- dry_ato_008
- dry_ato_009

原因：

- dry_ato_007 / dry_ato_008 只有设备关联风险，缺控制权变化闭环。
- dry_ato_009 有较强正常反证。

### 7.4 需要 DataAgent / Hive 离线补查

- dry_ato_002：行为对象聚集和 OAuth 使用链路。
- dry_ato_003：设备 / IP 聚合和 token 链路。
- dry_ato_006：离线登录日志。
- dry_ato_008：关注对象聚集。
- dry_ato_010：完整登录窗口和策略命中补证。

DataAgent 边界：

- 只作为 Hive / 数仓取数分析能力。
- 需要明确问题、字段、时间窗口、脱敏输出。
- 不自动处置，不自动上线策略。

## 8. Failed / Risk Items

- source_trace_missing: false
- strong_conclusion_from_weak_source: false
- model_inference_as_raw_evidence: false
- manual_input_as_strong_conclusion: false
- over_window_no_data_as_counter_evidence: false
- device_association_as_cheating_conclusion: false
- strategy_direction_overreach: false

## 9. Dry-run Conclusion

- dry_run_result: pass
- minimal_workflow_closed: true
- case_registry_supported: true
- evidence_card_supported: true
- pattern_summary_supported: true
- source_coverage_supported: true
- candidate_strategy_direction_supported: true
- manual_review_boundary_supported: true
- real_query_triggered: false
- release_package_updated: false

本轮 dry-run 表明：ATO batch case management 可以在脱敏模拟 case 上完成最小闭环。下一步如果进入真实 runtime，应优先验证 evidence_source / source_quality 是否能由真实 observation pipeline 自动填充。
