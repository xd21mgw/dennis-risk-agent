# Browser-Backed Fixed Actions Text Demo V1

This is an offline text demo. It does not start the browser-backed service, access real platforms, call DataAgent/Hive, read auth material, or execute source actions.

- cases_total: `26`
- cases_passed: `26`
- cases_failed: `0`
- default_runtime_routing_false: `true`
- controlled_parallel_groups_supported: `independent_parallel, dependency_serial, large_response_serial, auth_sensitive_serial`
- real_platform_called: `false`
- dataagent_called: `false`
- hive_called: `false`

## BBFA-DEMO-001

- user_query: 帮我判断 user_id=2871834924 是否疑似 ATO
- expected_source_plan: `login_logs_search -> archives_user_profile -> archives_user_analysis -> track_analysis_check_data_ready`
- expected_orchestration: ATO multi-source plan, not login logs only.
- actual_source_plan_or_template: `suspicious_anchor_discovery -> login_logs_search -> archives_user_profile -> archives_user_analysis -> content_action_deep_dive -> candidate_control_endpoint_extraction -> device_identity_consistency -> historical_baseline_comparison -> track_analysis_check_data_ready`
- expected_execution_groups: `(none)`
- actual_execution_groups: `dependency_serial, independent_parallel, auth_sensitive_serial`
- expected_boundary_flags: `single_source_not_enough_for_ato, no_data_not_risk_exclusion, archives_required_for_behavior_closure_non_blocking`
- actual_boundary_flags: `suspicious_anchor_discovery_required, anchor_not_found_must_be_explicit, content_action_deep_dive_if_web_publish_or_diversion_content, device_identity_consistency_required, common_device_id_not_sufficient_to_exclude_ato, track_activity_not_owner_proof, weapon_not_login_or_publish_chain_replacement, rcp_strategy_hit_not_anchor_replacement, response_too_large_not_login_evidence, wrapper_response_mismatch_requires_source_contract_gap, login_no_data_or_window_gap_not_ato_exclusion, login_log_window_incomplete, admin_app_log_only_gap, web_control_chain_missing, offline_hive_required, archives_required_for_behavior_closure_non_blocking, archives_failure_enters_partial_evidence, track_check_data_ready_not_risk_conclusion, large_response_limited_enters_source_quality, single_source_not_enough_for_ato, no_data_not_risk_exclusion, login_log_window_incomplete_possible, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：ATO 裸问必须先找可疑登录/内容/行为锚点；设备判断要比较机型、系统、UA、IP、登录端和登录方式，不只看 device_id；历史常用 device_id 不能单独排除 ATO；Track 活跃只能做辅助信号，不能证明本人操作。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_only_query_login_logs, do_not_skip_archives_for_ato, do_not_make_final_judgement_without_source_quality`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

我会按“控制权变化 -> 异常行为闭环 -> 扩散/策略佐证”收敛，不自动查平台。source_plan：suspicious_anchor_discovery -> login_logs_search -> archives_user_profile -> archives_user_analysis -> content_action_deep_dive -> candidate_control_endpoint_extraction -> device_identity_consistency -> historical_baseline_comparison -> track_analysis_check_data_ready。先看登录链路是否有新设备、异地、验证或 token 变化；再用档案用户分析对齐改密、发布、关注等后置动作；最后只把 Track 活跃与数据可用性、策略命中当旁证。no_data 只进 source_quality，不能排除 ATO。档案中心若 auth_failed/no_data/timeout，也只降级为 partial evidence，不能跳过行为闭环。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：ATO 裸问必须先找可疑登录/内容/行为锚点；设备判断要比较机型、系统、UA、IP、登录端和登录方式，不只看 device_id；历史常用 device_id 不能单独排除 ATO；Track 活跃只能做辅助信号，不能证明本人操作。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-DEMO-002

- user_query: 登录日志没查到，是不是就没风险？
- expected_source_plan: `login_logs_search`
- expected_orchestration: Explain login no_data/window gap as source quality, not counter-evidence.
- actual_source_plan_or_template: `login_logs_search`
- expected_execution_groups: `(none)`
- actual_execution_groups: `independent_parallel`
- expected_boundary_flags: `no_data_not_risk_exclusion, login_log_window_incomplete_possible`
- actual_boundary_flags: `no_data_not_risk_exclusion, login_no_data_or_window_gap_not_ato_exclusion, login_log_window_incomplete_possible, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：no_data 只代表当前条件下无结果，不能作为无风险反证；登录日志 no_data 或窗口不足不能排除 ATO；登录日志在线窗口可能不完整。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_output_low_risk_from_no_data, do_not_stop_multisource_plan`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

不能。source_plan：login_logs_search。它只能说明在线窗口和当前条件下没有可见登录记录。no_data 不是无风险反证；如果客诉时间超窗，必须写 window gap。后续要用账号操作、账号画像或经授权的离线来源补控制权变化链路。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：no_data 只代表当前条件下无结果，不能作为无风险反证；登录日志 no_data 或窗口不足不能排除 ATO；登录日志在线窗口可能不完整。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-DEMO-003

- user_query: 看下这个账号画像和状态
- expected_source_plan: `archives_user_profile`
- expected_orchestration: Account profile is baseline context; not final judgement.
- actual_source_plan_or_template: `archives_user_profile`
- expected_execution_groups: `(none)`
- actual_execution_groups: `independent_parallel`
- expected_boundary_flags: `profile_context_not_final_judgement`
- actual_boundary_flags: `profile_context_not_final_judgement, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：本轮只生成 source plan 和回答边界，不把未执行 source 写成已完成证据。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_make_final_risk_judgement_from_profile_only, do_not_output_pii_strict`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

