# Account Risk Data Source Registry v1

## Purpose

This registry lists account-risk data sources that can support L1 batch shallow lookup for Batch Risk Clustering Analysis Pack.

It is an ability index only. This document does not execute Hive SQL, call DataAgent, access real platforms, or authorize direct disposition.

Dennis Agent responsibility:

- explain which sources are useful;
- map sources to cluster features and evidence gaps;
- interpret aggregate / sampled results;
- produce risk hypotheses, representative sampling, evidence cards, and strategy suggestions.

DataAgent / Hive responsibility:

- batch feature extraction;
- aggregation;
- baseline / control group comparison;
- source freshness and permission checks.

Sensitive fields such as phone, identity number, real-name fields, credential material and raw request payloads must not be output in plaintext. IP can be used as an internal risk entity or aggregated feature, but should be masked or bucketed when shared outside the controlled analysis scope.

## Source Selection Principle

Use this registry as a source-priority map, not a raw table list.

Selection order:

1. Pick the capability-domain main table first.
2. Add auxiliary tables only when the batch question requires their specific field family, time granularity, or evidence boundary.
3. Treat L1 source outputs as shallow profile / aggregation evidence.
4. Route deep validation to representative cases, abnormal A -> B matrix rows, or the next DataAgent/Hive query plan.

No source below can directly authorize disposal. High-precision tags and admin histories still require current-batch behavior, time alignment, and false-positive review before strong judgement.

## Capability Domain 1: 通用风控特征宽表

主表：`ks_rc_arch.antispam_feature_map_default_partitioned`

辅助表：

- `ks_raw_log_v2.antispam_feature_map_partitioned`
- `ks_rc_bs.account_security_basic_info`

选择依据：

- 查询量最高，约 1115 次/月。
- 核心热门依赖表，适合作为批量 L1 浅查默认入口。

主表优先使用场景：

- 批量风险浅查。
- TOP 维度下探。
- 通用风控画像。
- A→B 有向相关矩阵基础字段。
- 多场景 batch_feature_table 的基础字段填充。

辅助表触发条件：

- `ks_raw_log_v2.antispam_feature_map_partitioned`：需要更原始的 feature map、字段缺失排查、特征口径对齐或主表聚合口径不够透明时使用。
- `ks_rc_bs.account_security_basic_info`：问题聚焦 ATO、账号安全基础画像、登录安全摘要或账号安全侧 profile 时补充。

| table_name | role | grain | freshness | field_richness | applicable_scenarios | notes |
|---|---|---|---|---|---|---|
| `ks_rc_arch.antispam_feature_map_default_partitioned` | main | user / device / feature snapshot | 快照 / 分区 | 高 | ATO, 虚假账号, 协议, 群控, 策略评估, 批量分簇 | 优先入口；特征含义和分区日期必须确认；只作为画像 / 特征证据，不可直接处置。 |
| `ks_raw_log_v2.antispam_feature_map_partitioned` | auxiliary | user / device / feature snapshot | 快照 / 分区 | 高 | ATO, 虚假账号, 协议, 群控, 批量分簇 | 用于主表口径复核和字段下探；字段缺失不能直接当作无风险。 |
| `ks_rc_bs.account_security_basic_info` | auxiliary | user snapshot | 日增量 / 快照 | 高 | ATO, 账号安全, 策略评估, 批量分簇 | 账号安全 profile 辅助证据；不能单独支撑强 ATO 结论。 |

## Capability Domain 2: 用户基础属性

主表：`kscdm.dim_ks_user_all`

辅助表：

- `ks_rc_bs.register_new_feature_wide_di`
- `ks_dw_app.ptc_user_all_wide_df`
- `ks_rc_bs.register_antispam_user_all`

选择依据：

- 查询量约 1230 次/月。
- 730 天周期，覆盖最全。
- 适合作为用户基础画像和 baseline / denominator 主入口。

主表优先使用场景：

- 用户基础画像。
- 账号生命周期。
- 人群 denominator / baseline。
- 真人 / 虚假账号辅助判断。
- 批量分簇中的用户维度公共字段补齐。

辅助表触发条件：

- `ks_rc_bs.register_new_feature_wide_di`：需要注册时点画像、注册环境、注册风险特征时使用。
- `ks_dw_app.ptc_user_all_wide_df`：需要更宽用户画像、活跃/留存/业务属性或对照组特征时使用。
- `ks_rc_bs.register_antispam_user_all`：需要注册反作弊标签、注册风险辅助判断时使用。

