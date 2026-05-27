# Batch Risk Clustering Methodology v1

## 1. Method Goal

Batch clustering converts a flat case list into risk clusters, representative samples, abnormal correlations, evidence gaps and strategy actions.

It must not turn similarity into a gang conclusion without join keys or shared infrastructure evidence.

## 2. Workflow

1. Validate batch schema and threshold mode.
2. Normalize entities and time windows.
3. Generate L1 wide table / profile shallow query plan.
4. Use `batch_feature_table` to run TOP dimension drilldown.
5. Run frequent pattern / contribution analysis.
6. Build cluster candidates by dimension.
7. Build abnormal A -> B correlation matrix.
8. Compare with baseline if available; mark `baseline_missing` if not.
9. Select representative samples.
10. Build cluster evidence cards.
11. Produce pattern summary and hypotheses.
12. Separate current evidence, historical similar pattern and missing evidence.
13. Produce follow-up plan and strategy / monitoring suggestions.

## 2A. L1 Batch Feature Layer

Use `batch_l1_feature_query_contract_v1.md` before abnormal matrix construction.

L1 layer output:

- `batch_feature_table`.
- `top_dimension_summary`.
- `frequent_pattern`.
- `contribution_score`.

DataAgent/Hive can later extract and aggregate this layer. Dennis Agent only plans, interprets, clusters and recommends.

L1 results feed:

- abnormal A -> B directed correlation matrix.
- cluster hints.
- representative case sampling.
- cluster evidence cards.
- expansion / strategy / monitoring candidates.

## 3. Entity Cluster

Cluster by:

- `user_id`
- `device_id`
- `ip`
- `phone_hash`
- `app_version`
- `channel`
- `campaign_id`
- `interface`
- `strategy_id`
- `login_method`
- `entry_source`

Boundary:

- UID / DID / IP are internal risk analysis entity fields.
- Phone plaintext must not be output; use `phone_hash` or safe_ref.
- Shared entity can support a cluster, but risk conclusion still needs behavior or source evidence.

## 4. Time Cluster

Cluster by:

- 集中爆发.
- 周期性.
- 活动窗口.
- 夜间 / 异常时间段.
- 策略上线前后.
- 版本发布前后.

Boundary:

- 时间集中是 risk clue, not final evidence.
- Campaign windows and product launches can create normal bursts.

## 5. Behavior Cluster

Cluster by:

- 登录.
- 发布.
- 评论.
- 私信.
- 关注.
- 提现.
- 下单.
- 助力.
- 接口请求.
- 前端行为缺失.
- 高风险动作链路.

Boundary:

- Behavior event proves occurrence, not necessarily malicious control.
- User claim and model inference cannot replace behavior evidence.

## 6. Environment Cluster

Cluster by:

- 设备型号.
- 系统版本.
- 客户端版本.
- 异常 mod 字段.
- 模拟器.
- root / hook / frida.
- 代理 / VPN.
- 异常网络环境.
- 多账号共设备.
- 多设备共账号.

Boundary:

- Device abnormality is supporting evidence, not standalone cheating / ATO conclusion.
- `mod=POST` or similar field names must be interpreted by field semantics; do not misread as HTTP method without source definition.

## 7. Strategy Cluster

Cluster by:

- 策略命中.
- 命中原因.
- 命中强度.
- 处置动作.
- 误伤反馈.
- 策略命中后行为.
- 策略未命中但异常集中的缺口.

Boundary:

- Strategy hit is evidence of model/rule response, not final human risk judgement.
- Strategy recall batches need secondary attribution and false-positive review.

## 8. Entry / Path Cluster

Cluster by:

- 扫码.
- OAuth.
- 一键登录.
- H5.
- Web.
- App.
- 协议直调.
- 外链入口.
- 投放渠道.
- 活动入口.

Boundary:

- Login or entry path must be linked to downstream abnormal action before being used as attack-path evidence.
- ATO Harmony / OAuth / one-key login must not be collapsed into credential stuffing.

## 9. Interface / Request Cluster

Cluster by:

- 请求量突增.
- 前端行为缺失.
- UA 异常.
- 版本异常.
- endpoint 集中.
- 参数模式异常.
- 请求时间间隔异常.
- response code 分布异常.

Boundary:

- Interface spike may be crawler, protocol direct call, retry storm, product launch or campaign traffic.
- Need frontend activity, UA, request interval, endpoint and response-code evidence before strong conclusion.

## 10. Abnormal Correlation Cluster

Use `abnormal_correlation_matrix_v1.md`.

Abnormal correlation is one of the core methods:

- A 条件下 B 是否异常集中.
- 是否高于正常基线.
- 是否覆盖足够比例.
- 是否解释工具链、基础设施、入口或策略漏洞.
- 是否单向或双向.

Without baseline, output `baseline_missing`.

Inputs from the L1 layer:

- TOP dimension concentration can create A -> B candidate relations.
- Frequent patterns with high contribution become candidate matrix rows.
- Contribution score can prioritize validation, but cannot upgrade to final risk judgement by itself.

## 11. Evidence Boundaries

- current batch facts must come from `current_input` or `current_task_observation`.
- historical case can be similar pattern / hypothesis only.
- no_data 不能作为无风险反证.
- blocked/timeout/partial source 必须 source_gap.
- 不能仅凭相似性判断同团伙.
- 高频组合 / 高贡献度 only creates cluster hint or candidate feature hint.
- 身份证、手机号、实名信息 and credential-like fields are controlled auxiliary evidence and must not be output in plaintext.