这个裸问只看账号基线，source_plan：archives_user_profile。重点是账号状态、注册/资料状态和风险摘要，用来判断背景线索。画像正常不等于本人操作，画像异常也不等于风险定性；行为链路要另补。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：本轮只生成 source plan 和回答边界，不把未执行 source 写成已完成证据。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-DEMO-004

- user_query: 这个账号最近有没有异常操作或风险日志？
- expected_source_plan: `archives_user_analysis`
- expected_orchestration: Use Archives user analysis; capped large response becomes partial observation.
- actual_source_plan_or_template: `archives_user_analysis`
- expected_execution_groups: `(none)`
- actual_execution_groups: `auth_sensitive_serial`
- expected_boundary_flags: `large_response_limited_enters_source_quality, partial_observation_available`
- actual_boundary_flags: `large_response_limited_enters_source_quality, partial_observation_available, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：大响应截断进入 source_quality；partial 观察可用于部分判断，但不能声称完整覆盖。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_dump_raw_records, do_not_claim_full_coverage_when_limited`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

这个问题收敛到操作时间线，source_plan：archives_user_analysis。重点看登录、改密、保护账号、冻结、直播/发布等动作是否能串成异常行为闭环。大响应只写 partial_observation_available，不能声称完整覆盖；raw records 不输出。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：大响应截断进入 source_quality；partial 观察可用于部分判断，但不能声称完整覆盖。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-DEMO-005

- user_query: 这个账号是不是异常发布/色导导流？
- expected_source_plan: `archives_photo_search -> archives_user_profile -> archives_user_analysis`
- expected_orchestration: Publish/content branch with photo search, profile baseline, and user analysis.
- actual_source_plan_or_template: `archives_photo_search -> archives_user_profile -> archives_user_analysis`
- expected_execution_groups: `(none)`
- actual_execution_groups: `auth_sensitive_serial`
- expected_boundary_flags: `photo_search_no_data_not_abnormal_publish_exclusion, archives_failure_enters_partial_evidence`
- actual_boundary_flags: `photo_search_no_data_not_abnormal_publish_exclusion, archives_failure_enters_partial_evidence, publish_chain_missing_evidence_must_be_explicit, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：档案中心失败进入 partial evidence，不中断回答。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_output_no_abnormal_publish_from_photo_no_data, do_not_use_archives_no_data_as_no_risk, do_not_make_final_judgement`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

导流/异常发布按“内容动作 -> 账号状态 -> 发布前后操作”看，source_plan：archives_photo_search -> archives_user_profile -> archives_user_analysis。先找作品/举报/发布线索，再看账号基线，最后对齐发布前后的登录、改密和风控操作。photo_search no_data 或档案中心失败都不能排除异常发布，只能作为当前条件下的 source_quality。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：档案中心失败进入 partial evidence，不中断回答。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-DEMO-006

- user_query: 这个账号有没有同设备关联账号？
- expected_source_plan: `archives_related_users -> archives_user_profile -> login_logs_search -> track_analysis_check_data_ready`
- expected_orchestration: Same-device relation is an expansion clue with cross-source validation.
- actual_source_plan_or_template: `archives_related_users -> archives_user_profile -> login_logs_search -> track_analysis_check_data_ready`
- expected_execution_groups: `(none)`
- actual_execution_groups: `auth_sensitive_serial, dependency_serial`
- expected_boundary_flags: `related_users_not_gang_conclusion, archives_related_users_spread_clue_not_gang`
- actual_boundary_flags: `related_users_not_gang_conclusion, archives_related_users_spread_clue_not_gang, archives_failure_enters_partial_evidence, same_device_relation_requires_cross_source_validation, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：同设备/关联用户只是扩散线索，不是团伙结论；archives_related_users 只提供扩散候选，需要交叉验证；档案中心失败进入 partial evidence，不中断回答。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_label_gang_from_same_device_only, do_not_claim_archives_related_users_gang, do_not_bulk_expand_without_plan`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

同设备只进入扩散/佐证层，source_plan：archives_related_users -> archives_user_profile -> login_logs_search -> track_analysis_check_data_ready。它能给候选关联账号，但不能直接写团伙。需要再用账号画像、登录日志和 Track 活跃与数据可用性验证设备、时间和行为是否一致；档案中心失败时输出 partial evidence。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：同设备/关联用户只是扩散线索，不是团伙结论；archives_related_users 只提供扩散候选，需要交叉验证；档案中心失败进入 partial evidence，不中断回答。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-DEMO-007

- user_query: 这个 eventId 为什么被拦？
- expected_source_plan: `rcp_event_detail -> rcp_event_feature_list`
- expected_orchestration: Event attribution first, feature list second when exact event identity is available.
- actual_source_plan_or_template: `rcp_event_detail -> rcp_event_feature_list`
- expected_execution_groups: `(none)`
- actual_execution_groups: `dependency_serial`
- expected_boundary_flags: `event_detail_not_policy_tree_asset_lookup, strategy_hit_not_final_judgement`
- actual_boundary_flags: `event_detail_not_policy_tree_asset_lookup, feature_list_partial_only_feature_group_summary, strategy_hit_not_final_judgement, attribution_not_cheating_judgement, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：feature list partial 只能做特征组摘要；策略命中只是辅助证据，不能单独定性风险。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_jump_to_policy_tree_asset_lookup, do_not_make_final_risk_judgement`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

