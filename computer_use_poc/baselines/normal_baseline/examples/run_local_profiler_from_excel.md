# Run Local Profiler from Excel - Example

## 概述

本文档说明如何基于本地 Excel 样例运行 normal_baseline profiler。

**重要口径声明：**

当前 profiler demo 使用的是 **population baseline / 大盘背景 baseline**，不是 LOGIN_AUE 精准 baseline。

- `baseline_scope = population_baseline`
- `baseline_scope_detail = population_login_or_source_baseline_from_available_offline_samples`
- `not_login_aue_specific = true`

这意味着 profiler 产出的所有字段分布、缺失率、低熵 profile 都是**大盘登录行为样本**的客观统计，而不是 LOGIN_AUE 场景下正常用户的精准画像。

**不宣称 LOGIN_AUE normal baseline 已完成。**

LOGIN_AUE 精准 baseline 后续需要：
1. 补充字段映射（loginType / _errorCode / userRegisterDays / userFanCnt 在 infra_user_action_log 中不存在）
2. 补充样本条件（使用 passport_action_log 的 params.type / status / uri 三重过滤，或使用档案中心补充用户画像条件）
3. 或使用 DataAgent 取 LOGIN_AUE 精准筛选后的正式样本

**大盘作弊率较低时，population baseline 可先用于判断字段/取值是否大盘常见。**

例如：如果一个字段在大盘样本中覆盖率 >95%、top1 比率 >90%，那么该字段的某个取值在大盘行为中是"常见"的——这可以作为观察新用户/新设备时"该取值是否离群"的参考背景，但不能直接作为"该取值就是正常的"判断。

## 前置条件

1. Python 3.9+，已安装 pandas / openpyxl / pyyaml
2. input Excel 文件位于 `input_excels/`
3. profiler_input_contract YAML 位于 `recon/profiler_input_contract_20260609_v0_1.yaml`

## 命令

```bash
python computer_use_poc/baselines/normal_baseline/src/normal_baseline_profiler.py \
  --input-dir computer_use_poc/baselines/normal_baseline/input_excels \
  --contract computer_use_poc/baselines/normal_baseline/recon/profiler_input_contract_20260609_v0_1.yaml \
  --output-dir /tmp/normal_baseline_profiler_demo \
  --topn-limit 20
```

`--contract` 参数必须指向一个有效的 YAML 文件。profiler 优先从 YAML 读取 contract，不再静默使用硬编码数据。如果 YAML 缺失或格式错误，会给出清晰的错误信息。

## 输出文件

| 文件 | 内容 |
|---|---|
| `normal_field_inventory.json` | 所有发现字段清单：source_name / field_path / field_origin / coverage / cardinality |
| `normal_field_profile_sample.json` | 字段样本 profile：coverage / missing / distinct / top1/top3 / cardinality / lifecycle |
| `normal_discrete_field_distribution.json` | 离散字段 TOP-N + __OTHER__ 分布；weapon_one_risk label TOP-N |
| `normal_field_missingness_profile.json` | 字段缺失率：null / empty / parse_error / missingness_type |
| `normal_low_entropy_profile.json` | field_value 粒度低熵 profile：normal_status / top1 / coverage / sample_size |
| `high_cardinality_summary.json` | 高基数字段摘要：distinct / unique / reuse / max_per_value / top_reused |
| `profiler_metadata.json` | profiler 元信息：版本 / 时间 / 字段统计 / baseline_scope / 边界声明 |

## baseline_scope 口径

profiler_metadata.json 中固化以下口径字段：

| 字段 | 值 | 说明 |
|---|---|---|
| baseline_scope | population_baseline | 大盘背景 baseline |
| baseline_scope_detail | population_login_or_source_baseline_from_available_offline_samples | 基于可用离线样本的大盘登录/行为 baseline |
| not_login_aue_specific | true | 当前不是 LOGIN_AUE 精准 baseline |
| login_aue_condition_status | not_mapped_in_current_infra_sample | LOGIN_AUE 条件未在当前 infra 样本中映射 |
| login_aue_missing_conditions | [loginType, _errorCode, userRegisterDays, userFanCnt] | 缺少的 LOGIN_AUE 条件字段 |

source_grain 说明：

| source | grain | 说明 |
|---|---|---|
| infra_user_action_log | population_login_behavior_sample | 大盘登录行为样本 |
| passport_action_log | app_related_passport_action_sample | APP 相关 passport 动作样本 |
| weapon_android | population_weapon_android_sample | 大盘 Android weapon 样本 |
| weapon_ios | population_weapon_ios_sample | 大盘 iOS weapon 样本 |

## low_entropy 说明

当前 Excel 样例每个 source 约 1000 条，不满足 3000 样本门槛（sample_low_entropy_rule_v0_1）。

因此 low_entropy_profile 中不应出现 `normal_low_entropy` 或 `normal_popular`。
应全部为 `normal_unknown_small_sample` 或 `normal_sparse_or_low_coverage`。

后续使用 DataAgent 取 3000~5000 条正式样本后，low_entropy_profile 才可能命中阈值。

## 测试

```bash
python -m pytest computer_use_poc/baselines/normal_baseline/tests/test_normal_baseline_profiler.py -v
```

## 边界声明

- 不做风险判断
- 不输出 risk_judgement
- 不输出 feature_candidate
- 不输出 candidate_feature_decision
- weapon_one_risk 只做覆盖率/TOP-N 统计，不做风险定性
- baseline_scope = population_baseline，不是 LOGIN_AUE 精准筛选
- 当前 baseline 是大盘背景 baseline，不宣称 LOGIN_AUE normal baseline 已完成
- 大盘作弊率较低时，population baseline 可先用于判断字段/取值是否大盘常见