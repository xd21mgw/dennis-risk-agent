# DataAgent Sampling Request Template v0.1

## 用途

本模板用于向 DataAgent 发起 normal baseline 样本抽取请求。

DataAgent 只负责取原始记录，不做任何分析。

## 请求模板

```yaml
request:
  request_id: "normal_baseline_{batch_id}_{timestamp}"
  request_type: sample_extraction
  purpose: normal_baseline_profiler_input
  
  # ⚠️ DataAgent 边界硬约束
  boundary:
    只取数不分析: true
    do_not_analyze: true
    不输出可疑正常异常风险共性特征等判断: true
    不自行扩展查询source: true
    不自行join其他表: true
    不改筛选条件: true
    不聚合字段分布: true
    不计算TOPN: true
    不计算低熵: true
    不计算缺失率: true
    不解释字段语义: true
    如果SQL有问题只指出执行错误和最小修正建议: true
  
  source:
    source_name: "{source_name}"
    table_hint: "{table_hint}"
  
  sampling_conditions:
    - field: "{field_name}"
      operator: "{operator}"
      value: "{value}"
      semantic: "{semantic_description}"
  
  time_window:
    start: "{start_time}"
    end: "{end_time}"
    timezone: "{timezone}"
  
  sampling_method:
    method: deterministic_hash_sample
    hash_field: "{hash_field}"
    hash_modulo: "{modulo}"
    hash_range_start: "{range_start}"
    hash_range_end: "{range_end}"
    expected_sample_size: "{expected_size}"
    no_bare_limit: true
  
  output_format:
    format: raw_records
    preserve_original_fields: true
    preserve_json_fields_as_raw_string: true  # JSON 字段保留原始字符串，本地 profiler 展开
    preserve_map_struct_fields_as_raw: true   # map/struct 保留原始结构，本地 profiler 展开
    preserve_array_fields_as_raw: true        # array 保留原始结构，本地 profiler 展开
    do_not_expand_json: true
    do_not_flatten_struct: true
    do_not_parse_nested: true
    do_not_aggregate: true
    do_not_compute_statistics: true
  
  required_output_fields:
    - entity_id
    - dt / event_time
    - source_name
    - "{all_ordinary_columns}"
    - "{all_json_columns_as_raw_string}"
    - "{all_map_struct_columns_as_raw}"
    - "{all_array_columns_as_raw}"
    - "{sampling_condition_fields}"
```

## 填写说明

1. `batch_id`：使用 normal_batch 描述文件中的 `batch_id`。
2. `source_name`：使用 normal_batch 中的 `source_name`。
3. `sampling_conditions`：严格照搬 normal_batch 中定义的条件，不得修改。
4. `hash_field / hash_modulo / hash_range`：使用 normal_batch 中定义的 hash 参数。
5. `output_format`：必须指定保留原始字段，不展开、不聚合。
6. 如果 DataAgent 返回的记录超过 `expected_sample_size`，local profiler 会自动截断到 expected 范围。

## DataAgent 错误处理

如果 DataAgent 执行出错：
- 只记录 `execution_error`、`error_message`、`sql_used`
- 不自行修改 SQL
- 不自行重试不同条件
- 不自行换表 / 换 source
- 只提供最小修正建议（如字段名拼写、分区格式）
- 修正必须经人工确认后重新提交