| table_name | role | grain | freshness | field_richness | applicable_scenarios | notes |
|---|---|---|---|---|---|---|
| `kscdm.dim_ks_user_all` | main | user | 全量 / 730 天周期 / 维表快照 | 高 | ATO, 虚假账号, 群控, 策略评估, 批量分簇 | 基础画像和 denominator 优先；不是风险标签表，不可直接处置。 |
| `ks_rc_bs.register_new_feature_wide_di` | auxiliary | user / registration event | 日增量 | 高 | 虚假账号, 注册作弊, 群控, 批量分簇 | 关注注册时间窗口；老账号需结合当前行为。 |
| `ks_dw_app.ptc_user_all_wide_df` | auxiliary | user | 日快照 | 高 | ATO, 虚假账号, 活动套利, baseline, 批量分簇 | 画像字段丰富；敏感字段需受控输出。 |
| `ks_rc_bs.register_antispam_user_all` | auxiliary | user | 全量 / 快照 | 中 | 虚假账号, 注册作弊, 策略评估 | 标签/分数是辅助证据；需确认高准还是高召。 |

## Capability Domain 3: 登录 / 账号安全行为

主表：`ks_raw_log_v3.infra_user_action_log`

辅助表：

- `ks_rc_bs.ks_account_login_basic_info`
- `ks_rc_bs.user_login_infos`

选择依据：

- 9999 天全量历史。
- 查询约 786 次/月。
- 覆盖登录、账号安全链路和用户行为动作，适合 ATO 研判和批量行为链路归因。

主表优先使用场景：

- 登录成功 / 失败。
- 改密登录。
- 登录设备 / IP。
- 账号安全链路。
- ATO 批量浅查。
- login_success → downstream abnormal action 的 A→B 有向相关。

辅助表触发条件：

- `ks_rc_bs.ks_account_login_basic_info`：需要登录基础明细、登录方法、设备/IP、失败原因、ATO 链路字段时使用。
- `ks_rc_bs.user_login_infos`：需要用户级登录摘要、最新登录上下文或 L1 聚合字段时使用。

| table_name | role | grain | freshness | field_richness | applicable_scenarios | notes |
|---|---|---|---|---|---|---|
| `ks_raw_log_v3.infra_user_action_log` | main | action / event | 全量 / 原始日志 | 高 | ATO, 行为链路, 协议, 群控, 批量分簇 | 先聚合再解释；动作语义需确认；不能输出原始日志全文。 |
| `ks_rc_bs.ks_account_login_basic_info` | auxiliary | user / login event | 日增量 / 明细 | 高 | ATO, 撞库, OAuth/一键登录接管, 批量分簇 | 关注登录方法、设备、IP、时间顺序；超窗 no_data 是 source_gap。 |
| `ks_rc_bs.user_login_infos` | auxiliary | user / login summary | 日增量 / 快照 | 中 | ATO, 登录环境聚集, 账号安全 | 适合 L1 计数和最新上下文；不足以单独支撑 token 链路结论。 |

## Capability Domain 4: Token / Web / Server 链路

主表：`ks_raw_log_v3.risk_web_server_log_proto`

辅助表：

- `ks_origin_risk_sf_log.passport_web_token_check`

选择依据：

- 专注风控精简日志。
- 协议治理场景核心来源。
- 适合补齐 Web/H5/serverlog/前后端链路断裂证据。

主表优先使用场景：

- 协议直调。
- Web/H5 链路。
- serverlog 聚合。
- 前后端链路断裂补证。
- endpoint / UA / app_version / response code 的 TOP 下探。

辅助表触发条件：

- `ks_origin_risk_sf_log.passport_web_token_check`：需要 token 检查状态、token 生命周期、token 异常或 Web 账号接管链路时使用。

| table_name | role | grain | freshness | field_richness | applicable_scenarios | notes |
|---|---|---|---|---|---|---|
| `ks_raw_log_v3.risk_web_server_log_proto` | main | request / server event | 实时/日增量日志 | 高 | 协议, 反爬, Web/H5 链路, 接口激增, 批量分簇 | 不输出 raw payload/header；只输出 endpoint、UA、版本、状态码、计数和派生比例。 |
| `ks_origin_risk_sf_log.passport_web_token_check` | auxiliary | request / token event | 日增量 / 原始链路 | 高 | ATO, token 异常, Web 接管, OAuth/Harmony | token 字段敏感；只输出状态、计数、异常类型和派生信号。 |

## Capability Domain 5: Admin / 判罚日志

主表：`ks_raw_log_v3.passport_action_log`

辅助表：

- `ks_db_origin.gifshow_admin_user_log_dt_snapshot`

选择依据：

- admin 核心操作日志。
- 9999 天全量。
- 适合解释档案中心操作、判罚历史、人工/系统处置链路。

主表优先使用场景：

