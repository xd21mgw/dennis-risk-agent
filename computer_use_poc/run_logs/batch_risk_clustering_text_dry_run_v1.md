# Batch Risk Clustering Text Dry Run v1

## 本轮目标

对 Batch Risk Clustering Analysis Pack 做深度文本级验证，确认它不只是模板完整，而是能支撑“多 case -> 分簇 -> 代表样本 -> 异常相关性矩阵 -> 攻击路径假设 -> 补证计划 -> 策略建议”的分析闭环。

## 新增文件

- `computer_use_poc/batch_risk_clustering/batch_risk_golden_samples_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_quality_rubric_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_text_dry_run_v1.md`
- `computer_use_poc/run_logs/batch_risk_clustering_text_dry_run_v1.md`

## 是否发现当前能力包缺口

发现的是文本表达和验收强化点，不是结构性缺口：

- response template 可增加固定“cluster heterogeneity check”。
- pattern summary 可增加 `baseline_missing_count`。
- 策略建议可强制每次输出 `do_not_auto_launch`。
- golden samples 后续可转成 machine-checkable YAML，便于自动回归。

当前能力包的核心闭环是成立的。

## Golden Sample 预期输出摘要

### Group 1: ATO 混合批次

- selected_mode: `batch_clustering_mode`。
- 预期分簇：撞库候选、Harmony/OAuth/一键登录接管候选、user_claim_only/source_gap、正常换机/误伤边界。
- 代表样本：撞库候选、Harmony/OAuth 候选、source-gap、正常换机 false positive。
- 关键边界：不能粗暴写成一批 ATO，不能误把 Harmony/OAuth 写成撞库。

### Group 2: 协议降版本 / 伪造客户端

- selected_mode: `batch_clustering_mode`。
- 预期分簇：旧版本高频、DID 不一致、多版本混用、异常 mod 字段语义待确认、前端行为缺失。
- 关键边界：不能把 `mod=POST` 误读成 HTTP method。
- 补证：字段字典、版本基线、UA / endpoint / request interval / frontend activity。

### Group 3: 接口请求量激增

- selected_mode: `alert_batch_or_population_analysis_mode`。
- 预期分簇：爬虫/协议候选、业务活动波动、监控采样口径变化、区域 429 聚集。
- 关键边界：不能直接强判爬虫。
- 补证：endpoint、UA、IP/ASN、frontend gap、response code、campaign flag、采样口径归一。

### Group 4: 活动套利 / 渠道假量

- selected_mode: `large_batch_aggregation_mode`。
- 预期异常相关：channel X -> reward_claim / low_retention / device_reuse。
- 反证样本：channel Y 高奖励但正常留存，channel Z 低留存但低奖励。
- 关键边界：不能只写“渠道异常”，必须输出有方向的异常相关。

### Group 5: 内部告警批次二次归因

- selected_mode: `large_batch_aggregation_mode`。
- 预期分簇：疑似真阳性 spam publish、正常 creator 高频误伤、source timeout gap、高影响人工复核。
- 关键边界：不能重复策略命中原因当作最终结论。
- 策略建议：拆分规则、误伤豁免 / review queue、监控 true positive rate / overturn rate / timeout ratio。

## 当前能力包需要补强的点

- 在 response template 中加入“该批是否异质、是否必须拆簇”的固定检查项。
- 在 pattern summary 中加入 baseline coverage / baseline_missing_count。
- 在 strategy recommendation 中固定输出 “candidate only / do_not_auto_launch”。
- 如果后续要自动化回归，可把 golden samples 转成 YAML。

## 是否建议进入 release 打包前 preflight

建议：可以进入 release 打包前 preflight。

理由：

- 文档包不包含真实平台数据、真实用户明细或凭证。
- 能力定位、阈值策略、异常相关性矩阵、代表样本、证据分层和边界均已覆盖。
- 已明确未接真实平台、未调用 DataAgent、未修改 auth/gateway。

注意：

- 进入 release 前仍必须运行 `release_preflight_check.py`。
- 若 release 包包含本目录，应确保不带出真实 run logs、source observation、case 原始样本或敏感字段。

## 未做事项

- 未访问真实平台。
- 未调用 DataAgent。
- 未修改 auth / gateway。
- 未重新打包 release。
- 未提交 git。