这是事件归因，不是策略树资产查询，source_plan：rcp_event_detail -> rcp_event_feature_list。先用 event detail 锚定事件时间、反馈和关键实体，再用 feature list 做可用特征摘要。策略命中只能作为事件层证据，不能单独推导用户风险。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：feature list partial 只能做特征组摘要；策略命中只是辅助证据，不能单独定性风险。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-DEMO-008

- user_query: feature list 只拿到 partial，能不能说明完整特征？
- expected_source_plan: `rcp_event_feature_list`
- expected_orchestration: Partial feature observation can summarize groups but cannot claim full detail coverage.
- actual_source_plan_or_template: `rcp_event_detail -> rcp_event_feature_list`
- expected_execution_groups: `(none)`
- actual_execution_groups: `dependency_serial`
- expected_boundary_flags: `feature_list_partial_only_feature_group_summary, partial_observation_available`
- actual_boundary_flags: `partial_observation_available, event_detail_not_policy_tree_asset_lookup, feature_list_partial_only_feature_group_summary, strategy_hit_not_final_judgement, attribution_not_cheating_judgement, do_not_upgrade_partial_to_strong_evidence, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：partial 观察可用于部分判断，但不能声称完整覆盖；feature list partial 只能做特征组摘要；策略命中只是辅助证据，不能单独定性风险。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_claim_complete_feature_coverage, do_not_output_raw_feature_values`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

不能说明完整特征。source_plan：rcp_event_detail -> rcp_event_feature_list。partial_observation_available 只能做部分观察。可引用 feature group、计数和关键实体摘要，但不能输出 raw feature values，也不能升级成强证据。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：partial 观察可用于部分判断，但不能声称完整覆盖；feature list partial 只能做特征组摘要；策略命中只是辅助证据，不能单独定性风险。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-DEMO-009

- user_query: 这条策略挂在哪棵策略树？
- expected_source_plan: `rcp_policy_tree_lookup`
- expected_orchestration: Policy-tree lookup is governance context only.
- actual_source_plan_or_template: `rcp_policy_tree_lookup`
- expected_execution_groups: `(none)`
- actual_execution_groups: `dependency_serial`
- expected_boundary_flags: `policy_tree_asset_not_event_hit_path`
- actual_boundary_flags: `policy_tree_asset_not_event_hit_path, policy_tree_lookup_not_single_case_risk_evidence, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：policyTree 是资产治理，不是单案命中证据。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_treat_policy_tree_as_event_hit, do_not_make_user_risk_judgement`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

这个只走策略资产治理，source_plan：rcp_policy_tree_lookup。policyTree lookup 解释策略树、版本和节点上下文。它不是 event hit path，不能证明某个用户或事件实际命中；命中证据要回到事件详情或策略命中入口。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：policyTree 是资产治理，不是单案命中证据。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-DEMO-010

- user_query: 命中过策略，能不能直接定性风险？
- expected_source_plan: `rcp_event_detail -> rcp_event_feature_list`
- expected_orchestration: Strategy hit is auxiliary evidence; risk judgement needs cross-source context.
- actual_source_plan_or_template: `rcp_event_detail -> rcp_event_feature_list`
- expected_execution_groups: `(none)`
- actual_execution_groups: `dependency_serial`
- expected_boundary_flags: `strategy_hit_not_final_judgement`
- actual_boundary_flags: `strategy_hit_not_final_judgement, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：策略命中只是辅助证据，不能单独定性风险。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_make_final_judgement_from_strategy_hit_only`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

不能直接定性。source_plan：rcp_event_detail -> rcp_event_feature_list，只解决事件层上下文；策略命中只是辅助证据。风险结论还要回到控制权变化、异常行为闭环和账号/设备/发布链路的交叉验证。没有 source_quality 支撑时，只能写线索和待补证。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：策略命中只是辅助证据，不能单独定性风险。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-DEMO-011

