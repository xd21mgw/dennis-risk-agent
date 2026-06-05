# Fact Table Contract v1

Status: phase4_6_contract_only. This contract defines the structured fact
input layer used by Dennis batch commonality reasoning. It does not change
runtime execution, start browser-backed service, call platforms, call
DataAgent/Hive, or refresh outputs.

Purpose:

- Keep raw details available for controlled local trace-back without putting
  raw bodies into model context.
- Project raw details into safe structured records.
- Build analysis tables from projected records.
- Make batch commonality consume structured tables, not only compressed
  per-user observations.

## Data Flow

```text
raw_detail_retention_layer
-> safe_projected_records
-> standard_detail_table
-> strategy_event_feature_row_table
-> device_detail_table
-> anchor_table / feature_table / relation_table / source_quality_table
-> round_support_table / rolling_anchor_summary
-> commonality_matrix / group_profile_candidate / candidate_features
```

`per_user_observation` is an explanation artifact for humans. It may summarize
one sample, but it must not be the only fact source for batch commonality.

## Raw Detail Retention Layer

Raw detail retention is for controlled trace-back only.

Rules:

- Do not place raw body, upstream body, capped body, `logContent`, credential
  material, or full request/response envelopes in user-visible answers.
- Do not use raw retained data as the main batch commonality input.
- Keep only safe references, source ids, counts, field paths, and projected
  values that are necessary for evidence chaining.

## Standard Detail Table

Every projected field-level fact should be representable as:

```yaml
standard_detail_table:
  - sample_id:
    entity_id:
    entity_type:
    round_id:
    source_id:
    action:
    observation_domain:
    field_name:
    field_value_or_safe_ref:
    event_time:
    source_quality:
    evidence_source: current_observation | projected_record | fixture_mock
```

## Strategy Event Request Detail Table

Strategy event hits are entry signals, not core candidate features. Dennis must
prefer request-detail fields when mining strategy-side candidate features.

```yaml
strategy_event_request_detail_table:
  - sample_id:
    entity_id:
    user_id:
    round_id:
    source_id:
    action: rcp_event_detail | rcp_event_feature_list | rcp_fast_query_hbase
    observation_domain: strategy_domain
    event_id:
    event_type:             # entry / direction label only
    policy_code:            # entry / direction label only
    risk_decision:          # entry / direction label only
    event_time:
    request_path:
    request_scene:
    entry:
    action_type:
    action_object:
    task_type:
    reward_type:
    client_params:
    app_version:
    ua:
    device_id:
    ip_or_network:
    frontend_activity_signal:
    backend_action_signal:
    time_delta_from_login_seconds:
    time_delta_between_actions_seconds:
    missing_request_detail_fields: []  # request-detail fields absent from the safe projection
    entry_label_fields_only: false     # true when only policy/event/decision labels are available
    source_quality:
    evidence_source: current_observation | projected_record | fixture_mock
```

Candidate features from `strategy_domain` must cite request detail field
combinations such as request path, action object, entry, task type, reward type,
client parameters, frontend/backend activity signals, and time deltas.
`policy_code`, `event_type`, and `risk_decision` are allowed only as entry or
direction labels. If request detail fields are missing, Dennis should output a
missing-evidence item such as `strategy_event_request_detail_missing`; it must
not turn policy concentration into a core risk feature.

## Strategy Event Feature Row Table

`rcp_event_feature_list` is a row-level feature source. Dennis must preserve
RCP feature rows before summarizing them. The original feature tab is the
primary input for field-level commonality; it is not a policy-code summary.

```yaml
strategy_event_feature_row_table:
  - sample_id:
    user_id:
    entity_id:
    event_id:
    event_type:
    source_id:
    source_name: rcp_event_feature_list
    feature_tab: 原始类 | 衍生类 | 聚合类 | 服务类 | 名单类 | 系统类 | 未创建类 | 未知
    feature_key:
    feature_name:
    feature_type:
    feature_value_or_safe_ref:
    value_present:
    value_comparable:
    comparable_type: 等值 | 数值分桶 | 时间差 | 文本相似 | 集合相似 | 不可比较
    sensitive_value_policy: 原值可用 | 只保留安全引用 | 只保留是否存在
    candidate_feature_eligible:
    high_value_reason:
    missing_reason:
    mapped_domain: 账号 | 设备 | 网络 | 内容 | 社交 | 行为 | 策略 | 反馈 | 处置 | 未知
    mapped_field_family:
    source_quality:
    evidence_source: current_observation | projected_record | fixture_mock
    original_feature_row_retained: true
```

Retention rules:

- Original-tab rows are retained by default. Unknown original-tab fields are
  retained with `mapped_domain=未知`; they are not dropped only because Dennis
  does not yet know the feature meaning.
