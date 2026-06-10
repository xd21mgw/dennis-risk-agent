# Population Baseline v0.1 Run Report

## 运行概况

| 项目 | 值 |
|---|---|
| profiler 版本 | v0.1 |
| baseline_scope | population_baseline |
| sample_size_level | initial_population_baseline |
| not_login_aue_specific | true |
| rule_source | sample_frequency_rule_v0_1 |
| profiled_at | 2026-06-10T19:33:04 |
| output_dir | /tmp/normal_baseline_layered_v0_2 |

## 分层门槛

| 参数 | 值 | 含义 |
|---|---|---|
| observable_min_covered_count | 200 | 可观察频率的最低 covered 数 |
| referenceable_min_covered_count | 300 | 可引用频率的最低 covered 数 |
| strong_low_entropy_min_covered_count | 1000 | 强低熵判断的最低 covered 数 |
| min_coverage_ratio_for_strong | 0.8 | 强低熵判断的最低覆盖率 |
| top1_ratio_threshold | 0.9 | top1 集中度阈值 |
| top3_ratio_threshold | 0.97 | top3 集中度阈值 |

## 4 个 Source 样本量

| source_name | 样本行数 | 发现字段数 | 采集方式 |
|---|---|---|---|
| infra_user_action_log | 1000 | 121 | Excel fallback |
| passport_action_log | 1000 | 187 | Excel fallback |
| weapon_android | 1000 | 886 | Excel fallback |
| weapon_ios | 1000 | 272 | Excel fallback |

注：当前样本为用户本地 Hive 查询后导出的约 1000 条 Excel 样例，不是 DataAgent 正式 3000-5000 抽样。

## 7 个 Profiler JSON 输出

| 文件 | 条目数 | 说明 |
|---|---|---|
| normal_field_inventory.json | 1466 | 字段发现清单 |
| normal_field_profile_sample.json | 1380 | 字段级统计（类型、基数、覆盖等） |
| normal_discrete_field_distribution.json | 1367 | 离散字段 TOP-N 分布 |
| normal_field_missingness_profile.json | 1380 | 字段缺失率档案 |
| normal_low_entropy_profile.json | 1367 | 低熵/高频状态 |
| high_cardinality_summary.json | 82 | 高基数字段摘要 |
| profiler_metadata.json | 30 fields | 元数据 |

## normal_status 分布

| normal_status | 数量 | 占比 | 含义 |
|---|---|---|---|
| normal_sparse_or_low_coverage | 652 | 47.7% | covered_count < 200，样本不足观察 |
| normal_referenceable | 455 | 33.3% | 300 ≤ covered_count < 1000，可引用但不足强低熵 |
| normal_low_entropy | 104 | 7.6% | covered_count ≥ 1000 且 top1 ≥ 0.9 或 top3 ≥ 0.97 |
| normal_not_popular_in_sample | 83 | 6.1% | covered_count ≥ 1000 但未达高频阈值 |
| normal_observable | 57 | 4.2% | 200 ≤ covered_count < 300，可观察频率 |
| normal_popular | 16 | 1.2% | covered_count ≥ 1000 且 top1 ≥ 0.5 |
| **合计** | **1367** | **100%** | |

## normal_low_entropy 示例

| field_path | covered | top1 | top3 | coverage |
|---|---|---|---|---|
| passport_action_log.status | 1000 | 0.934 | 0.954 | 1.00 |
| weapon_android.raw_data.buildBootloader | 1000 | 1.000 | 1.000 | 1.00 |
| weapon_android.raw_data.weaponDecodeHeader.weaponStatus | 1000 | 0.971 | 1.000 | 1.00 |
| weapon_android.raw_data.oneDataVersion | 1000 | 1.000 | 1.000 | 1.00 |
| weapon_android.raw_data.buildLibpath | 1000 | 1.000 | 1.000 | 1.00 |
| weapon_android.raw_data.weaponPlatform | 1000 | 1.000 | 1.000 | 1.00 |
| infra_user_action_log.result | 1000 | 0.744 | 1.000 | 1.00 |
| weapon_android.product | 1000 | 0.521 | 1.000 | 1.00 |

## normal_popular 示例