- user_query: 先给 plan_mode，不要执行平台，说明是否查平台和 DataAgent
- expected_source_plan: `source_plan_only_no_action_selected`
- expected_orchestration: Plan-mode answer translates execution status into natural language.
- actual_source_plan_or_template: `source_plan_only_no_action_selected`
- expected_execution_groups: `(none)`
- actual_execution_groups: `(none)`
- expected_boundary_flags: `plan_mode_no_platform_execution, default_runtime_routing_false`
- actual_boundary_flags: `plan_mode_no_platform_execution, default_runtime_routing_false, missing_explicit_source_plan`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：plan mode 只输出分析流程和 source plan，不声称已查询平台；browser-backed source 仍需显式 source plan，不自动默认路由。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_emit_full_routing_metadata_by_default, do_not_dump_boundary_flags_yaml_by_default`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

本轮只给分析路径，不查平台，source_plan：plan-only（本轮不选择具体 source）。先明确风险假设和实体字段，再列实时只读 source；实时证据能闭合才给 evidence-based 结论，不闭合就输出 partial evidence、missing_evidence 和离线补证计划。DataAgent/Hive 执行前必须逐次授权。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：plan mode 只输出分析流程和 source plan，不声称已查询平台；browser-backed source 仍需显式 source plan，不自动默认路由。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-DEMO-012

- user_query: 给我 routing_metadata debug run log YAML
- expected_source_plan: `source_plan_only_no_action_selected`
- expected_orchestration: Explicit debug request may show full routing_metadata.
- actual_source_plan_or_template: `source_plan_only_no_action_selected`
- expected_execution_groups: `(none)`
- actual_execution_groups: `(none)`
- expected_boundary_flags: `missing_explicit_source_plan`
- actual_boundary_flags: `missing_explicit_source_plan`
- metadata_visibility: `full_routing_metadata`
- routing_metadata_yaml_visible: `true`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：本轮只生成 source plan 和回答边界，不把未执行 source 写成已完成证据。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。已按请求附完整内部过程 YAML。
- should_not_do: `do_not_hide_internal_run_log_metadata`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

已按 debug / run log 请求输出完整 routing_metadata；本轮仍未访问真实平台，未调用 DataAgent/Hive。

routing_metadata:
  route: multi_evidence_orchestration
  capability: multi_evidence_orchestration_contracts
  sub_capability: null
  intent_type: browser_backed_fixed_actions_text_debug
  execution_mode: plan_mode
  evidence_mode: expert_reasoning
  query_plan_only: true
  platform_called: false
  platform_call_summary: []
  dataagent_called: false
  direct_tool_bypass: false
  sensitive_output: false
  redaction_applied: true
  boundary_flags:
    - missing_explicit_source_plan
  source_quality:
    completed_sources: []
    no_data_sources: []
    blocked_sources: []
    auth_failed_sources: []
    timeout_sources: []
    parse_error_sources: []
    missing_sources: []
  missing_required_fields: []
  partial_reason: null
  final_status: answered

## BBFA-DEMO-013

- user_query: browser-backed pure passthrough：service 不含 normalized_observation / source_quality / evidence_card_inputs，Dennis 怎么生成证据卡
- expected_source_plan: `source_plan_only_no_action_selected`
- expected_orchestration: Pure passthrough envelope is consumed by Dennis; Dennis generates observation, source_quality_matrix, evidence_card, missing_evidence and final_answer_boundary.
- actual_source_plan_or_template: `source_plan_only_no_action_selected`
- expected_execution_groups: `(none)`
- actual_execution_groups: `(none)`
- expected_boundary_flags: `pure_passthrough_envelope_required, dennis_generates_observation_from_passthrough, dennis_generates_source_quality_matrix, dennis_generates_evidence_card, service_normalized_observation_not_required, service_evidence_card_inputs_not_required`
- actual_boundary_flags: `pure_passthrough_envelope_required, dennis_generates_observation_from_passthrough, dennis_generates_source_quality_matrix, dennis_generates_evidence_card, service_normalized_observation_not_required, service_evidence_card_inputs_not_required, service_source_card_not_required, compat_summary_legacy_only, default_runtime_routing_false`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：browser-backed service 只提供 passthrough envelope / transport metadata / capped body；Dennis 从 passthrough envelope 生成 observation，不依赖 service normalized_observation；Dennis 从 transport_status_matrix/source_results 合并 source_quality_matrix；Dennis 从 completed/partial passthrough 观察生成 evidence_card。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_require_service_normalized_observation, do_not_require_service_evidence_card_inputs, do_not_use_compat_summary_in_pure_passthrough`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

按显式 source_plan 处理：plan-only（本轮不选择具体 source）。保留 source_quality、missing_evidence 和 final_answer_boundary，不自动执行平台查询。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：browser-backed service 只提供 passthrough envelope / transport metadata / capped body；Dennis 从 passthrough envelope 生成 observation，不依赖 service normalized_observation；Dennis 从 transport_status_matrix/source_results 合并 source_quality_matrix；Dennis 从 completed/partial passthrough 观察生成 evidence_card。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-DEMO-014

