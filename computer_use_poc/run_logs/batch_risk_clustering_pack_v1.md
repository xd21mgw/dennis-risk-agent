# Batch Risk Clustering Pack v1

## 本轮目标

新增 Dennis Risk Agent 能力包：Batch Risk Clustering Analysis Pack。目标是解决从单 case 研判到多 case 批量研判的核心跃迁，沉淀分簇、代表样本抽样、共性模式总结、攻击路径假设、证据缺口、举一返三和策略建议模板。

## 新增文件列表

- `computer_use_poc/batch_risk_clustering/README.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_case_schema_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_threshold_policy_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_clustering_methodology_v1.md`
- `computer_use_poc/batch_risk_clustering/abnormal_correlation_matrix_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_representative_sampling_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_evidence_card_template_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_pattern_summary_template_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_response_template_v1.md`
- `computer_use_poc/batch_risk_clustering/batch_risk_runtime_validation_cases_v1.yaml`
- `computer_use_poc/run_logs/batch_risk_clustering_pack_v1.md`

## 修改文件列表

- `computer_use_poc/README.md`
- `computer_use_poc/smoke_tests.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/answer_experience_templates.md`

## 阈值策略摘要

- 1-2 个实体：`single_entity_execution_mode`，可逐个深查。
- 3-4 个实体：`small_multi_case_execution_mode`，可全量深查 + cross-case comparison。
- 5-9 个实体：`small_batch_mode`，先轻量分组，再决定全查或抽 3-5 个代表样本。
- 10-49 个实体：`batch_clustering_mode`，不逐个在线查，先分簇、异常相关性矩阵、代表样本抽样。
- 50-499 个实体：`large_batch_aggregation_mode`，默认 aggregation / DataAgent-Hive query plan。
- 500+ 个实体：`alert_batch_or_population_analysis_mode`，只做批次级分布、异常相关性、抽样和策略建议。

核心边界：

- 5 个以下可全量深查。
- 10+ 默认 batch_clustering_mode。
- 50+ 默认 aggregation / DataAgent-Hive query plan。
- DataAgent 只能作为 Hive / 数仓取数分析能力。

## 不可预测矩阵 / 异常相关性矩阵摘要

“不可预测矩阵”在本项目中定义为异常相关性矩阵，不是不确定性矩阵，也不是预测误差矩阵。

核心判断：

- A 条件下 B 是否异常集中。
- 是否高于正常基线；无基线必须标 `baseline_missing`。
- 是否覆盖批次足够比例。
- 是否解释工具链、基础设施、入口、策略漏洞或套利路径。
- 是否单向或双向成立。

异常相关性只能生成候选风险模式，不能替代 raw evidence。不能仅凭相似性判断同团伙。

## 分簇方法摘要

分簇维度：

- entity cluster：user_id、device_id、ip、phone_hash、app_version、channel、campaign_id、interface、strategy_id、login_method、entry_source。
- time cluster：集中爆发、周期性、活动窗口、夜间/异常时间段、策略上线前后、版本发布前后。
- behavior cluster：登录、发布、评论、私信、关注、提现、下单、助力、接口请求、前端行为缺失、高风险动作链路。
- environment cluster：设备型号、系统版本、客户端版本、异常 mod、模拟器、root/hook/frida、代理/VPN、异常网络、多账号共设备、多设备共账号。
- strategy cluster：策略命中、命中原因、强度、处置动作、误伤反馈、命中后行为、未命中缺口。
- entry/path cluster：扫码、OAuth、一键登录、H5、Web、App、协议直调、外链入口、投放渠道、活动入口。
- interface/request cluster：请求量突增、前端行为缺失、UA 异常、版本异常、endpoint 集中、参数模式异常、请求间隔异常、response code 分布异常。

## 代表样本抽样摘要

- 5-9 个实体：可建议全量深查或抽 3-5 个代表样本。
- 10+ 个实体：默认抽 3-5 个代表样本，不逐个深查。

代表样本类型：

- high-confidence positive sample。
- boundary / ambiguous sample。
- suspected false positive sample。
- high-impact sample。
- source-gap sample。

每个代表样本都要生成 evidence card。

## Evidence Type Separation 摘要

必须区分：

- raw evidence。
- derived evidence。
- model inference。
- user claim。
- missing evidence。
- blocked evidence。
- historical similar pattern。

强制规则：

- manual_input 不能单独支撑 strong conclusion。
- model_inference 不能当 raw evidence。
- user_claim 不能单独支撑强结论。
- no_data 不能作为无风险反证。
- blocked/timeout/partial source 必须 source_gap。
- 历史 case 不能污染当前批次事实证据。

## Validation Cases 摘要

新增 15 个 YAML validation cases：

- single entity ATO execution。
- four entity full investigation。
- five entity small batch。
- ten entity batch clustering。
- 100 entity Hive plan。
- ATO credential stuffing candidate。
- ATO Harmony / OAuth candidate。
- device group control batch。
- protocol downgrade batch。
- interface traffic spike。
- activity arbitrage batch。
- alert secondary attribution。
- strategy recommendation with user ids。
- context contamination new batch。
- no_data not counter evidence。

## Smoke Tests 摘要

新增 BATCH-RISK-001 到 BATCH-RISK-016，覆盖目录存在性、schema、阈值策略、异常相关性矩阵、代表样本、证据分层、模板、validation YAML、10+ 分簇、50+ 聚合、no_data/source_gap、历史污染、相似性同团伙边界和 DataAgent/Hive 边界。

## 未做事项

- 未访问真实平台。
- 未调用 DataAgent。
- 未修改 auth / gateway。
- 未重新打包 release。
- 未提交 git。
- 未将能力包接入真实 runtime enforce / execution。

## 后续说明

后续如要 runtime 生效，需要 overlay 或重新打 patch release，并在入口层将 threshold policy 纳入真实 routing guard。
