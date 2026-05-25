# Batch L1 Drilldown Layer Patch v1

## Goal

Add the missing L1 batch data drilldown layer to Batch Risk Clustering Analysis Pack without redesigning the existing batch clustering capability.

## Added Files

- `computer_use_poc/batch_risk_clustering/account_risk_data_source_registry_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_l1_feature_query_contract_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_top_dimension_drilldown_template_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_frequent_pattern_contribution_template_v1.md`

## Updated Files

- `computer_use_poc/batch_risk_clustering/README.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_clustering_methodology_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_response_template_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_runtime_validation_cases_v1.yaml`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/smoke_tests.md`

## New Workflow

```text
批量输入
→ L1 宽表 / 画像浅查
→ TOP 维度下探
→ 频繁项 / 贡献度分析
→ A→B 有向相关矩阵
→ cluster hint
→ 代表抽样
→ cluster evidence card
→ 举一反三 / 策略建议
```

## L1 Feature Query Contract

Added `batch_feature_table` schema covering:

- user profile
- device profile
- IP / network
- login security
- behavior
- frontend chain
- strategy hit
- content behavior
- channel / campaign
- fake account tags
- baseline / control

## Data Source Registry

Added account-risk data source registry for six source groups:

1. 通用风控特征宽表 / 画像底表
2. 用户基础属性 / 注册画像
3. 登录 / 账号安全行为日志
4. Token / Web / Server 行为链路
5. Admin / 档案 / 判罚日志
6. 虚假账号标签 / 大盘 / 下游作恶

Each table is documented with capability domain, grain, freshness, field richness, applicable scenarios and notes.

## TOP Dimension Drilldown

Added `top_dimension_summary` schema and supported dimensions:

- app_version
- ip24
- device_model
- login_type / login_method
- strategy_hit
- abnormal_action
- frontend_missing_rate
- channel
- fake_account_tag

## Frequent Pattern / Contribution

Added `frequent_pattern` and `contribution_score` templates.

High contribution combinations are explicitly limited to:

- cluster hint
- candidate feature hint
- representative sampling guide
- abnormal correlation candidate

They are not final risk conclusions.

## Regression Coverage

Added text-level validation for:

- ATO mixed batch
- protocol / client anomaly batch
- group-control / device farm batch
- fake account / downstream badness batch
- high contribution with plausible business explanation requiring downgrade to review

## Boundaries

- Did not access real platform.
- Did not call DataAgent.
- Did not execute Hive SQL.
- Did not modify auth or gateway.
- Did not repackage release.
- Did not create strategy or disposal actions.
- Sensitive fields such as identity number, phone, real-name information and credential-like fields are controlled auxiliary evidence and must not be output in plaintext.