- user_query: batch result 只有 transport_status_matrix/source_results，body_truncated=true，还有单 source timeout，Dennis 如何合并
- expected_source_plan: `source_plan_only_no_action_selected`
- expected_orchestration: Dennis merges transport_status_matrix/source_results into source_quality_matrix; body_truncated becomes partial observation and timeout becomes missing evidence.
- actual_source_plan_or_template: `source_plan_only_no_action_selected`
- expected_execution_groups: `(none)`
- actual_execution_groups: `(none)`
- expected_boundary_flags: `transport_status_matrix_merge_required, body_truncated_means_partial_observation, partial_observation_available, source_timeout_non_blocking_partial, timeout_platform_error_parse_error_missing_evidence, raw_body_capped_limited_observation_only`
- actual_boundary_flags: `pure_passthrough_envelope_required, dennis_generates_observation_from_passthrough, dennis_generates_source_quality_matrix, dennis_generates_evidence_card, service_normalized_observation_not_required, service_evidence_card_inputs_not_required, service_source_card_not_required, compat_summary_legacy_only, default_runtime_routing_false, transport_status_matrix_merge_required, source_quality_matrix_merge_required, body_truncated_means_partial_observation, partial_observation_available, raw_body_capped_limited_observation_only, source_timeout_non_blocking_partial, timeout_platform_error_parse_error_missing_evidence`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：browser-backed service 只提供 passthrough envelope / transport metadata / capped body；Dennis 从 passthrough envelope 生成 observation，不依赖 service normalized_observation；Dennis 从 transport_status_matrix/source_results 合并 source_quality_matrix；Dennis 从 completed/partial passthrough 观察生成 evidence_card。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_claim_complete_from_capped_body, do_not_discard_completed_source, do_not_make_final_judgement_without_source_quality`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

按显式 source_plan 处理：plan-only（本轮不选择具体 source）。保留 source_quality、missing_evidence 和 final_answer_boundary，不自动执行平台查询。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：browser-backed service 只提供 passthrough envelope / transport metadata / capped body；Dennis 从 passthrough envelope 生成 observation，不依赖 service normalized_observation；Dennis 从 transport_status_matrix/source_results 合并 source_quality_matrix；Dennis 从 completed/partial passthrough 观察生成 evidence_card。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-NATURAL-001

- user_query: 帮我判断 user_id=2871834924 是否疑似 ATO
- expected_source_plan: `login_logs_search -> archives_user_profile -> archives_user_analysis -> track_analysis_check_data_ready`
- expected_orchestration: ATO multi-source plan, not login logs only.
- actual_source_plan_or_template: `suspicious_anchor_discovery -> login_logs_search -> archives_user_profile -> archives_user_analysis -> content_action_deep_dive -> candidate_control_endpoint_extraction -> device_identity_consistency -> historical_baseline_comparison -> track_analysis_check_data_ready`
- expected_execution_groups: `(none)`
- actual_execution_groups: `dependency_serial, independent_parallel, auth_sensitive_serial`
- expected_boundary_flags: `single_source_not_enough_for_ato, no_data_not_risk_exclusion, archives_required_for_behavior_closure_non_blocking`
- actual_boundary_flags: `suspicious_anchor_discovery_required, anchor_not_found_must_be_explicit, content_action_deep_dive_if_web_publish_or_diversion_content, device_identity_consistency_required, common_device_id_not_sufficient_to_exclude_ato, track_activity_not_owner_proof, weapon_not_login_or_publish_chain_replacement, rcp_strategy_hit_not_anchor_replacement, response_too_large_not_login_evidence, wrapper_response_mismatch_requires_source_contract_gap, login_no_data_or_window_gap_not_ato_exclusion, login_log_window_incomplete, admin_app_log_only_gap, web_control_chain_missing, offline_hive_required, archives_required_for_behavior_closure_non_blocking, archives_failure_enters_partial_evidence, track_check_data_ready_not_risk_conclusion, large_response_limited_enters_source_quality, single_source_not_enough_for_ato, no_data_not_risk_exclusion, login_log_window_incomplete_possible, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：ATO 裸问必须先找可疑登录/内容/行为锚点；设备判断要比较机型、系统、UA、IP、登录端和登录方式，不只看 device_id；历史常用 device_id 不能单独排除 ATO；Track 活跃只能做辅助信号，不能证明本人操作。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_only_query_login_logs, do_not_skip_archives_for_ato, do_not_make_final_judgement_without_source_quality`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

我会按“控制权变化 -> 异常行为闭环 -> 扩散/策略佐证”收敛，不自动查平台。source_plan：suspicious_anchor_discovery -> login_logs_search -> archives_user_profile -> archives_user_analysis -> content_action_deep_dive -> candidate_control_endpoint_extraction -> device_identity_consistency -> historical_baseline_comparison -> track_analysis_check_data_ready。先看登录链路是否有新设备、异地、验证或 token 变化；再用档案用户分析对齐改密、发布、关注等后置动作；最后只把 Track 活跃与数据可用性、策略命中当旁证。no_data 只进 source_quality，不能排除 ATO。档案中心若 auth_failed/no_data/timeout，也只降级为 partial evidence，不能跳过行为闭环。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：ATO 裸问必须先找可疑登录/内容/行为锚点；设备判断要比较机型、系统、UA、IP、登录端和登录方式，不只看 device_id；历史常用 device_id 不能单独排除 ATO；Track 活跃只能做辅助信号，不能证明本人操作。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-NATURAL-002

- user_query: 登录日志没查到，是不是就说明没风险？
- expected_source_plan: `login_logs_search`
- expected_orchestration: Explain login no_data/window gap as source quality, not counter-evidence.
- actual_source_plan_or_template: `login_logs_search`
- expected_execution_groups: `(none)`
- actual_execution_groups: `independent_parallel`
- expected_boundary_flags: `no_data_not_risk_exclusion, login_log_window_incomplete_possible`
- actual_boundary_flags: `no_data_not_risk_exclusion, login_no_data_or_window_gap_not_ato_exclusion, login_log_window_incomplete_possible, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：no_data 只代表当前条件下无结果，不能作为无风险反证；登录日志 no_data 或窗口不足不能排除 ATO；登录日志在线窗口可能不完整。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_output_low_risk_from_no_data, do_not_stop_multisource_plan`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

不能。source_plan：login_logs_search。它只能说明在线窗口和当前条件下没有可见登录记录。no_data 不是无风险反证；如果客诉时间超窗，必须写 window gap。后续要用账号操作、账号画像或经授权的离线来源补控制权变化链路。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：no_data 只代表当前条件下无结果，不能作为无风险反证；登录日志 no_data 或窗口不足不能排除 ATO；登录日志在线窗口可能不完整。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-NATURAL-003

- user_query: 看下这个账号画像、状态，以及最近有没有异常操作
- expected_source_plan: `archives_user_profile -> archives_user_analysis`
- expected_orchestration: Profile baseline plus recent operation timeline; profile is not final risk judgement.
- actual_source_plan_or_template: `archives_user_profile -> archives_user_analysis`
- expected_execution_groups: `(none)`
- actual_execution_groups: `independent_parallel, auth_sensitive_serial`
- expected_boundary_flags: `profile_context_not_final_judgement, large_response_limited_enters_source_quality, partial_observation_available`
- actual_boundary_flags: `profile_context_not_final_judgement, large_response_limited_enters_source_quality, partial_observation_available, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：大响应截断进入 source_quality；partial 观察可用于部分判断，但不能声称完整覆盖。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_make_final_risk_judgement_from_profile_only, do_not_dump_raw_records, do_not_claim_complete_timeline`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

这个问题拆成账号基线和近期操作两段，source_plan：archives_user_profile -> archives_user_analysis。账号画像/状态只回答基线是否异常；近期操作要看档案用户分析里的改密、保护、发布、直播、关注等时间线。如果操作明细被截断，只能写 partial_observation_available，并把未覆盖窗口放进 missing_evidence。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：大响应截断进入 source_quality；partial 观察可用于部分判断，但不能声称完整覆盖。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-NATURAL-004

- user_query: 这个账号是不是异常发布/色导导流？
- expected_source_plan: `archives_photo_search -> archives_user_profile -> archives_user_analysis`
- expected_orchestration: Publish/content branch with photo search, profile baseline, and user analysis.
- actual_source_plan_or_template: `archives_photo_search -> archives_user_profile -> archives_user_analysis`
- expected_execution_groups: `(none)`
- actual_execution_groups: `auth_sensitive_serial`
- expected_boundary_flags: `photo_search_no_data_not_abnormal_publish_exclusion, archives_failure_enters_partial_evidence`
- actual_boundary_flags: `photo_search_no_data_not_abnormal_publish_exclusion, archives_failure_enters_partial_evidence, publish_chain_missing_evidence_must_be_explicit, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：档案中心失败进入 partial evidence，不中断回答。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_output_no_abnormal_publish_from_photo_no_data, do_not_use_archives_no_data_as_no_risk, do_not_make_final_judgement`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

导流/异常发布按“内容动作 -> 账号状态 -> 发布前后操作”看，source_plan：archives_photo_search -> archives_user_profile -> archives_user_analysis。先找作品/举报/发布线索，再看账号基线，最后对齐发布前后的登录、改密和风控操作。photo_search no_data 或档案中心失败都不能排除异常发布，只能作为当前条件下的 source_quality。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：档案中心失败进入 partial evidence，不中断回答。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-NATURAL-005

- user_query: 这个账号有没有同设备关联账号？是不是一批黑产？
- expected_source_plan: `archives_related_users -> archives_user_profile -> login_logs_search -> track_analysis_check_data_ready`
- expected_orchestration: Same-device relation is an expansion clue with cross-source validation.
- actual_source_plan_or_template: `archives_related_users -> archives_user_profile -> login_logs_search -> track_analysis_check_data_ready`
- expected_execution_groups: `(none)`
- actual_execution_groups: `auth_sensitive_serial, dependency_serial`
- expected_boundary_flags: `related_users_not_gang_conclusion, archives_related_users_spread_clue_not_gang`
- actual_boundary_flags: `related_users_not_gang_conclusion, archives_related_users_spread_clue_not_gang, archives_failure_enters_partial_evidence, same_device_relation_requires_cross_source_validation, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：同设备/关联用户只是扩散线索，不是团伙结论；archives_related_users 只提供扩散候选，需要交叉验证；档案中心失败进入 partial evidence，不中断回答。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_label_gang_from_same_device_only, do_not_claim_archives_related_users_gang, do_not_bulk_expand_without_plan`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

同设备只进入扩散/佐证层，source_plan：archives_related_users -> archives_user_profile -> login_logs_search -> track_analysis_check_data_ready。它能给候选关联账号，但不能直接写团伙。需要再用账号画像、登录日志和 Track 活跃与数据可用性验证设备、时间和行为是否一致；档案中心失败时输出 partial evidence。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：同设备/关联用户只是扩散线索，不是团伙结论；archives_related_users 只提供扩散候选，需要交叉验证；档案中心失败进入 partial evidence，不中断回答。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-NATURAL-006

- user_query: 这个 eventId 为什么被拦？
- expected_source_plan: `rcp_event_detail -> rcp_event_feature_list`
- expected_orchestration: Event attribution first, feature list second when exact event identity is available.
- actual_source_plan_or_template: `rcp_event_detail -> rcp_event_feature_list`
- expected_execution_groups: `(none)`
- actual_execution_groups: `dependency_serial`
- expected_boundary_flags: `event_detail_not_policy_tree_asset_lookup, strategy_hit_not_final_judgement`
- actual_boundary_flags: `event_detail_not_policy_tree_asset_lookup, feature_list_partial_only_feature_group_summary, strategy_hit_not_final_judgement, attribution_not_cheating_judgement, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：feature list partial 只能做特征组摘要；策略命中只是辅助证据，不能单独定性风险。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_jump_to_policy_tree_asset_lookup, do_not_make_final_risk_judgement`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

这是事件归因，不是策略树资产查询，source_plan：rcp_event_detail -> rcp_event_feature_list。先用 event detail 锚定事件时间、反馈和关键实体，再用 feature list 做可用特征摘要。策略命中只能作为事件层证据，不能单独推导用户风险。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：feature list partial 只能做特征组摘要；策略命中只是辅助证据，不能单独定性风险。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-NATURAL-007

- user_query: 这条策略挂在哪棵策略树？能不能说明用户有风险？
- expected_source_plan: `rcp_policy_tree_lookup`
- expected_orchestration: Policy-tree lookup is governance context only.
- actual_source_plan_or_template: `rcp_policy_tree_lookup`
- expected_execution_groups: `(none)`
- actual_execution_groups: `dependency_serial`
- expected_boundary_flags: `policy_tree_asset_not_event_hit_path, strategy_hit_not_final_judgement`
- actual_boundary_flags: `policy_tree_asset_not_event_hit_path, policy_tree_lookup_not_single_case_risk_evidence, strategy_hit_not_final_judgement, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：policyTree 是资产治理，不是单案命中证据；策略命中只是辅助证据，不能单独定性风险。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_treat_policy_tree_as_event_hit, do_not_make_user_risk_judgement`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

这个只走策略资产治理，source_plan：rcp_policy_tree_lookup。policyTree lookup 解释策略树、版本和节点上下文。它不是 event hit path，不能证明某个用户或事件实际命中；命中证据要回到事件详情或策略命中入口。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：policyTree 是资产治理，不是单案命中证据；策略命中只是辅助证据，不能单独定性风险。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-NATURAL-008

- user_query: 命中过策略，能不能直接定性风险？
- expected_source_plan: `rcp_event_detail -> rcp_event_feature_list`
- expected_orchestration: Strategy hit is auxiliary evidence; risk judgement needs cross-source context.
- actual_source_plan_or_template: `rcp_event_detail -> rcp_event_feature_list`
- expected_execution_groups: `(none)`
- actual_execution_groups: `dependency_serial`
- expected_boundary_flags: `strategy_hit_not_final_judgement`
- actual_boundary_flags: `strategy_hit_not_final_judgement, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：策略命中只是辅助证据，不能单独定性风险。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_make_final_judgement_from_strategy_hit_only`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

不能直接定性。source_plan：rcp_event_detail -> rcp_event_feature_list，只解决事件层上下文；策略命中只是辅助证据。风险结论还要回到控制权变化、异常行为闭环和账号/设备/发布链路的交叉验证。没有 source_quality 支撑时，只能写线索和待补证。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：策略命中只是辅助证据，不能单独定性风险。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-NATURAL-009

- user_query: 这批设备行为很像协议上号，应该怎么查？
- expected_source_plan: `source_plan_only_no_action_selected`
- expected_orchestration: Anti-cheat device protocol question stays plan-only; realtime sources first and offline device/request/behavior/feature plan when incomplete.
- actual_source_plan_or_template: `source_plan_only_no_action_selected`
- expected_execution_groups: `(none)`
- actual_execution_groups: `(none)`
- expected_boundary_flags: `universal_realtime_first_workflow, offline_device_request_behavior_feature_plan_required, strategy_hit_not_final_judgement, default_runtime_routing_false`
- actual_boundary_flags: `universal_realtime_first_workflow, offline_device_request_behavior_feature_plan_required, strategy_hit_not_final_judgement, default_runtime_routing_false`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：通用风险研判先规划实时只读 source，实时不闭合再给离线补证计划；设备/协议上号实时证据不闭合时，需要设备、请求、行为和特征宽表离线补证计划；策略命中只是辅助证据，不能单独定性风险；browser-backed source 仍需显式 source plan，不自动默认路由。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_treat_device_protocol_similarity_as_final_conclusion, do_not_skip_offline_device_request_behavior_plan, do_not_execute_platform_when_user_asks_analysis_only`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

