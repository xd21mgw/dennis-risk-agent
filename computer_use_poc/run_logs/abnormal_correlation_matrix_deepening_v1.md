# Abnormal Correlation Matrix Deepening v1

## 本轮目标

将 `abnormal_correlation_matrix_v1.md` 从概念定义升级为可执行的批量风控分簇方法，补齐风险解释层、基线处理、关系强度分级、反向验证、混杂/伪相关排除和标准输出样例。

## 修改文件

- `computer_use_poc/batch_risk_clustering/abnormal_correlation_matrix_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_quality_rubric_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_text_dry_run_v1.md`
- `computer_use_poc/smoke_tests.md`

## 新增文件

- `computer_use_poc/run_logs/abnormal_correlation_matrix_deepening_v1.md`

## 补强内容

### Relation families

- infrastructure correlation：IP / device / proxy / ASN 与设备、账号、请求模式的异常绑定。
- toolchain correlation：app_version / mod / frontend gap / old version 与异常请求或行为的绑定。
- entry-path correlation：login_method / OAuth / Harmony / one-click-login 与后续 kick_out / token_revoke / publish / password_change。
- behavior-chain correlation：login_success / no_frontend_action / strategy_hit 与后续高风险动作。
- business-arbitrage correlation：channel / campaign / activity_entry 与 reward_claim / retention / device reuse。
- strategy-feedback correlation：strategy_id / hit_reason / control_action 与 false-positive feedback / manual review / complaint / churn。

### Baseline policy

- `historical_normal_baseline_available`
- `same_period_control_group_available`
- `strategy_population_baseline_available`
- `only_current_batch_available`
- `baseline_missing`

规则：

- 有历史正常基线或同周期对照组时，才允许 strong enrichment。
- 只有当前批次时，只能写 `batch_internal_concentration`。
- `baseline_missing` 时只能 hypothesis_only / weak，除非有非常强 raw evidence join key。
- 必须检查 denominator，不能只看分子。
- 策略召回集合必须标 `selection_bias_risk`。

### Relationship strength

- `strong_abnormal_correlation`
- `medium_abnormal_correlation`
- `weak_signal`
- `hypothesis_only`
- `not_enough_evidence`

### Required checks

- direction_check
- reverse_check
- time_alignment_check
- denominator_check
- confounder_check
- selection_bias_check
- business_explanation_check
- source_quality_check

## 3 个样例摘要

### ATO Harmony/OAuth

`login_method=HARMONY_ONE_CLICK -> kick_out/token_revoke/publish_after_login` 应输出 entry-path correlation。缺授权链路和 token raw evidence 时只能 medium，不能 strong，也不能默认写成撞库。

### 协议降版本

`old_app_version + abnormal_mod -> high_frequency_backend_action` 应输出 toolchain correlation。`mod=POST` 只能表示字段语义待确认，不能当 HTTP method。缺前端行为基线时只能 medium/weak。

### 活动套利

`channel=A -> reward_claim + low_retention + device_reuse` 应输出 business-arbitrage correlation。没有渠道全量分母时只能 `batch_internal_concentration`，不能 strong enrichment。

## Smoke tests 摘要

新增 BATCH-RISK-017 到 BATCH-RISK-024：

- relation families 存在。
- baseline_missing 不得 strong enrichment。
- only_current_batch 只能 batch_internal_concentration。
- 必须包含 reverse_check / confounder_check / denominator_check。
- relationship_strength grading 存在。
- 标准输出表格模板存在。
- `mod=POST` 不得误判为 HTTP method。
- strategy recall batch 必须标记 `selection_bias_risk`。

## 未做事项

- 未访问真实平台。
- 未调用 DataAgent。
- 未修改 auth / gateway。
- 未重新打包 release。
- 未提交 git。

## 是否影响 release 打包

影响 release 内容候选，但不要求本轮重新打包。若后续将 Batch Risk Clustering Analysis Pack 纳入 release，必须先运行 release preflight。
