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
- expected_boundary_flags: `single_source_not_enough_for_ato, no_data_not_risk_exclusion, archives_required_for_behavior_closure_non_blocking`
- actual_boundary_flags: `login_no_data_or_window_gap_not_ato_exclusion, archives_required_for_behavior_closure_non_blocking, archives_failure_enters_partial_evidence, track_check_data_ready_not_risk_conclusion, large_response_limited_enters_source_quality, single_source_not_enough_for_ato, no_data_not_risk_exclusion, login_log_window_incomplete_possible, source_quality_required`
- should_not_do: `do_not_only_query_login_logs, do_not_skip_archives_for_ato, do_not_make_final_judgement_without_source_quality`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

我会按“控制权变化 -> 异常行为闭环 -> 扩散/策略佐证”收敛，不自动查平台。source_plan：login_logs_search -> archives_user_profile -> archives_user_analysis -> track_analysis_check_data_ready。先看登录链路是否有新设备、异地、验证或 token 变化；再用档案用户分析对齐改密、发布、关注等后置动作；最后只把 Track 活跃与数据可用性、策略命中当旁证。no_data 只进 source_quality，不能排除 ATO。档案中心若 auth_failed/no_data/timeout，也只降级为 partial evidence，不能跳过行为闭环。

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

不能。source_plan：login_logs_search。它只能说明在线窗口和当前条件下没有可见登录记录。no_data 不是无风险反证；如果客诉时间超窗，必须写 window gap。后续要用账号操作、账号画像或经授权的离线来源补控制权变化链路。

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

这个裸问只看账号基线，source_plan：archives_user_profile。重点是账号状态、注册/资料状态和风险摘要，用来判断背景线索。画像正常不等于本人操作，画像异常也不等于风险定性；行为链路要另补。

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

这个问题收敛到操作时间线，source_plan：archives_user_analysis。重点看登录、改密、保护账号、冻结、直播/发布等动作是否能串成异常行为闭环。大响应只写 partial_observation_available，不能声称完整覆盖；raw records 不输出。

## BBFA-DEMO-005

- user_query: 这个账号是不是异常发布/色导导流？
- expected_source_plan: `archives_photo_search -> archives_user_profile -> archives_user_analysis`
- expected_orchestration: Publish/content branch with photo search, profile baseline, and user analysis.
- actual_source_plan_or_template: `archives_photo_search -> archives_user_profile -> archives_user_analysis`
- expected_boundary_flags: `photo_search_no_data_not_abnormal_publish_exclusion, archives_failure_enters_partial_evidence`
- actual_boundary_flags: `photo_search_no_data_not_abnormal_publish_exclusion, archives_failure_enters_partial_evidence, publish_chain_missing_evidence_must_be_explicit, source_quality_required`
- should_not_do: `do_not_output_no_abnormal_publish_from_photo_no_data, do_not_use_archives_no_data_as_no_risk, do_not_make_final_judgement`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

导流/异常发布按“内容动作 -> 账号状态 -> 发布前后操作”看，source_plan：archives_photo_search -> archives_user_profile -> archives_user_analysis。先找作品/举报/发布线索，再看账号基线，最后对齐发布前后的登录、改密和风控操作。photo_search no_data 或档案中心失败都不能排除异常发布，只能作为当前条件下的 source_quality。

## BBFA-DEMO-006

- user_query: 这个账号有没有同设备关联账号？
- expected_source_plan: `archives_related_users -> archives_user_profile -> login_logs_search -> track_analysis_check_data_ready`
- expected_orchestration: Same-device relation is an expansion clue with cross-source validation.
- actual_source_plan_or_template: `archives_related_users -> archives_user_profile -> login_logs_search -> track_analysis_check_data_ready`
- expected_boundary_flags: `related_users_not_gang_conclusion, archives_related_users_spread_clue_not_gang`
- actual_boundary_flags: `related_users_not_gang_conclusion, archives_related_users_spread_clue_not_gang, archives_failure_enters_partial_evidence, same_device_relation_requires_cross_source_validation, source_quality_required`
- should_not_do: `do_not_label_gang_from_same_device_only, do_not_claim_archives_related_users_gang, do_not_bulk_expand_without_plan`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

同设备只进入扩散/佐证层，source_plan：archives_related_users -> archives_user_profile -> login_logs_search -> track_analysis_check_data_ready。它能给候选关联账号，但不能直接写团伙。需要再用账号画像、登录日志和 Track 活跃与数据可用性验证设备、时间和行为是否一致；档案中心失败时输出 partial evidence。

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

这是事件归因，不是策略树资产查询，source_plan：rcp_event_detail -> rcp_event_feature_list。先用 event detail 锚定事件时间、反馈和关键实体，再用 feature list 做可用特征摘要。策略命中只能作为事件层证据，不能单独推导用户风险。

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

不能说明完整特征。source_plan：rcp_event_detail -> rcp_event_feature_list。partial_observation_available 只能做部分观察。可引用 feature group、计数和关键实体摘要，但不能输出 raw feature values，也不能升级成强证据。

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

这个只走策略资产治理，source_plan：rcp_policy_tree_lookup。policyTree lookup 解释策略树、版本和节点上下文。它不是 event hit path，不能证明某个用户或事件实际命中；命中证据要回到事件详情或策略命中入口。

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

不能直接定性。source_plan：rcp_event_detail -> rcp_event_feature_list，只解决事件层上下文；策略命中只是辅助证据。风险结论还要回到控制权变化、异常行为闭环和账号/设备/发布链路的交叉验证。没有 source_quality 支撑时，只能写线索和待补证。
