# Browser-Backed Fixed Actions Text Demo V1

This is an offline text demo. It does not start the browser-backed service, access real platforms, call DataAgent/Hive, read auth material, or execute source actions.

- cases_total: `10`
- cases_passed: `10`
- cases_failed: `0`
- default_runtime_routing_false: `true`
- real_platform_called: `false`
- dataagent_called: `false`
- hive_called: `false`

## BBFA-DEMO-001

- user_query: 帮我判断 user_id=2871834924 是否疑似 ATO
- expected_source_plan: `login_logs_search -> archives_user_profile -> archives_user_analysis -> track_analysis_check_data_ready`
- expected_orchestration: ATO multi-source plan, not login logs only.
- actual_source_plan_or_template: `login_logs_search -> archives_user_profile -> archives_user_analysis -> track_analysis_check_data_ready`
- expected_boundary_flags: `single_source_not_enough_for_ato, no_data_not_risk_exclusion`
- actual_boundary_flags: `login_no_data_or_window_gap_not_ato_exclusion, track_check_data_ready_not_risk_conclusion, large_response_limited_enters_source_quality, single_source_not_enough_for_ato, no_data_not_risk_exclusion, login_log_window_incomplete_possible, source_quality_required`
- should_not_do: `do_not_only_query_login_logs, do_not_make_final_judgement_without_source_quality`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

我会先按显式 source_plan 做 ATO 研判，不自动执行平台查询：login_logs_search -> archives_user_profile -> archives_user_analysis -> track_analysis_check_data_ready。登录日志用于看可见窗口内的登录时间、IP、设备和方式；档案账号画像用于确认账号当前状态和注册/状态基线；档案用户分析用于补最近操作和风险日志；Track checkDataReady 只验证设备维度数据是否可读。即使某个 source no_data，也只写入 source_quality，不能直接排除 ATO；最终只能在证据齐备后给倾向，不做单源定性。

## BBFA-DEMO-002

- user_query: 登录日志没查到，是不是就没风险？
- expected_source_plan: `login_logs_search`
- expected_orchestration: Explain login no_data/window gap as source quality, not counter-evidence.
- actual_source_plan_or_template: `login_logs_search`
- expected_boundary_flags: `no_data_not_risk_exclusion, login_log_window_incomplete_possible`
- actual_boundary_flags: `no_data_not_risk_exclusion, login_no_data_or_window_gap_not_ato_exclusion, login_log_window_incomplete_possible, source_quality_required`
- should_not_do: `do_not_output_low_risk_from_no_data, do_not_stop_multisource_plan`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

不能。这里的 source_plan 是 login_logs_search，它只能回答在线窗口和查询条件下是否有可见登录记录。no_data 代表当前 source 没返回记录，不代表没有登录、没有异常设备，也不代表没有 ATO。如果投诉或异常时间超出在线窗口，需要把 window gap 写进 missing_evidence，并用档案操作、账号画像或后续离线授权来源补证。

## BBFA-DEMO-003

- user_query: 看下这个账号画像和状态
- expected_source_plan: `archives_user_profile`
- expected_orchestration: Account profile is baseline context; not final judgement.
- actual_source_plan_or_template: `archives_user_profile`
- expected_boundary_flags: `profile_context_not_final_judgement`
- actual_boundary_flags: `profile_context_not_final_judgement, source_quality_required`
- should_not_do: `do_not_make_final_risk_judgement_from_profile_only, do_not_output_pii_strict`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

我会把这个问题收敛到账号基线 source_plan：archives_user_profile。重点看账号状态、注册/资料状态、标签或风险信息摘要，用来判断当前账号画像是否有明显背景线索。但画像是静态/近实时基线，不等于行为链路；不能仅凭账号状态正常或异常就给最终风险结论。

## BBFA-DEMO-004

- user_query: 这个账号最近有没有异常操作或风险日志？
- expected_source_plan: `archives_user_analysis`
- expected_orchestration: Use Archives user analysis; capped large response becomes partial observation.
- actual_source_plan_or_template: `archives_user_analysis`
- expected_boundary_flags: `large_response_limited_enters_source_quality, partial_observation_available`
- actual_boundary_flags: `large_response_limited_enters_source_quality, partial_observation_available, source_quality_required`
- should_not_do: `do_not_dump_raw_records, do_not_claim_full_coverage_when_limited`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

我会把 source_plan 收敛为档案中心用户分析：archives_user_analysis。它负责看最近操作和风险日志摘要，重点关注登录、改密、保护账号、冻结、直播/发布相关操作和时间分布。如果响应过大，只能输出 partial_observation_available：说明可以看到部分结构、计数或时间范围，但不能声称完整明细覆盖。下一步应缩短时间窗、降低 pageSize 或分页复查；raw records 不输出。

## BBFA-DEMO-005

- user_query: 这个账号是不是异常发布/色导导流？
- expected_source_plan: `archives_photo_search -> archives_user_profile -> archives_user_analysis`
- expected_orchestration: Publish/content branch with photo search, profile baseline, and user analysis.
- actual_source_plan_or_template: `archives_photo_search -> archives_user_profile -> archives_user_analysis`
- expected_boundary_flags: `photo_search_no_data_not_abnormal_publish_exclusion`
- actual_boundary_flags: `photo_search_no_data_not_abnormal_publish_exclusion, publish_chain_missing_evidence_must_be_explicit, source_quality_required`
- should_not_do: `do_not_output_no_abnormal_publish_from_photo_no_data, do_not_make_final_judgement`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

