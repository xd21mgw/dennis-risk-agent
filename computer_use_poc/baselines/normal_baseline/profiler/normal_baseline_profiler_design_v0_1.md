# normal_baseline Profiler Design v0.1

## 定位

local profiler 是 normal_baseline 的本地分析组件，负责对 DataAgent 抽取的原始样本记录做字段发现、分布统计和低熵 profile。

它不做风险判断，不做候选特征推荐，不做策略建议。

## 输入

- DataAgent 返回的 raw sample records（JSON/CSV 格式）
- 每条记录包含：entity_id、dt/event_time、source_name、普通列、JSON 字段、map/struct 字段、array 字段
- 对应的 normal_batch yaml 描述文件

## 处理流程

### Phase 1：字段发现（Field Discovery）

1. 遍历所有样本记录的所有字段
2. 普通列：直接识别为 `ordinary_column`
3. JSON 字段：递归展开，生成 `json_path`（如 `deviceInfo.deviceModel`）
4. map/struct 字段：递归展开，生成 `map_path` / `struct_path`（如 `extParams.key_name`）
5. array/list 字段：归一化摘要，生成 `array_path`（如 `tagList[].tagName`）
6. 统一生成 `field_path`：`source_name.column_name` 或 `source_name.column_name.nested_key`
7. 输出 `normal_field_inventory`

### Phase 2：字段 Profile（Field Profile）

1. 对每个 `field_path`，计算：
   - `seen_count`：出现次数
   - `coverage_ratio`：非空非缺失比例
   - `missing_ratio`：缺失比例
   - `distinct_value_count`：唯一值数量
   - `top1_ratio`：TOP1 值占比
   - `top3_ratio`：TOP3 值占比
   - `cardinality_bucket`：基数桶（low / medium / high / very_high）
   - `value_shape`：值形状（scalar / enum / range / json / array / mixed）
   - `sample_examples`：3~5 个示例值
   - `field_lifecycle_status`：生命周期状态
2. 输出 `normal_field_profile_sample`

### Phase 3：离散分布（Discrete Distribution）

1. 对离散/枚举型字段，计算 TOP-N 分布：
   - 默认 TOP20
   - 低于 TOP20 阈值的值合并为 `__OTHER__`
   - `other_value_count` 和 `other_value_ratio`
   - 不存储全量分布
2. 对高基数字段（deviceId / xm1 / xm3 / androidId / oaid / ip / photoId / commentId / requestId）：
   - 不展开全量 value
   - 只做摘要：`distinct_value_count`、`unique_value_ratio`、`reuse_ratio`、`max_entities_per_value`、`top_reused_values TOP-N`
3. 输出 `normal_discrete_field_distribution`

### Phase 4：缺失率 Profile（Missingness Profile）

1. 对每个 `field_path`，计算：
   - `covered_entity_count`
   - `missing_count`
   - `missing_ratio`
   - `null_ratio`
   - `empty_string_ratio`
   - `parse_error_ratio`
   - `missingness_type`
2. 输出 `normal_field_missingness_profile`

### Phase 5：低熵 Profile（Low Entropy Profile）

1. 对每个 `field_value`（粒度是 field_value，不是 field），计算：
   - `top1_ratio`
   - `coverage_ratio`
   - `sample_entity_count`
2. 应用低熵规则：
   ```
   sample_entity_count >= 3000
   AND coverage_ratio >= 0.8
   AND (
     top1_ratio >= 0.9
     OR top3_ratio >= 0.97
   )
   ```
3. 命中 → `normal_low_entropy` 或 `normal_popular`
4. 不命中 → `normal_not_popular_in_sample`（仅记录，不做风险判断）
5. 条件不满足 → `normal_sparse_or_low_coverage` / `normal_unknown_small_sample` / `normal_unknown_sampling_bias`
6. 输出 `normal_low_entropy_profile`

## 字段展开策略

### 普通列

直接映射为 `field_path = source_name.column_name`，不做展开。

### JSON 字段递归展开

- 输入：raw JSON string
- 解析为 JSON object
- 递归遍历所有 key
- 生成 `field_path = source_name.json_column.key1.key2...`
- 嵌套 JSON 继续递归
- 数组内对象展开为 `field_path = source_name.json_column[].key1.key2...`
- 最大展开深度：5 层（超过 5 层标 `parse_depth_exceeded`）

### map/struct 字段递归展开

- 输入：raw map / struct
- 遍历所有 key
- 生成 `field_path = source_name.map_column.key_name`
- 嵌套 map/struct 继续递归
- 最大展开深度：5 层

### array/list 字段归一化摘要

- 输入：raw array / list
- 如果元素是 scalar：统计 `array_length`、`distinct_element_count`、`top_elements TOP-N`
- 如果元素是 object：展开为 `field_path = source_name.array_column[].key1.key2...`
- 最大展开深度：5 层

## 高基数字段处理

以下字段不展开全量 value：
- deviceId
- xm1
- xm3
- androidId
- oaid
- ip
- photoId
- commentId
- requestId

只做摘要：
- `distinct_value_count`：唯一值总数
- `unique_value_ratio`：只出现一次的值比例
- `reuse_ratio`：被多个 entity 共用的值比例
- `max_entities_per_value`：单个 value 最多关联多少 entity
- `top_reused_values TOP-N`：被最多 entity 共用的 TOP-N value

## 输出 Schema

参见 `profiler/local_profiler_output_schema_v0_1.yaml` 和 `schemas/` 目录下各 schema 文件。

## 不做的事

- 不做 risk_judgement
- 不做 feature_candidate 推荐
- 不做 candidate_feature_decision
- 不做跨 source 对比
- 不做异常检测
- 不做模式识别
- 不接入 Dennis runtime
- 不自动触发 DataAgent