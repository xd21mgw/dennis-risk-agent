# Provider Request Contract v1

## 0. 目标

本文件定义 Evidence Tool Router 到各 provider 的统一中间层请求格式。不同 provider 的真实 API 未来可能不同，本文件不定义真实 API、真实表名、真实字段名或真实 SQL。

## 1. 统一 provider_request 结构

```yaml
provider_request:
  request_id:
  source_query_intent_id:
  provider:
  request_type:
  target_evidence:
  risk_question:
  minimum_inputs:
  required_data_domains:
  field_types_needed:
  join_paths_needed:
  time_window:
  query_dimensions:
  expected_outputs:
  quality_checks:
  freshness_expectation:
  permission_boundary:
  safety_boundary:
  manual_review_required:
  provider_specific_payload:
```

## 2. 字段说明

- `request_id`：Router 生成的 provider request 标识。
- `source_query_intent_id`：来源 query intent 标识。
- `provider`：目标 provider。
- `request_type`：查询类型，如实时日志、离线分析、策略链路、设备指纹、关系图、人工补证。
- `target_evidence`：目标证据。
- `risk_question`：原始风险问题。
- `minimum_inputs`：最小输入。
- `required_data_domains`：需要的数据域。
- `field_types_needed`：抽象字段类型，不写真字段。
- `join_paths_needed`：抽象 join path。
- `time_window`：时间窗。
- `query_dimensions`：查询维度。
- `expected_outputs`：期望输出。
- `quality_checks`：质量检查要求。
- `freshness_expectation`：时效要求。
- `permission_boundary`：权限边界。
- `safety_boundary`：安全边界。
- `manual_review_required`：是否需要人工确认。
- `provider_specific_payload`：provider 定制载荷，只能使用抽象结构。

## 3. Provider Specific Payload

### dataagent_provider

`provider_specific_payload` 是自然语言 question。

```yaml
provider_specific_payload:
  natural_language_question:
  context_summary:
  expected_markdown_sections:
  do_not_generate_real_sql_without_permission:
```

说明：

- Data Agent 适合自然语言问题。
- 不假设 Data Agent 支持结构化 constraints。
- 返回 SQL 不等于返回结果。

### realtime_log_provider

未来可能是 structured query。

```yaml
provider_specific_payload:
  log_scope:
  entity_keys:
  event_or_api_types:
  time_window:
  sequence_requirement:
  aggregation_requirement:
```

说明：

- 真实 API 待内部平台定义。
- 只表达日志范围、实体、事件和时间窗。

### risk_engine_provider

未来可能是风险事件或策略链路查询。

```yaml
provider_specific_payload:
  risk_event_id:
  entity_keys:
  strategy_context:
  decision_context:
  time_window:
```

说明：

- 可以表达 risk_event_id / user_id / strategy_id 等抽象输入。
- 策略命中不等于风险事实。

### device_fingerprint_provider

未来可能是设备、指纹、SDK 和画像查询。

```yaml
provider_specific_payload:
  device_entities:
  fingerprint_entities:
  app_context:
  sdk_context:
  time_window:
```

说明：

- 可以表达 device_id / fingerprint_id 等抽象输入。
- SDK 缺失不能直接判破解包。

### relation_graph_provider

未来可能是图查询。

```yaml
provider_specific_payload:
  seed_user_ids:
  seed_device_ids:
  relation_types:
  graph_depth:
  time_window:
  aggregation_requirement:
```

说明：

- 强关联和团组只说明存在关系，不直接说明作恶。

### structured_sql_or_feature_provider

未来可能是结构化 API、实时 SQL 或 feature service。

```yaml
provider_specific_payload:
  feature_or_topic:
  entity_keys:
  dimensions:
  metrics:
  time_window:
  output_shape:
```

说明：

- 真实 API、SQL 和字段映射由未来内部平台补充。

### manual_review_provider

未来是人工任务说明。

```yaml
provider_specific_payload:
  review_question:
  evidence_summary:
  missing_evidence:
  counter_evidence_to_check:
  business_owner_or_reviewer:
  decision_needed:
```

说明：

- 用于权限、业务合理性、授权边界、误伤复核。

## 4. 生成约束

- provider request 必须继承 query intent 的 `safety_boundary`。
- provider request 必须保留 `permission_boundary`。
- provider request 不得包含真实 API、真实表名、真实字段名或真实 SQL。
- provider request 不得要求 provider 绕过权限。
- provider request 不得要求 provider 直接给最终处罚建议。