| field_path | covered | top1 | coverage |
|---|---|---|---|
| infra_user_action_log.action_type | 1000 | 0.556 | 1.00 |
| weapon_android.sdk_version | 1000 | 0.809 | 1.00 |
| weapon_android.raw_data.sourceIpv6 | 1000 | 0.747 | 1.00 |
| weapon_android.raw_data.weaponRisk | 1000 | 0.627 | 1.00 |
| weapon_ios.sdk_version | 1000 | 0.773 | 1.00 |
| weapon_ios.raw_data.sourceIpv6 | 1000 | 0.693 | 1.00 |

## normal_referenceable 示例

| field_path | covered | top1 | coverage |
|---|---|---|---|
| weapon_android.raw_data.ps | 998 | 0.986 | 1.00 |
| passport_action_log.phone_mod | 997 | 0.041 | 1.00 |
| weapon_android.raw_data.sourceType | 997 | 0.995 | 1.00 |
| weapon_ios.raw_data.network.llw0_up | 996 | 0.998 | 1.00 |
| weapon_ios.raw_data.hwProduct | 996 | 0.095 | 1.00 |

## normal_observable 示例

| field_path | covered | top1 | coverage |
|---|---|---|---|
| weapon_android.raw_data.vendorSecHw.huawei_ifaa | 292 | 0.003 | 0.29 |
| weapon_android.raw_data.inputDevice.2[1].id | 265 | 0.302 | 0.27 |
| weapon_android.raw_data.inputDevice.2[1].name | 265 | 0.502 | 0.27 |
| infra_user_action_log.extra.serviceToken.basicToken.version | 256 | 1.000 | 0.26 |
| infra_user_action_log.extra.serviceToken.basicToken.userId | 256 | 0.004 | 0.26 |

## normal_not_popular_in_sample 示例

| field_path | covered | top1 | coverage |
|---|---|---|---|
| infra_user_action_log.server_ip | 1000 | 0.046 | 1.00 |
| infra_user_action_log.user_agent | 1000 | 0.431 | 1.00 |
| infra_user_action_log.uri | 1000 | 0.331 | 1.00 |
| passport_action_log.uri | 1000 | 0.283 | 1.00 |
| passport_action_log.sys_ver | 1000 | 0.156 | 1.00 |

## High Cardinality Summary

共 82 个高基数字段，包括：user_id, did, deviceId, androidId, oaid, idfa, idfv, ip, clientIP, clientIp, sourceIp, requestId, headerKsId, egid, photoId 等。这些字段只做 high_cardinality_summary（distinct_count / top_reused_values），不进入普通 TOP-N 低熵判断。

## Missingness 分布

| missingness_type | 数量 |
|---|---|
| low_coverage_unreliable | 801 |
| normal_present | 486 |
| normal_sparse_field | 90 |
| source_not_checked | 3 |

## 当前限制说明

1. **样本量不足正式门槛**：当前 4 个 source 各约 1000 行，为用户本地导出的 Excel 样例。正式 population baseline 需要 3000-5000 行。
2. **DataAgent 服务账号权限不足**：DataAgent Conversational API 的 SQL 引擎使用的服务账号缺少目标表的读权限，无法通过 DataAgent 直接执行正式抽样 SQL。
3. **推荐路径**：用户在 Jupyter/Notebook 中执行 `normal_population_sample_extraction_sql_v0_1.sql` 中的 deterministic hash sample SQL，导出 CSV 后重新运行 profiler。
4. **47.7% 字段为 sparse_or_low_coverage**：因样本仅 1000 行，很多子字段覆盖不足 200 条，需更多样本才能进入 observable/referenceable 层。
5. **not_login_aue_specific=true**：当前 baseline 是大盘背景 baseline，不是 LOGIN_AUE 正边精准筛选。
6. **不做风险判断**：所有输出不包含 risk_judgement / feature_candidate / candidate_feature_decision。

## 边界声明

- 不做风险判断
- 不输出 risk_judgement / feature_candidate / candidate_feature_decision
- normal_popular / normal_low_entropy 代表大盘常见，不等于安全
- normal_not_popular_in_sample 不等于风险候选
- normal_observable / normal_referenceable 只能作为参考，不做强判断
- baseline 缺失或过时时，必须标记 baseline_gap
