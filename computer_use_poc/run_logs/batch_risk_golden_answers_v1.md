# Batch Risk Golden Answers v1

## 本轮目标

为 Batch Risk Clustering Analysis Pack 增加用户体感 golden answers，验证回答是否像资深风控专家，而不是模板化罗列字段。

## 新增文件

- `computer_use_poc/batch_risk_clustering/batch_risk_golden_answers_v1.md`
- `computer_use_poc/run_logs/batch_risk_golden_answers_v1.md`

## 是否修改模板

未修改模板。

原因：

- `batch_risk_response_template_v1.md` 已包含批量结论摘要、处理模式、分簇结果、异常相关性矩阵、代表样本证据卡、攻击路径假设、误伤与反证、补证计划、举一返三和不可强判声明。
- `answer_experience_templates.md` 也已补齐异常相关性矩阵深度字段。

## 3 条 Golden Answer 摘要

### 1. ATO 混合批次

理想回答要求：

- 不能写成单一 ATO 簇。
- 至少拆出撞库候选、Harmony/OAuth/一键登录接管、user_claim/source_gap、正常换机/误伤边界。
- 进入 `batch_clustering_mode`，不逐个在线查。
- 输出异常相关性矩阵、3-5 个代表样本、证据边界、缺证计划和不可强判项。

### 2. 接口请求量激增

理想回答要求：

- 不能直接强判爬虫。
- 同时区分爬虫/协议直调、业务活动波动、监控口径变化、策略上线或版本发布影响。
- 输出 interface -> request_pattern / frontend_activity_gap、app_version -> request_spike、user/device cluster -> request_pattern。
- 缺前端行为、UA、版本、用户分布、时间基线时标 baseline_missing / denominator_required。

### 3. 活动渠道假量 / 套利

理想回答要求：

- 不能直接强判渠道作假。
- 输出 channel -> reward_claim / low_retention / device_reuse / low_real_behavior 和 campaign -> abnormal_conversion。
- 没有渠道全量分母时只能 batch_internal_concentration，不能 strong enrichment。
- 策略建议必须 candidate only / do_not_auto_launch，并包含灰度验证、监控指标和人工复核边界。

## Common Bad Answer 摘要

典型差回答包括：

- 泛泛建议查 IP / 设备 / 日志，没有明确结论和分簇。
- 直接强判爬虫 / 套利 / ATO。
- 把所有 case 混成一个风险簇。
- 没有 baseline 却写 strong enrichment。
- 只复述策略命中原因。
- 把 no_data 当无风险反证。
- 把 user_claim 当 strong evidence。
- 自动建议全量拦截或拉黑。

## 是否发现 response template 仍需修补

未发现必须修补项。

可选增强：

- 后续可在 response template 中增加“用户体感短答版”示例，但当前 golden answers 已可作为示范材料。

## 是否建议进入 release patch 候选

建议进入 release patch 候选。

理由：

- golden answers 覆盖 ATO mixed batch、interface spike、activity/channel arbitrage 三类高频批量场景。
- 每条均包含 ideal answer、bad answer、scoring notes、调用边界和不可强判边界。
- 未包含真实平台数据、真实用户明细或敏感凭证。

进入 release 前仍需运行 release preflight。

## 未做事项

- 未访问真实平台。
- 未调用 DataAgent。
- 未修改 auth / gateway。
- 未重新打包 release。
- 未提交 git。