- 档案中心核心操作。
- 用户分析。
- admin 行为。
- 判罚记录。
- 账号处置历史。
- ATO 改密 / 换绑 / 申诉相关动作复核。

辅助表触发条件：

- `ks_db_origin.gifshow_admin_user_log_dt_snapshot`：需要 admin 用户日志快照、长期处置历史、误伤复核或策略评估回看时使用。

| table_name | role | grain | freshness | field_richness | applicable_scenarios | notes |
|---|---|---|---|---|---|---|
| `ks_raw_log_v3.passport_action_log` | main | action | 全量 / 原始日志 | 中 | ATO, 改密/换绑/申诉, 策略评估, 判罚复核 | admin/action log 是事件证据；需要确认 actor、action_type、时间顺序。 |
| `ks_db_origin.gifshow_admin_user_log_dt_snapshot` | auxiliary | user / admin action snapshot | 快照 | 中 | 判罚复核, 误伤评估, 策略评估 | 解释历史处置和人工操作；不是当前批次风险事实本身。 |

## Capability Domain 6: 虚假账号标签

主表：`ks_rc_bs.fake_account_tag_all_summary_snapshot`

辅助表：

- `ks_rc_bs.fake_account_tag_all_detail_snapshot`
- `ks_rc_bs.fake_account_tag_di`
- `ks_rc_bs.fake_account_tag_online_detail`
- `ks_rc_bs.fake_account_tag_offline_detail`
- `ks_rc_bs.fake_account_high_recall_snapshot`

选择依据：

- summary 表查询约 161 次/月。
- 适合作为虚假账号标签 L1 主入口。
- 其他表按高召 / 高准 / 在线 / 离线 / 日增量需要选择。

主表优先使用场景：

- 虚假账号标签总览。
- 注册 / 登录作恶辅助判断。
- 下游作恶聚合。
- 批量分簇。
- 策略验证。
- 误伤排查。

辅助表触发条件：

- `ks_rc_bs.fake_account_tag_all_detail_snapshot`：需要标签明细、标签来源、标签组合或 cluster evidence card 时使用。
- `ks_rc_bs.fake_account_tag_di`：需要日增量、时间对齐或最近新增标签时使用。
- `ks_rc_bs.fake_account_tag_online_detail`：需要在线侧标签、实时策略验证或在线误伤排查时使用。
- `ks_rc_bs.fake_account_tag_offline_detail`：需要离线归因、批量复核或离线模型/规则解释时使用。
- `ks_rc_bs.fake_account_high_recall_snapshot`：需要扩召、举一反三、召回面评估时使用；必须标记高误伤风险。

| table_name | role | grain | freshness | field_richness | applicable_scenarios | notes |
|---|---|---|---|---|---|---|
| `ks_rc_bs.fake_account_tag_all_summary_snapshot` | main | user / tag summary snapshot | 快照 | 高 | 虚假账号, 下游作恶, 策略评估, 批量分簇 | 主入口；summary 标签需解释高准/高召和时效，不可直接处置。 |
| `ks_rc_bs.fake_account_tag_all_detail_snapshot` | auxiliary | user / tag detail snapshot | 快照 | 高 | 虚假账号, 群控, 下游作恶, 误伤排查 | 明细可支持 cluster evidence；仍需当前批次行为验证。 |
| `ks_rc_bs.fake_account_tag_di` | auxiliary | user / tag event | 日增量 | 高 | 虚假账号, 批量分簇, 时间对齐 | 适合验证标签新增与风险事件时序。 |
| `ks_rc_bs.fake_account_tag_online_detail` | auxiliary | user / online tag detail | 实时 / 在线 | 高 | 虚假账号, 在线策略评估, 误伤排查 | 在线标签需区分高准/高召和策略口径；可辅助但不直接强判。 |
| `ks_rc_bs.fake_account_tag_offline_detail` | auxiliary | user / offline tag detail | 离线 / 快照 | 高 | 虚假账号, 离线归因, 策略复盘 | 离线标签适合批量分析和复盘，不等于在线处置依据。 |
| `ks_rc_bs.fake_account_high_recall_snapshot` | auxiliary | user snapshot | 快照 | 中 | 虚假账号, 召回扩展, 举一反三 | 高召来源必须标 `false_positive_risk=high`；只作为扩召候选。 |

## Evidence Boundary

- Registry membership does not mean a source is available or permitted for a given task.
- DataAgent/Hive query plan must include permission, freshness, and time-window checks.
- High recall sources must be marked with false-positive risk.
- Admin or historical tags are context / auxiliary evidence unless tied to current batch behavior.
- No field from these sources should be copied as raw platform response into user-facing output.