先按反作弊设备异常的通用 workflow 走，source_plan：plan-only（本轮不选择具体 source）。实时层先看设备/IP/请求/策略命中/前端活跃能否形成协议上号链路；实时不闭合时，离线补设备宽表、请求明细、行为序列和特征宽表。相似设备行为只是线索，不能直接定性为协议或群控。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：通用风险研判先规划实时只读 source，实时不闭合再给离线补证计划；设备/协议上号实时证据不闭合时，需要设备、请求、行为和特征宽表离线补证计划；策略命中只是辅助证据，不能单独定性风险；browser-backed source 仍需显式 source plan，不自动默认路由。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-NATURAL-010

- user_query: 这批账号是不是同一批盗号？
- expected_source_plan: `source_plan_only_no_action_selected`
- expected_orchestration: Batch ATO uses existing clustering plus ATO lens, representative deep dive, and cluster backfill.
- actual_source_plan_or_template: `source_plan_only_no_action_selected`
- expected_execution_groups: `(none)`
- actual_execution_groups: `(none)`
- expected_boundary_flags: `batch_ato_cluster_lens_required, existing_cluster_plus_ato_lens, compromised_account_cluster_detection, representative_ato_single_case_deep_dive, cluster_level_backfill, representative_sample_not_global_proof`
- actual_boundary_flags: `batch_ato_cluster_lens_required, existing_cluster_plus_ato_lens, web_untrusted_login_cluster, login_to_action_delta_required, device_identity_inconsistency_cluster, compromised_account_cluster_detection, representative_ato_single_case_deep_dive, cluster_level_backfill, representative_sample_not_global_proof, batch_login_gap_not_low_risk, hive_required_hint, offline_hive_required, login_log_window_incomplete, admin_app_log_only_gap, web_control_chain_missing, hive_registry_first_query_plan, batch_user_facing_no_runtime_yaml, default_runtime_routing_false`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：批量 ATO 要在已有分簇上叠加 ATO lens，不是从零分簇或逐用户 for-loop；保留内容/设备/策略/时间等已有簇，再判断是否叠加 ATO 盗号投放嫌疑；多个账号存在 WEB/H5/PC 非可信登录或登录端从 APP 偏移；需要提取 WEB/控制链登录到发视频/评论/直播/私信等后置动作的时间差。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_skip_ato_cluster_lens, do_not_globalize_representative_sample, do_not_treat_track_as_owner_proof`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

批量 ATO 先保留已有分簇，再叠加 ato_cluster_lens，source_plan：plan-only（本轮不选择具体 source）。输出要区分内容导流簇、compromised_account_cluster、content_abuse_only_cluster 和 mixed_cluster。核心检查 web_untrusted_login_cluster、login_to_action_delta、device_identity_inconsistency_cluster，每个疑似簇抽代表样本做 representative_ato_single_case_deep_dive，再做 cluster_level_backfill。代表样本不能证明全批账号都被盗，常用 device_id、Track 活跃和登录 no_data 都不能当排除 ATO 的反证。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：批量 ATO 要在已有分簇上叠加 ATO lens，不是从零分簇或逐用户 for-loop；保留内容/设备/策略/时间等已有簇，再判断是否叠加 ATO 盗号投放嫌疑；多个账号存在 WEB/H5/PC 非可信登录或登录端从 APP 偏移；需要提取 WEB/控制链登录到发视频/评论/直播/私信等后置动作的时间差。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-NATURAL-011

- user_query: 登录没异常，但档案中心操作很可疑，怎么判断？
- expected_source_plan: `login_logs_search -> archives_user_profile -> archives_user_analysis -> track_analysis_check_data_ready`
- expected_orchestration: Conflicting login and Archives observations require source_quality and missing evidence, not forced conclusion.
- actual_source_plan_or_template: `suspicious_anchor_discovery -> login_logs_search -> archives_user_profile -> archives_user_analysis -> content_action_deep_dive -> candidate_control_endpoint_extraction -> device_identity_consistency -> historical_baseline_comparison -> track_analysis_check_data_ready`
- expected_execution_groups: `(none)`
- actual_execution_groups: `dependency_serial, independent_parallel, auth_sensitive_serial`
- expected_boundary_flags: `conflicting_sources_require_source_quality, final_judgement_boundary_required, single_source_not_enough_for_ato`
- actual_boundary_flags: `suspicious_anchor_discovery_required, anchor_not_found_must_be_explicit, content_action_deep_dive_if_web_publish_or_diversion_content, device_identity_consistency_required, common_device_id_not_sufficient_to_exclude_ato, track_activity_not_owner_proof, weapon_not_login_or_publish_chain_replacement, rcp_strategy_hit_not_anchor_replacement, response_too_large_not_login_evidence, wrapper_response_mismatch_requires_source_contract_gap, login_no_data_or_window_gap_not_ato_exclusion, login_log_window_incomplete, admin_app_log_only_gap, web_control_chain_missing, offline_hive_required, archives_required_for_behavior_closure_non_blocking, archives_failure_enters_partial_evidence, track_check_data_ready_not_risk_conclusion, large_response_limited_enters_source_quality, single_source_not_enough_for_ato, no_data_not_risk_exclusion, login_log_window_incomplete_possible, conflicting_sources_require_source_quality, final_judgement_boundary_required, source_quality_required`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：ATO 裸问必须先找可疑登录/内容/行为锚点；设备判断要比较机型、系统、UA、IP、登录端和登录方式，不只看 device_id；历史常用 device_id 不能单独排除 ATO；Track 活跃只能做辅助信号，不能证明本人操作。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_discard_conflicting_source, do_not_force_conclusion, do_not_make_final_judgement_without_source_quality`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