这个问题走发布/内容承接 source_plan：archives_photo_search -> archives_user_profile -> archives_user_analysis。photo_search 看作品/举报/发布线索，账号画像看当前账号状态，用户分析补发布前后的登录、改密、风控操作时间线。photo_search no_data 不能写成没有异常发布，只能说明该 source 在当前条件下未返回线索；最终需要结合操作链路和其他证据。

## BBFA-DEMO-006

- user_query: 这个账号有没有同设备关联账号？
- expected_source_plan: `archives_related_users -> archives_user_profile -> login_logs_search -> track_analysis_check_data_ready`
- expected_orchestration: Same-device relation is an expansion clue with cross-source validation.
- actual_source_plan_or_template: `archives_related_users -> archives_user_profile -> login_logs_search -> track_analysis_check_data_ready`
- expected_boundary_flags: `related_users_not_gang_conclusion`
- actual_boundary_flags: `related_users_not_gang_conclusion, same_device_relation_requires_cross_source_validation, source_quality_required`
- should_not_do: `do_not_label_gang_from_same_device_only, do_not_bulk_expand_without_plan`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

我会把同设备当扩散线索处理，source_plan 是 archives_related_users -> archives_user_profile -> login_logs_search -> track_analysis_check_data_ready。archives_related_users 只说明同设备关系或候选关联账号，后续要用账号画像、登录日志和 Track readiness 验证设备/时间/行为是否一致。不能因为同设备就直接写团伙，也不能无计划批量扩散。

## BBFA-DEMO-007

- user_query: 这个 eventId 为什么被拦？
- expected_source_plan: `rcp_event_detail -> rcp_event_feature_list`
- expected_orchestration: Event attribution first, feature list second when exact event identity is available.
- actual_source_plan_or_template: `rcp_event_detail -> rcp_event_feature_list`
- expected_boundary_flags: `event_detail_not_policy_tree_asset_lookup, strategy_hit_not_final_judgement`
- actual_boundary_flags: `event_detail_not_policy_tree_asset_lookup, feature_list_partial_only_feature_group_summary, strategy_hit_not_final_judgement, attribution_not_cheating_judgement, source_quality_required`
- should_not_do: `do_not_jump_to_policy_tree_asset_lookup, do_not_make_final_risk_judgement`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

这个是 RCP 事件归因，不是策略树资产查询，source_plan 是 rcp_event_detail -> rcp_event_feature_list。先用 event detail 确认事件时间、策略命中、反馈和关键实体；再用 feature list 看特征分组/可用部分观察。策略命中只能说明这个事件触发了某些策略条件，不能单独推导用户最终风险。

## BBFA-DEMO-008

- user_query: feature list 只拿到 partial，能不能说明完整特征？
- expected_source_plan: `rcp_event_feature_list`
- expected_orchestration: Partial feature observation can summarize groups but cannot claim full detail coverage.
- actual_source_plan_or_template: `rcp_event_detail -> rcp_event_feature_list`
- expected_boundary_flags: `feature_list_partial_only_feature_group_summary, partial_observation_available`
- actual_boundary_flags: `event_detail_not_policy_tree_asset_lookup, feature_list_partial_only_feature_group_summary, strategy_hit_not_final_judgement, attribution_not_cheating_judgement, partial_observation_available, do_not_upgrade_partial_to_strong_evidence, source_quality_required`
- should_not_do: `do_not_claim_complete_feature_coverage, do_not_output_raw_feature_values`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

不能说明完整特征。source_plan 是 rcp_event_detail -> rcp_event_feature_list，partial_observation_available 只能作为部分观察。可以引用 feature group、估算计数、关键实体和 source_quality.large_response_limited，但要明确 raw feature values 和完整明细不可见。如果需要完整覆盖，需要更窄查询或专门的有界提取，不应把 partial 升级成强证据。

## BBFA-DEMO-009

- user_query: 这条策略挂在哪棵策略树？
- expected_source_plan: `rcp_policy_tree_lookup`
- expected_orchestration: Policy-tree lookup is governance context only.
- actual_source_plan_or_template: `rcp_policy_tree_lookup`
- expected_boundary_flags: `policy_tree_asset_not_event_hit_path`
- actual_boundary_flags: `policy_tree_asset_not_event_hit_path, policy_tree_lookup_not_single_case_risk_evidence, source_quality_required`
- should_not_do: `do_not_treat_policy_tree_as_event_hit, do_not_make_user_risk_judgement`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

这个走策略资产治理，不是单案事件归因，source_plan 是 rcp_policy_tree_lookup。policyTree lookup 用来解释 policyCode 所在策略树、版本和节点上下文，帮助理解策略资产关系。它不能证明某个 user_id 或 eventId 实际命中过该策略；事件命中要回到 rcp_event_detail / feature list 或策略命中入口。

## BBFA-DEMO-010

- user_query: 命中过策略，能不能直接定性风险？
- expected_source_plan: `rcp_event_detail -> rcp_event_feature_list`
- expected_orchestration: Strategy hit is auxiliary evidence; risk judgement needs cross-source context.
- actual_source_plan_or_template: `rcp_event_detail -> rcp_event_feature_list`
- expected_boundary_flags: `strategy_hit_not_final_judgement`
- actual_boundary_flags: `strategy_hit_not_final_judgement, source_quality_required`
- should_not_do: `do_not_make_final_judgement_from_strategy_hit_only`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

不能直接定性。source_plan 是 rcp_event_detail -> rcp_event_feature_list，策略命中只是一类辅助证据。我会先看事件详情和 feature list 的可用观察，再把登录日志、账号画像、用户操作或发布链路作为交叉验证。如果只有策略命中，没有时间线、行为链和 source_quality 支撑，只能输出风险线索或待补证，不能给最终处置结论。