- Other tabs are retained when they are high value for commonality, candidate
  feature mining, false-positive analysis, or chain explanation. Examples:
  device / network / action / task / reward / client / timing / risk /
  enforcement / feedback fields.
- Sensitive values are not printed as raw values. The row remains traceable via
  `value_present`, `sensitive_value_policy`, and a safe reference where allowed.
- Android and iOS feature keys may differ. Dennis should preserve platform
  rows first and map them to field families later. Complete device fingerprint
  similarity remains a later device-detail stage, often requiring Weapon or
  device-side evidence.

Commonality levels:

- `coverage_commonality`: multiple samples have the same `feature_key`; this
  only proves the field is visible and must not support candidate features by
  itself.
- `field_value_commonality`: multiple samples share the same or comparable
  value for the same `feature_key`; this may feed candidate commonality.
- `field_combination_commonality`: multiple fields jointly explain a behavior
  pattern; this is the preferred source for candidate features.

Candidate features derived from RCP feature rows must cite
`source_feature_keys`, field combinations, supporting samples, false-positive
risks, missing fields, and validation method. `policy_code`, `event_type`, and
`risk_decision` remain entry labels only.

## Device Detail Table

`device_detail_table` is a multi-source device field detail table, not a device
summary. Dennis must keep device fields as rows before producing any candidate
feature. `device_id` is only an anchor or relation handle; it is not a device
fingerprint feature.

Weapon `weapon_inventory` / graphData / riskData is the preferred primary
device evidence source. RCP event feature rows can supplement event-time client
or device context, but they do not represent a full device profile. Login logs
and Track can support behavior-device consistency checks. Track frontend
activity itself belongs to `behavior_domain`; only the consistency result
between login device, backend action device, and frontend active device is kept
in this device table.

```yaml
device_detail_table:
  - sample_id:
    user_id:
    entity_id:
    round_id:
    device_id:
    device_safe_ref:
    source_id:
    source_name:
    action:
    device_source_type: 设备基础信息 | 设备风险标签 | 设备使用画像 | 安装列表 / 应用环境 | 账号-设备关系 | 行为-设备一致性 | 未知
    device_field_key:
    device_field_name:
    device_field_value_or_safe_ref:
    device_field_type:
    value_present:
    value_comparable:
    comparable_type: 等值 | 数值分桶 | 文本相似 | 集合相似 | 布尔 | 不可比较
    source_quality:
    evidence_source: current_observation | projected_record | fixture_mock
    event_time:
    query_time:
    device_role: 登录设备 | 后端行为设备 | Weapon 设备 | Track 关联设备 | 画像设备 | 策略事件上下文设备字段 | 未知
    sensitive_value_policy: 原值可用 | 只保留安全引用 | 只保留是否存在
    device_platform:
    app_version:
    os_version:
    phone_model:
    risk_label:
    risk_label_group:
    usage_signal:
    environment_signal:
    automation_signal:
    modification_signal:
    low_life_signal:
    app_environment_signal:
    relation_signal:
    behavior_device_consistency_signal:
    mapped_field_family:
    source_priority_boundary:
```

Device field families:

- 设备基础字段：机型、系统版本、客户端版本、平台类型、设备号。
- 设备新鲜度：启动次数少、开机时间短、最近首次出现、使用沉淀不足。
- 生活化缺失：无锁屏、无 SIM、长期充电、缺少正常使用痕迹。
- 自动化痕迹：自动化服务、脚本环境、异常客户端 / UA / 版本组合。
- 改机 / 对抗痕迹：改机标签、root、hook、frida、模拟器、环境伪造。
- 安装列表 / 应用环境：风险应用、工具类应用、应用列表相似、批量环境模板。
- 设备风险标签：设备风险命中、画像异常、低质量、设备族 / 相似簇。
- 账号-设备承载结构：一号多设备、多账号同设备、不同设备但字段相似。
- 行为-设备一致性：登录设备、后端行为设备、前端活跃设备是否一致。

Commonality levels remain shared with other fact tables:

- `coverage_commonality`: device field exists for multiple samples. This only
  means field visibility and must not become risk commonality.
- `field_value_commonality`: multiple samples share the same or comparable
  device field value.
- `field_combination_commonality`: multiple device fields jointly explain a
  candidate pattern, such as low-life device environment or automation traces.
- `derived_candidate_feature`: a model-proposed candidate feature built from
  multiple retained fields. It must cite source rows, false-positive risk, and
  validation method.

Device candidate features must cite `source_device_fields`, field combination,
supporting device/user/sample counts, black-gray interpretation,
false-positive risk, missing fields, validation method, and
`not_final_conclusion=true`. Same `device_id`, Android platform, source
coverage, or strategy hit cannot be a core device feature by itself.