这类冲突不能二选一强判，source_plan：suspicious_anchor_discovery -> login_logs_search -> archives_user_profile -> archives_user_analysis -> content_action_deep_dive -> candidate_control_endpoint_extraction -> device_identity_consistency -> historical_baseline_comparison -> track_analysis_check_data_ready。登录无异常只说明可见登录链路暂未发现问题；档案中心操作可疑要继续对齐动作时间、来源端、设备/IP/UA 和历史基线。最终用 source_quality 标出哪个来源完成、哪个来源缺口，missing_evidence 写清未闭合控制链。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：ATO 裸问必须先找可疑登录/内容/行为锚点；设备判断要比较机型、系统、UA、IP、登录端和登录方式，不只看 device_id；历史常用 device_id 不能单独排除 ATO；Track 活跃只能做辅助信号，不能证明本人操作。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。

## BBFA-NATURAL-012

- user_query: 先别查平台，告诉我应该怎么分析
- expected_source_plan: `source_plan_only_no_action_selected`
- expected_orchestration: Plan-mode answer only; do not claim platform execution.
- actual_source_plan_or_template: `source_plan_only_no_action_selected`
- expected_execution_groups: `(none)`
- actual_execution_groups: `(none)`
- expected_boundary_flags: `plan_mode_no_platform_execution, default_runtime_routing_false`
- actual_boundary_flags: `plan_mode_no_platform_execution, default_runtime_routing_false, missing_explicit_source_plan`
- metadata_visibility: `user_visible_summary`
- routing_metadata_yaml_visible: `false`
- user_visible_status_summary: 执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：plan mode 只输出分析流程和 source plan，不声称已查询平台；browser-backed source 仍需显式 source plan，不自动默认路由。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
- should_not_do: `do_not_execute_platform_when_user_asks_analysis_only, do_not_emit_full_routing_metadata_by_default, do_not_call_dataagent, do_not_call_hive`
- pass: `true`
- issue_if_failed: none
- fix_applied: none

Dennis_answer_draft:

本轮只给分析路径，不查平台，source_plan：plan-only（本轮不选择具体 source）。先明确风险假设和实体字段，再列实时只读 source；实时证据能闭合才给 evidence-based 结论，不闭合就输出 partial evidence、missing_evidence 和离线补证计划。DataAgent/Hive 执行前必须逐次授权。

执行状态：本轮未访问真实平台，未调用 DataAgent/Hive。证据边界：plan mode 只输出分析流程和 source plan，不声称已查询平台；browser-backed source 仍需显式 source plan，不自动默认路由。缺失字段/下一步：如需执行，先补齐明确实体、时间窗口和显式 source plan。默认只展示自然语言执行状态，不展示内部过程 YAML。
