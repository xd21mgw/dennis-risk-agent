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

## Registry Table

| group | table_name | capability_domain | grain | freshness | field_richness | applicable_scenarios | notes |
|---|---|---|---|---|---|---|---|
| 1. 通用风控特征宽表 / 画像底表 | `ks_rc_arch.antispam_feature_map_default_partitioned` | risk feature wide table | user / device / feature snapshot | partitioned snapshot | high | ATO, 虚假账号, 协议, 群控, 策略评估, 批量分簇 | Feature meaning and partition date must be checked; high-risk feature is auxiliary evidence, not direct disposal basis. |
| 1. 通用风控特征宽表 / 画像底表 | `ks_raw_log_v2.antispam_feature_map_partitioned` | raw risk feature map | user / device / feature snapshot | partitioned snapshot | high | ATO, 虚假账号, 协议, 群控, 批量分簇 | Rawer feature view; validate field definitions and missingness before enrichment claims. |
| 1. 通用风控特征宽表 / 画像底表 | `ks_rc_bs.account_security_basic_info` | account security profile | user snapshot | snapshot / daily | high | ATO, 账号安全, 策略评估, 批量分簇 | Good L1 profile source; not enough alone for strong ATO conclusion. |
| 2. 用户基础属性 / 注册画像 | `ks_rc_bs.register_new_feature_wide_di` | registration feature wide table | user / registration event | daily incremental | high | 虚假账号, 注册作弊, 群控, 批量分簇 | Time window around registration matters; old account drift needs latest profile join. |
| 2. 用户基础属性 / 注册画像 | `ks_rc_bs.register_antispam_user_all` | registration anti-spam profile | user | full / snapshot | medium | 虚假账号, 注册作弊, 策略评估 | Tag or score is auxiliary; check if high-precision or recall-oriented. |
| 2. 用户基础属性 / 注册画像 | `ks_dw_app.ptc_user_all_wide_df` | user base wide table | user | daily snapshot | high | ATO, 虚假账号, 活动套利, 批量分簇 | Use for baseline and normal user profile comparison; contains sensitive attributes that must be controlled. |
| 2. 用户基础属性 / 注册画像 | `kscdm.dim_ks_user_all` | user dimension | user | dimension snapshot | medium | 基础画像, baseline, 批量分簇 | Good for denominator and population control; not a risk label source. |
| 3. 登录 / 账号安全行为日志 | `ks_rc_bs.ks_account_login_basic_info` | login security behavior | user / login event | daily incremental | high | ATO, 撞库, OAuth/一键登录接管, 批量分簇 | Need login method, device, IP, time order; no_data over window is source_gap. |
| 3. 登录 / 账号安全行为日志 | `ks_raw_log_v3.infra_user_action_log` | user action log | action / event | raw log / incremental | high | ATO, 行为链路, 协议, 批量分簇 | Action semantics need validation; high volume may need aggregation. |
| 3. 登录 / 账号安全行为日志 | `ks_rc_bs.user_login_infos` | login info summary | user / login event or summary | daily / snapshot | medium | ATO, 登录环境聚集, 账号安全 | Useful for L1 counts and latest login context; not enough for token chain conclusion. |
| 4. Token / Web / Server 行为链路 | `ks_origin_risk_sf_log.passport_web_token_check` | web token check chain | request / token event | raw / incremental | high | ATO, token 异常, Web 接管, OAuth/Harmony | Token fields are sensitive; output only status, counts, and derived signals. |
| 4. Token / Web / Server 行为链路 | `ks_raw_log_v3.risk_web_server_log_proto` | web/server risk request log | request / server event | raw / incremental | high | 协议, 反爬, Web 行为链路, 接口激增 | Raw payload/header must not be output; aggregate endpoint, UA, version, response code. |
| 5. Admin / 档案 / 判罚日志 | `ks_raw_log_v3.passport_action_log` | account admin / passport action | action | raw / incremental | medium | ATO, 改密/换绑/申诉, 策略评估 | Admin action is event evidence; check actor and action type before inference. |
| 5. Admin / 档案 / 判罚日志 | `ks_db_origin.gifshow_admin_user_log_dt_snapshot` | admin user log snapshot | user / admin action snapshot | snapshot | medium | 判罚复核, 误伤评估, 策略评估 | Human/admin log can explain disposition history; not current-batch risk evidence by itself. |
| 6. 虚假账号标签 / 大盘 / 下游作恶 | `ks_rc_bs.fake_account_tag_all_summary_snapshot` | fake account tag summary | user / tag summary snapshot | snapshot | high | 虚假账号, 下游作恶, 策略评估, 批量分簇 | Summary tags need precision/recall interpretation. |
| 6. 虚假账号标签 / 大盘 / 下游作恶 | `ks_rc_bs.fake_account_tag_all_detail_snapshot` | fake account tag detail | user / tag detail snapshot | snapshot | high | 虚假账号, 群控, 下游作恶 | Detail tags can be cluster hints; avoid direct disposal without current evidence. |
| 6. 虚假账号标签 / 大盘 / 下游作恶 | `ks_rc_bs.fake_account_tag_di` | fake account tag daily | user / tag event | daily incremental | high | 虚假账号, 批量分簇 | Daily tag freshness helps time alignment. |
| 6. 虚假账号标签 / 大盘 / 下游作恶 | `ks_rc_bs.fake_account_tag_online_detail` | online fake account detail | user / online tag detail | near-real-time / online | high | 虚假账号, 在线策略评估 | Check whether online tag is high-precision or recall-oriented. |
| 6. 虚假账号标签 / 大盘 / 下游作恶 | `ks_rc_bs.fake_account_tag_offline_detail` | offline fake account detail | user / offline tag detail | offline snapshot | high | 虚假账号, 离线归因 | Offline tag is useful for batch analysis, not direct live action. |
| 6. 虚假账号标签 / 大盘 / 下游作恶 | `ks_rc_bs.fake_account_high_recall_snapshot` | high recall fake account | user snapshot | snapshot | medium | 虚假账号, 召回扩展 | High recall means false-positive risk must be marked. |
| 6. 虚假账号标签 / 大盘 / 下游作恶 | `ks_rc_bs.reg_check_market_all_sham_user_di` | market sham user / registration check | user / registration event | daily incremental | medium | 渠道假量, 注册作弊, 活动套利 | Use with channel and retention denominator; not standalone fraud proof. |
| 6. 虚假账号标签 / 大盘 / 下游作恶 | `ks_rc_bs.dwd_fake_account_audit_login_spam_user_all_di` | fake account audit login spam | user / audit result | daily incremental | high | 登录垃圾账号, 虚假账号, 批量分簇 | Audit result is strong auxiliary evidence if current and high precision; still verify current batch behavior. |
| 6. 虚假账号标签 / 大盘 / 下游作恶 | `ks_rc_bs.dwd_fake_account_audit_reg_spam_user_all_di` | fake account audit registration spam | user / audit result | daily incremental | high | 注册垃圾账号, 虚假账号 | Registration spam does not automatically prove current downstream action. |
| 6. 虚假账号标签 / 大盘 / 下游作恶 | `ks_rc_bs.dwd_fake_account_downstream_bad_user_all_di` | downstream bad user | user / downstream bad event | daily incremental | high | 下游作恶, 虚假账号, 策略评估 | Downstream badness supports cluster evidence when time aligned with current batch. |

## Evidence Boundary

- Registry membership does not mean a source is available or permitted for a given task.
- DataAgent/Hive query plan must include permission, freshness, and time-window checks.
- High recall sources must be marked with false-positive risk.
- Admin or historical tags are context / auxiliary evidence unless tied to current batch behavior.
- No field from these sources should be copied as raw platform response into user-facing output.

