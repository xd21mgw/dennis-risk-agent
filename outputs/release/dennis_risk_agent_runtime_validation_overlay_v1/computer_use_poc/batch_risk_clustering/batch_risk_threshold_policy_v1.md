# Batch Risk Threshold Policy v1

## 1. Purpose

Thresholds decide whether Dennis should run single-case execution, small multi-case comparison, batch clustering, or aggregation planning.

This policy prevents accidental large-scale online lookups and keeps batch reasoning separate from single-case evidence closure.

## 2. Threshold Table

| entity_count | selected_mode | default behavior | key boundary |
|---:|---|---|---|
| 1-2 | `single_entity_execution_mode` | 可逐个深查，输出单 case evidence card。 | 如用户明确要求批量视角，可补轻量对比，但不进入正式分簇。 |
| 3-4 | `small_multi_case_execution_mode` | 默认仍可全量深查；每个 case 输出简版 evidence card。 | 最后增加 cross-case comparison；不能因为相似就直接判定同团伙。 |
| 5-9 | `small_batch_mode` | 不默认逐个深查全部长链路；先轻量分组、风险假设、优先级排序。 | 可全查或抽 3-5 个代表样本，取决于用户要求和成本。 |
| 10-49 | `batch_clustering_mode` | 默认标准批量分簇研判。 | 不逐个在线查；先做分簇、异常相关性矩阵、代表样本抽样。 |
| 50-499 | `large_batch_aggregation_mode` | 必须优先生成聚合分析 / DataAgent-Hive query plan。 | 不逐个在线查；只建议抽样深查。 |
| 500+ | `alert_batch_or_population_analysis_mode` | 只做批次级分布、异常相关性、代表样本抽样、策略建议。 | 必须生成离线取数 / 聚合分析计划。 |

## 3. Detailed Rules

### 1-2 entities

- Mode: `single_entity_execution_mode`.
- 可逐个深查.
- 输出单 case evidence card.
- 如果用户问“这两个是否相似”，只做轻量对比，不升级为团伙判断.

### 3-4 entities

- Mode: `small_multi_case_execution_mode`.
- 可全量深查.
- 每个 case 输出简版 evidence card.
- 增加 cross-case comparison:
  - 共设备.
  - 共 IP / subnet / ASN.
  - 共入口.
  - 共版本.
  - 共策略命中.
  - 共行为链路.
- 必须有 join key 或共用基础设施证据，才可升级为同源风险；不能仅凭相似性判断同团伙.

### 5-9 entities

- Mode: `small_batch_mode`.
- 5 个以下可全量深查；5-9 个是小批量，应先轻量分组.
- 默认先分组、排序、提出风险假设.
- 若用户明确要求且成本可控，可以深查全部.
- 否则建议抽 3-5 个代表样本.
- 输出 small batch summary + representative evidence cards.

### 10-49 entities

- Mode: `batch_clustering_mode`.
- 10+ batch_clustering_mode 是标准批量分簇默认触发点.
- 不逐个在线查.
- 先做:
  - entity cluster.
  - time cluster.
  - behavior cluster.
  - environment cluster.
  - strategy cluster.
  - entry/path cluster.
  - interface/request cluster.
  - abnormal correlation matrix.
- 抽 3-5 个代表样本做 evidence card.

### 50-499 entities

- Mode: `large_batch_aggregation_mode`.
- 50+ aggregation / DataAgent-Hive query plan 是默认路径.
- 必须优先生成聚合分析 / DataAgent-Hive query plan.
- 不逐个在线查.
- 重点分析:
  - 字段分布.
  - 条件分布.
  - 异常富集.
  - 时间爆发.
  - 策略命中.
  - 渠道 / 版本 / 设备 / IP 聚集.

### 500+ entities

- Mode: `alert_batch_or_population_analysis_mode`.
- 只做批次级分布、异常相关性、代表样本抽样、策略建议.
- 不做逐个研判.
- 必须生成离线取数 / 聚合分析计划.
- 如用户要求逐个查，应降级说明成本与不可行性，建议抽样或分批.

## 4. Intent Overrides

- 如果用户问“策略怎么做 / 如何灰度 / 如何误伤控制 / 举一返三 / 监控怎么建”，即使带了 user_id，也优先 plan mode，不查平台.
- 如果用户明确说“帮我查这几个用户”，且实体数 <5，可以全量深查.
- 如果用户明确说“帮我查这批用户”，且实体数 >=10，默认先批量分簇和抽样，不逐个查.
- 如果用户说“这些接口请求量突然升高”，默认 interface/request batch clustering.
- 如果用户说“这批告警帮我归因”，默认 alert batch clustering.

## 5. DataAgent Boundary

- DataAgent 只能定位为 Hive / 公司数仓取数分析能力.
- DataAgent 不是万能数据底座.
- 真实平台 observation、DataAgent 查询、Hive 离线取数都只作为后续补证路径，本 pack 不执行.