Minimum device candidates currently recognized by contract:

- `low_life_device_environment_candidate`
- `automation_or_script_device_candidate`
- `device_environment_similarity_cluster_candidate`
- `account_device_fanout_candidate`
- `risky_app_environment_candidate`
- `behavior_device_consistency_gap_candidate`

## Anchor Table

Anchors are evidence handles that can drive bounded drilldown or commonality.

```yaml
anchor_table:
  - round_id:
    sample_id:
    entity_id:
    anchor_type:
    anchor_value_or_safe_ref:
    source_id:
    field_path:
    source_quality:
    anchor_class: presence_anchor | anomaly_anchor | commonality_anchor | chain_anchor
    anchor_score:
    selection_status: selected | skipped_by_domain_cap | skipped_by_type_cap | skipped_low_score | skipped_missing_anchor | plan_only
    anchor_priority_reason:
```

## Feature Table

Candidate features are not conclusions or strategies to auto-launch.

```yaml
feature_table:
  - feature_name:
    source_domains: []
    supporting_current_evidence: []
    supporting_selected_anchors: []
    signal_inputs: []
    hypothesis_inputs: []
    validation_needed: true
    false_positive_risk:
    not_final_conclusion: true
```

## Relation Table

Relations are bounded edges, not graph-wide expansion.

```yaml
relation_table:
  - from_entity:
    to_entity:
    relation_type:
    edge_type:
    edge_strength:
    source_id:
    source_quality:
    round_id:
    expansion_depth:
    stop_reason:
```

## Source Quality Table

Source quality is a first-class input to commonality and feature mining.

```yaml
source_quality_table:
  - round_id:
    entity_id:
    source_id:
    action:
    quality_class: completed | partial | no_data | skipped | timeout | missing_contract | parse_error
    reason:
    partial_subtype:
    missing_fields: []
    response_limited:
```

`no_data`, `skipped`, `timeout`, `missing_contract`, and response limits are
gaps, not low-risk counter evidence.

## Round Support Table

Rolling batch commonality must track per-round support.

```yaml
round_support_table:
  - signal_name:
    round_id:
    support_entities: []
    support_count:
    support_ratio:
    source_quality_summary:
```

## Rolling Anchor Summary

Rolling anchor summaries prevent one round from becoming a global conclusion.

```yaml
rolling_anchor_summary:
  - anchor_type:
    anchor_value_or_safe_ref:
    cumulative_support_count:
    support_rounds: []
    stability_across_rounds: stable | weakening | dropped | emerging | insufficient_rounds
    new_anchor_delta: []
    dropped_anchor_reason:
    current_status: stable | weakening | dropped | emerging | insufficient_rounds
```

Rolling batch outputs also need:

- `round_support_count`
- `cumulative_support_count`
- `support_ratio`
- `stability_across_rounds`
- `new_anchor_delta`
- `stable_anchors`
- `dropped_anchors`

## Mode Consumption

`full_observation_mode`:

- Suitable for fewer than 10 entities.
- May rely on per-sample evidence cards for human readability.
- Must still retain source quality, anchor table, and feature table references.
- Commonality should use projected facts and anchors, not narrative text alone.

`sample_expand_validate_mode`:

- Rolling batch mode: first 10, expand 10, up to 50.
- Must consume `anchor_table`, `feature_table`, `relation_table`,
  `source_quality_table`, `round_support_table`, and
  `rolling_anchor_summary`.
- Must output round support, cumulative support, stability across rounds, new
  anchor delta, stable anchors, and dropped anchors.
- Per-user observations are explanation material only.

## Mapping From Existing Artifacts

Current Phase 3/4 artifacts can map into the table layer:

- `base_summary_card` and `drilldown_evidence_card` -> `standard_detail_table`
- `candidate_anchor_pool`, `selected_drilldown_anchors`, `skipped_anchors` -> `anchor_table`
- `candidate_features` -> `feature_table`
- `relation_expansion_result` -> `relation_table`
- `source_quality` -> `source_quality_table`
- `commonality_matrix.shared_signals` -> `round_support_table`
- `anchor_scoring_summary` and cross-round deltas -> `rolling_anchor_summary`

Runtime may initially produce these as equivalent structured artifacts. Phase 4.6
only fixes the contract and checks; full runtime table emission is a later step.

## Boundaries

- Do not restore raw bodies into model context.
- Do not let per-user observation be the only batch commonality source.
- Do not treat missing, skipped, no-data, timeout, or missing-contract rows as
  counter evidence.
- Do not treat a candidate feature as a final conclusion.
- Do not treat rolling support as full coverage without validation.
- DataAgent/Hive validation remains authorization-gated and is not executed by
  this contract.
