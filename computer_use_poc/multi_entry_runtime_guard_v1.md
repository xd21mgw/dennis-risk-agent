# Multi-entry Runtime Guard v1

Guard marker: `DENNIS_ROUTING_GUARD_V1`.

## 0. Plan-only Diagnostic / Plan -> Execution Gate

`plan_only_diagnostic` 只能证明 intent / routing / source plan / output contract 设计是否合理，不能证明 live runtime config、safeBins、runner、auth state 或平台权限可用。

Plan 合格后进入 execution 前必须同时满足：

- `routing_mode` 正确。
- `source_plan` 正确。
- DataAgent/Hive 未默认执行，仍为逐次授权。
- Browser / DOM / SPA 未作为 P0 默认 source；P0 优先受控 API runner / API direct。
- `no_data_not_risk_exclusion` 和 `strategy_hit_not_final_judgement` 边界明确。
- output contract 明确：execution 必须有 `evidence_card` / `source_quality` / 用户可读执行状态摘要。
- plan-only 默认必须有自然语言执行状态摘要，说明未查平台、未调用 DataAgent/Hive 和 `reason_not_executed`；完整 `routing_metadata` 只在 debug / run log / explicit metadata request / regression 中展示。

Source priority and access method must be separated across all risk scenes:

- 证据价值决定 `source_priority`，执行方式决定 `access_method`。API direct first 是同等证据价值下的低成本 / 稳定采集路径优先，不是 P0 / P1 / P2 的唯一判定标准。
- 每个 source plan item must separately declare `source_priority: P0 | P1 | P2 | conditional` and `access_method: api_direct | controlled_runner | browser_cookie_activation | same_origin_fetch | manual_gap | hive_authorized`.
- 非纯 API source 不能天然降级；如果它是当前场景核心证据，仍然可以是 P0。
- Browser 不作为通用默认替代；但对于档案中心用户分析、发布作品 / 发布链路等特定 P0 source，如果平台必须 browser 激活 cookie / SPA / same-origin fetch，可以作为受控 P0 采集链路。
- 受控 browser P0 source 必须满足：`executor_agent=dennis-risk-agent`、`main_direct_tool_bypass=false`、`readonly=true`、timeout / checkpoint / partial evidence fallback 完整，且 `auth_failed` / redirect / profile_lock / same_origin_error 进入 `source_quality`。

如果 plan 合格但 execution 失败，优先归因到 `config/runtime`、runner/safeBin/auth 或 `source_orchestration`，不要直接判定为脑子 / 路由问题。

如果 execution 成功但结论差，优先归因到 `evidence_reasoning` 或 `output_contract`。

DataAgent/Hive：

- 每一次调用都必须用户逐次授权。
- 上一次授权、同一轮对话、P0/P1 数据不足，都不构成后续自动调用授权。
- 可以生成 query plan、推荐 SQL、表选择和字段说明，但不能自动执行。

Browser：

- P0 优先受控 API runner / API direct。
- browser / DOM / SPA 不作为通用默认替代；只有当该 source 的已登记 access method 需要 `browser_cookie_activation` / `same_origin_fetch` 时，才能作为受控采集链路。
- main agent 不得通过 browser / curl / cookie 接管平台查询。

策略命中：

- 用户明确问“策略命中”时，策略命中是显式目标 source。
- 策略命中只能作为辅助风险信号，不是最终 ATO 定性证据。
- stop condition 不能跳过用户显式目标 source。用户问策略命中时，天师策略命中必须进入 target source；用户问异常发布 / 作品引流 / 非本人发布时，发布作品列表、发布时间、发布设备和发布来源链路必须进入 target source。

Failure Triage Card 模板见 `computer_use_poc/failure_triage_card_template_v1.md`。

## 1. Supported Entry Points

This guard applies before any Dennis Risk Agent execution from:

- KIM group chat entry.
- APP entry.
- Web entry.
- Future internal or semi-open entries.

The guard is entry-agnostic. KIM is the first validated entry, not the only target.

## 2. Unified Entry Handling Principles

All entries must pass through the same runtime guard before calling Dennis:

- intent classification.
- task fingerprint classification.
- context boundary decision.
- execution / plan / fast_ack mode decision.
- mixed request decomposition.
- field output policy selection.
- DataAgent execution boundary.
- response length / channel constraint.

The guard must run before tool call, browser access, DataAgent call, or `sessions_spawn`.

General evidence reasoning hard gate:

- Applies to account security, protocol attack, group control, anti-crawler, activity anti-cheating, traffic diversion, traffic anti-cheating, strategy attribution, and batch risk clustering.
- If an answer judges whether a user, device, interface, batch, campaign, channel, strategy hit, or event is risky, route to evidence mode unless the user explicitly asks for pure methodology.
- Evidence mode output must include `evidence_card`, `source_quality`, and a user-visible execution-status summary; full `routing_metadata` is debug/run-log/regression only unless explicitly requested.
- If any required block is missing, self-correct before final output.
- Do not output natural-language judgement only.
- `no_data`, `timeout`, `blocked`, `auth_failed`, stale source, and partial source are quality states, not no-risk counter evidence.
- Strategy hit, rule hit, model score, blacklist hit, risk tag, or confidence level cannot be the only strong evidence.
- Separate `raw_evidence`, `strategy_hit`, `model_score`, `inference`, `user_claim`, `counter_evidence`, and `missing_evidence`.
- When new evidence arrives after an initial answer, recompute conclusion and mark `conclusion_recompute_after_new_evidence`.
- Every source must expose time window and coverage boundary; out-of-window gaps become `required_offline_check` / `missing_evidence`.

Universal realtime-first workflow:

- For any risk judgement, first form `risk_hypothesis_and_source_plan`; do not flatten platform source status into a conclusion.
- Prefer realtime readonly source plans when required fields are complete and the source is registered.
- If realtime evidence closes the chain, output an evidence-based conclusion with source-quality and time-window boundaries.
- If realtime evidence does not close the chain, output partial evidence, missing evidence, and an offline supplement plan by risk scene. Do not force a low-risk or high-risk conclusion from gaps.
- Offline supplement plans must be scene-specific: account takeover uses login/control/action chains; anti-cheating uses device/request/behavior/feature tables; traffic diversion uses content/comment/DM/profile/audit/strategy sources; strategy governance uses version/release/hit/false-positive/gray metrics.
- DataAgent/Hive execution requires explicit authorization for each query, table, time range, and evidence direction. A previous approval cannot be reused.
- Batch/commonality questions use shared dimensions, representative samples and coverage backfill; representative single-case evidence cannot prove every entity in the batch.

Release / overlay readiness gate:

- Before any release or live overlay, run `python3 computer_use_poc/runtime_preflight_check.py`.
- A checked-in template is not live runtime. Live config must still be validated separately.
- If runtime config is not applied, mark `runtime_config_not_applied`.
- If source wrapper is unavailable, expose `source_quality` and do not pretend wrapper-first succeeded.

Platform call preflight:

- Before any realtime platform source, read `computer_use_poc/platform_call_playbook_index.md` and the referenced platform playbook.
- Platform Access Execution v0.1 contracts live in `computer_use_poc/platform_access/`; platform calls must produce `platform_access_observation` or an equivalent source card before being merged into an evidence card.
- Platform failure classification order is: invocation chain, dependency, base domain / endpoint contract, parameter contract, upstream id availability, same-origin context, path permission, then auth / permission. Do not collapse 302 / 403 / timeout into generic `auth_failed`.
- Core principle: 先判调用链路，再判认证；先判参数契约，再判权限；先判局部 API，再判平台不可用。
- If memory retrieval fails, fall back to files; do not guess platform paths.
- Do not classify platform capabilities as only "API direct" or "not API direct". Use `api_direct_confirmed`, `same_origin_api_confirmed`, `partial_api_direct`, or `pending_api_direct_confirmation`.
- Prefer low-cost structured sources: `api_direct_confirmed` before `same_origin_api_confirmed`, same-origin fetch before DOM, precise `sourceId/eventId/deviceId/eventType` before broad scan, realtime readonly API before DataAgent / Hive.
- 实时只读 API 查询不需要用户确认 when required fields are complete.
- DataAgent / Hive / 大批量 / 写操作 / 高风险操作需要确认 or query plan.
- DataAgent / Hive confirmation is per call, not session-wide. A previous user approval only authorizes that one query.
- Each source must produce a checkpoint and source_quality.
- P1/P2 browser source must not block P0 partial evidence output.
- Old observations must not be used as "no-cache" realtime results.
- Low-cost source `no_data`, `blocked`, `timeout`, or `auth_failed` must enter `source_quality`; it is not low-risk / no-risk evidence.
- If source coverage is incomplete, mark `source_window_boundary`, `missing_evidence`, or `offline_hive_required`.
- If later higher-quality evidence conflicts with an earlier low-cost source, recompute the conclusion and prefer longer-window, fuller-chain, raw-behavior evidence over strategy names or model scores.
- If the user question involves `user_id` / `device_id` activity, profile, recent-30-day behavior, whether a device was active on a given day, or long-inactive-then-sudden-activation, prefer `track_analysis_activity_profile_api_direct`.
- `track_analysis_activity_profile_api_direct` is `api_direct_confirmed`, low cost, `realtime_readonly_api`; do not default to SPA DOM and do not call DataAgent / Hive first.
- If login log, Hive, Weapon, Archives, or strategy-hit evidence shows abnormal mobile device, non-historical device, new-device login, post-scan new device, device risk tag, or event-day strategy hit, trigger track-analysis event-day alignment as a low-cost supporting source.
- Track-analysis `no_data`, `blocked`, or `timeout` must enter `source_quality`; it cannot exclude risk.
- If backend login / scan / device switch / strategy hit exists on a day but track-analysis userId/deviceId duration is `0` or no frontend activity, mark `front_backend_activity_mismatch`. This is a medium/high-value lead for protocol login, token/session use, or non-real-client behavior, but it is not standalone final judgement.

Browser-backed fixed actions v1 guard:

- The v1 fixed action batch is registered for explicit source plans only; `default_runtime_routing=false` remains mandatory.
- Before any browser-backed action call, the source plan must name the exact action and typed params. Caller-provided URL, path, header, cookie, token, session, secret, raw body, or raw query is forbidden.
- ATO single-case explicit source plan must start with realtime P0 source collection: login/control chain, Archives profile, Archives user analysis, Archives photo search, and Track checkDataReady. Suspicious anchors are derived from those observations; `suspicious_anchor_discovery` is not an executable standalone source.
- User-facing ATO answer must use the business evidence-card template: conclusion, suspicious anchors, candidate control endpoint / `device_identity_consistency`, login-chain evidence, content/four-items/post-action evidence, historical baseline, evidence gaps, next actions. It must not display `routing_metadata`, `source_quality` YAML, `boundary_flags`, `execution_mode`, validator fields, or platform debug YAML.
- ATO / login anomaly source plan: `login_logs_search + archives_user_profile + track_analysis_check_data_ready` in `independent_parallel`; `archives_photo_search + archives_user_analysis` in Archives `auth_sensitive_serial`.
- Abnormal publish / content handoff source plan: `archives_photo_search -> archives_user_profile -> archives_user_analysis`.
- Account spread source plan: `archives_related_users -> archives_user_profile/login_logs_search/track_analysis_check_data_ready`.
- RCP event attribution source plan: `rcp_event_detail -> rcp_event_feature_list`.
- Policy asset governance source plan: `rcp_policy_tree_lookup` only.
- Source output must include `source_plan`, `actions`, `source_quality_matrix`, `missing_evidence`, `evidence_strength`, and `final_answer_boundary`.
- Browser-backed service output is pure passthrough. Entry/runtime layers must not require service-side `normalized_observation`, `source_card`, `source_quality`, `evidence_card_inputs`, or `compat_summary`; Dennis generates observation, source quality, evidence card, missing evidence and final boundary from passthrough envelope / transport metadata / capped body.
- `body_truncated=true` means partial observation only; auth redirect or API 302 means `auth_flow_not_completed_in_bound_context`; timeout/platform/parse errors enter missing evidence without blocking partial answer.
- Controlled parallel source output must keep per-item `source_id`, `action`, `execution_group`, `depends_on`, `timeout_class`, `failure_policy`, `source_priority`, and `expected_observation`; supported groups are `independent_parallel`, `dependency_serial`, `large_response_serial`, and `auth_sensitive_serial`.
- `/actions/batch` and `/actions/multi_source_plan` are explicit source-plan execution paths only. They do not change `default_runtime_routing=false`, do not authorize new actions, and do not allow caller-provided URL/path/header/cookie/token/session fields.
- `no_data`, `auth_failed`, `blocked`, `timeout`, `parse_error`, `partial_observation_available`, and `large_response_limited` are source-quality states, not low-risk or no-risk evidence.
- Archives 302 / redirect is `auth_flow_not_completed_in_bound_context`; do not label it as generic no permission unless the source explicitly returns permission denial.
- `track_analysis_check_data_ready` is readiness/provenance only, not completed risk evidence.
- `rcp_policy_tree_lookup` is policy-tree asset governance, not single-event hit path. Do not replace `rcp_event_detail -> rcp_event_feature_list` with policy-tree lookup for event attribution.
- Strategy hit, event detail, feature list, policy tree, and final risk judgement must remain separate layers.
- Risk entity identifiers (`user_id`, `device_id`, `ip`, `event_id`, `strategy_id`, `photo_id`, `policyCode`, `policyTreeCode`) may be retained for internal risk review/source chaining. Credential secrets and strict PII remain forbidden output and storage.

Dennis source execution guard:

- In real case / source observation / evidence card execution, `dennis-risk-agent` must treat SSO / cookie / runner troubleshooting details in AGENTS.md, TOOLS.md, SOUL.md, USER.md, IDENTITY.md, or session-memory as `main_agent_config_ops_only`, `deprecated_for_dennis_subagent`, and `not_for_case_execution`.
- Hard forbid during case execution: read `.ks_sso/sso-state.json`, manually build Cookie/Header, use curl / urllib / requests with Cookie, debug `SmartSSOSession`, debug `sso_session_runner.py` / `sso_session.py`, import or inspect auth bridge implementation, perform live auth repair, or replace source observation with tool troubleshooting.
- Case execution calls must enter through `computer_use_poc/runtime_case_execution_runner.py`, which builds the source plan and uses browser-backed `/actions/batch` or `/actions/multi_source_plan` in live mode.
- Legacy runners (`sso_session_runner`, `archives_profile_runner`, Weapon runner), freeform `browser_backed_service_client --action`, task-local curl, and ad-hoc browser fetch are `debug_only` / `manual_diagnostic_only` / `not_for_case_execution`; they are not fallback paths after browser-backed source gaps.
- Each source may attempt only the harness-managed batch path. Repeated runner debugging, auth probing, single-action fallback, or endpoint exploration is a source execution guard violation.
- When a source path fails, emit `source_status=tool_gap | auth_bridge_gap | blocked | timeout | parse_error | no_data`, fill `source_quality`, continue the next source, and produce partial evidence card if the matrix is incomplete.
- `tool_gap`, `auth_bridge_gap`, `no_data`, `timeout`, `blocked`, and `parse_error` are not low-risk / no-risk counter evidence.

RCP / Tianshi strategy-hit chain:

- `eventList` on `rcp.corp.kuaishou.com` is the primary upstream source for realtime strategy-hit event lists.
- `fastQueryHbase` uses `rcp.corp.kuaishou.com` and is fallback / optional, not the main blocking point.
- `eventList` accepts `eventType`, `timeRange`, optional `sourceIds`, policy/feedback filters, `conditionGroups`, `tableHeaderList` / custom columns, and pagination. It is not a single `userId` API.
- Downstream `rcpEventDetail`, `rcpEventFeatureList`, `getPolicyVersionListByEvent`, and `nodePolicyAttribution` require upstream `eventId/eventType/queryTime/policyCode/policyVersion`; missing fields become `missing_upstream_id`, not auth failure.
- `eventList completed_no_hit` and empty `hitPolicies` are not no-risk evidence. Use detail/custom columns when upstream IDs exist.

DataAgent / Hive registry preflight:

- Before any DataAgent/Hive call for account security, ATO, login anomaly, password reset, passToken, kick out, login success/failure, or historical login-chain analysis, read `computer_use_poc/batch_risk_clustering/account_security_hive_source_registry_v1.md`.
- Before every DataAgent / Hive execution, ask for explicit user confirmation. This applies to each new SQL, new problem, new time range, new table, and new evidence direction.
- "查吧 DataAgent" authorizes only the current described query. Follow-up prompts such as "继续查", "再查一下", "看设备活跃", or "查同设备其他账号" must produce a new query description and wait for confirmation if they require DataAgent / Hive.
- DataAgent / Hive plans, recommended SQL, table selection, and analysis of already returned results can be produced without confirmation.
- The DataAgent prompt must include Dennis registry-recommended tables, table purpose, time window, partition requirements, key fields, and no-data interpretation.
- Successful login must prioritize `ks_rc_bs.ks_account_login_basic_info`.
- Login failure / credential stuffing / brute force / resetPwd must prioritize `ks_rc_bs.dwd_risk_usr_accnt_login_orign_info` with `p_action_type='login'` or `p_action_type='resetPwd'` as applicable.
- Web RCP and App RCP should use registry tables before generic warehouse discovery.
- If DataAgent suggests a non-registry table such as a general business login fact table, mark it `candidate_secondary_source`; it must not replace the registry table unless the registry table is unavailable or does not contain required fields.
- If registry table permission or fields are unavailable, then DataAgent may search candidate tables, but the answer must preserve the registry gap and explain the fallback.
- Output must separate `online_api_evidence`, `hive_registry_recommended_source`, `dataagent_candidate_source`, and `missing_hive_result`.
- A submitted or pending Hive/DataAgent job is not an evidence result. Mark it `missing_hive_result` or `hive_query_pending`, not completed evidence.

This guard is a main-agent routing contract, not only a prompt paragraph. The main agent entry layer must produce a normalized routing decision before any downstream task:

```yaml
routing_decision:
  entry: kim | app | web | future
  detected_intents:
    - ato_single_case
    - ato_expansion
    - black_market_paused_branch
  mode_by_intent:
    ato_single_case: execution_readonly
    ato_expansion: plan_mode_only
    black_market_paused_branch: fast_ack
  mixed_request_decomposed: true
  dennis_spawn_allowed: true
  dennis_spawn_slice: ato_single_case_only
  dataagent_allowed: false
  write_action_allowed: false
  field_output_policy: field_output_classification_policy_v1
```

If this routing decision cannot be produced, the entry must fail closed to plan-only or clarification instead of spawning Dennis execution.

## 2A. Task Fingerprint And Context Boundary Guard

Before using previous conversation context, the entry layer must build a `task_fingerprint`.

```yaml
task_fingerprint:
  task_type: single_case_analysis | interface_alert_analysis | batch_analysis | strategy_design | methodology | validation_followup
  subject_type: user | device | interface | campaign | channel | batch | general
  subject_ids:
    - "<UID | DID | IP | interface | rule_id | batch_id | safe_ref>"
  time_window:
  risk_domain:
  user_intent:
```

Then assign `context_mode`:

```yaml
context_mode: fresh_context | same_task_continuation | same_batch_continuation | methodology_mode
```

Context mode rules:

- `fresh_context`: new subject, new task type, new risk domain, new time window, or unclear relation. Do not inherit previous evidence.
- `same_task_continuation`: same task fingerprint and same subject/time window. Evidence inheritance is allowed with provenance.
- `same_batch_continuation`: same batch id or same case set and same risk domain. Batch-level evidence inheritance is allowed with provenance.
- `methodology_mode`: user asks concepts, methodology, strategy principles, or evaluation framework. Inherit domain knowledge and templates only, not case evidence.

Default inheritance policy:

| context object | default inheritance |
|---|---|
| domain_knowledge | allowed |
| methodology | allowed |
| response_template | allowed |
| previous_case_evidence | denied unless same_task/same_batch fingerprint matches |
| previous_tool_observation | denied unless same_task/same_batch fingerprint matches |
| previous_entity_ids | denied unless explicitly re-mentioned or same_task/same_batch fingerprint matches |
| previous_final_judgement | denied unless same_task/same_batch fingerprint matches and is cited as previous judgement |

Historical cases can be used only as general pattern or hypothesis. They must not be used as current evidence.

Response-time provenance check:

- Factual evidence must come from `current_input` or `current_task_observation`.
- Do not cite UID / DID / IP / BSSID / interface / platform observation outside current task scope.
- Missing join key means no "same gang", "same attack chain", "same batch risk", or "shared infrastructure" conclusion.
- If historical case is referenced, label it as "historical experience / similar pattern", not evidence for the current task.

Required output labels when historical context is relevant:

```yaml
current_task_evidence:
historical_context:
hypothesis:
missing_join_key:
required_validation:
```

## 3. Core Routing Modes

### A. execution mode

Applies to:

- ATO single-case fact judgement.
- User provides clear `user_id`, event time window, and abnormal action.
- Explicit single-entity query such as "帮我查 / 帮我看 / 看近期登录 / 看设备关联 / 看策略命中 / 判断这个具体 case".

Behavior:

- May perform readonly observation.
- Output concise evidence card.
- No disposition.
- No automatic expansion.
- No DataAgent unless explicitly authorized by a separate offline analysis flow.
- If a source is blocked, timed out, or unavailable, output partial evidence card instead of empty methodology.
- Required partial fields: `completed_sources`, `blocked_sources`, `timeout_sources`, `parse_error_sources`, `missing_evidence`, `source_quality`, `freshness_status`, `permission_status`, `next_action`.
- ATO single case with explicit `user_id` stays in `single_entity_execution_mode`; do not downgrade it to plan-only by default.
- Weapon / login log / archives / strategy hit timeout, auth block, or parse error must degrade to partial evidence card. If all sources fail, output query plan plus missing evidence instead of a bare timeout.
- Single-case ATO conclusion status must be one of `data_supports_ato_suspicion`, `insufficient_support`, or `data_against_ato_suspicion`.
- Per-source checkpoint is mandatory. After each source finishes, record `source_name`, `source_type`, `source_status`, `evidence_summary`, `evidence_time_range`, `source_quality`, `raw_reference_safe_id`, `collected_at`, `failure_reason`, and `next_source_decision`.
- Completed P0/P1 sources must be retained even if later P2 browser sources time out. `no_data` is still a completed source and must carry `no_data_not_risk_exclusion`.
- Default total budget is 180s. If any P0/P1 source has completed, stop extending P2 browser sources at the 120s or 150s checkpoint and emit partial evidence before the overall timeout.
- Source priority must follow evidence value, not access method. For ATO: P0 = Archives Center user analysis, unified login log, Weapon graphData; P0-explicit = Tianshi strategy hit when the user asks policy hit; P0-conditional = publish chain / publish device for abnormal publish cases and Weapon riskData after a suspicious deviceId is resolved; P1/P2 = deeper device SDK, browser DOM fallback, offline supplement, and other non-blocking evidence.
- ATO source priority corrected: 档案中心用户分析是 P0 account baseline source；统一登录日志是 P0；Weapon graphData 是 P0；Weapon riskData 是 `P0-conditional / P1`，只有 graphData / 登录日志 / 发布链路 / track-analysis 等 source 产出可疑 `deviceId` 后触发；用户明确问策略命中时天师策略命中是 `P0-explicit`；涉及发布作品、异常发布、作品引流、非本人发布、内容操作时，发布作品 / 发布时间 / 发布设备 / 发布来源链路是 `P0-conditional`；track-analysis 对协议上号、OAuth / 扫码、后端有事件但前端无活跃、异常发布当天无真实前端活跃等场景可升为 P0。
- P0 multi-source orchestration gate: for single-user account security / ATO / login anomaly cases, `user_login_unified_log` is only the first P0 source, never the terminal judgement source. Whether login log returns `completed`, `no_data`, `auth_failed`, `timeout`, or `parse_error`, continue the default P0 sequence unless the overall deadline is reached: `user_login_unified_log` -> Weapon USER_ID to DEVICE_ID graphData -> Weapon device riskData for resolved devices -> Tianshi strategy hit summary when sourceId/time_window is available -> Archives profile availability check. Each unavailable source must still checkpoint as `blocked`, `auth_failed`, `timeout`, `parse_error`, or `not_checked`.
- Browser-backed fixed actions v1 source plan: for ATO / login anomaly, the default source plan is `login_logs_search -> archives_user_profile -> archives_user_analysis -> track_analysis_check_data_ready`. Archives Center is a key evidence item for account state and behavior closure, but not a hard blocker: `auth_failed`, `no_data`, `partial_observation_available`, `timeout`, `blocked`, or `parse_error` enter `source_quality` and `missing_evidence`, then Dennis outputs partial evidence instead of stopping or turning the failure into low-risk counter-evidence.
- Browser-backed fixed actions v1 publish/spread branches: abnormal publish / traffic diversion / content handoff plan `archives_photo_search -> archives_user_profile -> archives_user_analysis`; black-market account spread / same-device plan `archives_related_users -> archives_user_profile -> login_logs_search -> track_analysis_check_data_ready`. `archives_photo_search no_data` does not exclude abnormal publish, and `archives_related_users` / same-device relation is only an expansion clue, not a gang conclusion.
- Browser-backed fixed actions v1 unstable source boundary: private message, profile four-items, past four-items, and `related_devices` are follow-up only unless a stable interface, explicit clue, or user-supplied line of inquiry exists; they must not be described as default verified required sources.
- The P0 sequence above is dependency-aware, not a fixed unconditional list: `weapon_device_risk` requires a raw `deviceId` from graphData / login_log / publish_chain / track_analysis; if no device reference exists, record `missing_device_reference` instead of claiming riskData coverage.
- ATO time_window_inference is a P0 pre-step. If the user only provides `user_id`, do not treat the latest 7 days as the only window. Build candidate windows from user_report_time, archives user analysis device/account changes, audit log reason/time, recent publish_time, publish_device_time, strategy_hit_time, login_event_time, device_first_seen_time, and track-analysis frontend_activity_time.
- Weapon path hard rule: use `/apiv2/graphData?product=KUAISHOU&productName=KUAISHOU&groupValue={userId}&groupKey=USER_ID&dimKey=DEVICE_ID&searchLevel=2` for user-to-device resolution, then `/apiv2/riskData?product=KUAISHOU&deviceIds={deviceId}` for device risk. Do not use `/api/graphData` as default guidance, and do not freely explore alternate frontend paths after `/apiv2/*` fails; record the failure in `source_quality`.
- If P0 source execution cannot complete, output a partial evidence card with completed / no_data / blocked / auth_failed / timeout / parse_error / not_checked sources. Do not stop at a single login-log `no_data` conclusion.
- Track-analysis supporting source must only be marked `completed` when the executable endpoint is verified in the current runtime. If the contract says `api_direct_confirmed` but the live executable endpoint is not verified, downgrade that source to `pending_api_direct_confirmation` / `source_gap` and do not use it as completed evidence.
- Observation logging must start with a skeleton record and append per-source checkpoints. A timeout must still leave a partial or timeout observation record.
- Main agent must not take over direct platform execution after dennis-risk-agent timeout. It may record `subagent_timeout` and return partial / retry plan, but must not run `sso_session.py`, curl with cookie, agent-browser state load, or same-origin fetch by itself.
- Unified login log readonly observation must use the controlled wrapper / dennis-risk-agent source orchestration. Temporary curl + cookie is not an allowed fallback.
- SSO state presence does not prove API direct availability. Redirect / 302, same-origin failure, browser profile lock, and auth failure must be recorded as source quality issues: `auth_session_issue`, `same_origin_error`, `profile_lock`, or `auth_failed`.
- For 2-9 user ATO complaint batches, default to `small_batch_execution_with_checkpoint`, not pure plan-only. Query P0 sources per user, starting with unified login log. Add P1 sources only for anomalous users. P2 browser sources are excluded from the default small-batch path.
- Single user/source auth failure, timeout, blocked, or parse error must not collapse the whole small batch into no output.
- Unified login log online API is reliable only for about 7 days and mainly covers APP login / refresh token / password verification. Complaint time outside that window must be marked `login_log_window_incomplete` and `source_time_range_gap`.
- APP login no_data, single DID, or stable IP can only support `app_login_visible_window_no_strong_anomaly`; it cannot output low risk, no risk, or ATO exclusion without other counter evidence.
- For scan/OAuth, offline promotion fraud, unfamiliar link, violation posting, or friend deletion complaints, normal APP login logs must still carry `app_login_only_source_gap`, `missing_oauth_or_scan_chain`, `missing_publish_audit`, `missing_device_sdk`, and `missing_strategy_hit` as relevant.
- Runtime guard depends on runtime config apply. A readonly template in the repo is not enough: live `openclaw.json` must contain a dedicated `dennis-risk-agent` entry with `exec.security=allowlist`, `safeBins`, `tools.deny`, `fs.workspaceOnly=true`, and `loopDetection`.
- If dennis is still inheriting full-profile defaults, mark `runtime_config_not_applied`. Do not claim semi-open safety boundaries are active, and do not treat wrapper-first / tools deny / safeBins as hard constraints.
- When `runtime_config_not_applied` appears, risk answers must expose `source_quality` / `runtime_config_gap`, and main agent still must not directly take over platform querying.

### B. plan mode

Applies to:

- ATO 举一返三.
- Similar victim discovery.
- Same attack batch check.
- Expansion planning.
- Strategy evaluation / kill-vs-review separation / batch expansion.
- Strategy recommendation / monitoring metrics / grey release / false-positive control / governance design even when the prompt contains `user_id`.
- 3+ `user_id` or `device_id` batch analysis unless the user has explicitly confirmed real batch execution cost and scope.
- 10+ detected entities of type `user_id` / `device_id` / `did` / `ip` / `account` / generic entity. This is a hard guard: route to `batch_clustering_mode` or plan mode, never one-by-one online execution by default.

Behavior:

- Do not call tools.
- Do not call DataAgent.
- Do not query more users.
- Only output DataAgent / Hive query plan.
- Must explicitly include `offline_hive_required=true` and `DataAgent_plan_needed=true`.
- For batch prompts, output case registry requirements, pattern summary plan, evidence layering, missing evidence, and DataAgent/Hive query plan.

### B1. hard batch routing guard

This guard runs before execution mode selection.

```yaml
batch_routing_guard:
  entity_count_3_9: batch_plan_mode
  entity_count_10_49: batch_clustering_mode
  entity_count_50_plus: large_batch_aggregation_mode_or_DataAgent_Hive_query_plan
  default_online_execution_allowed: false
```

Rules:

- If the input contains 10 or more `user_id`, `device_id`, `did`, `ip`, `account`, or entity identifiers, execution mode is blocked unless the user explicitly says "逐个查每个用户", "逐个在线查询", or "每个都调平台查".
- For 10-49 entities, select `batch_clustering_mode`.
- For 50+ entities, select aggregation / DataAgent-Hive query plan and do not run online one-by-one checks.
- For 2-9 ATO complaint users, use `small_batch_execution_with_checkpoint` and P0-only default execution.
- For 3-9 non-ATO entities, default to `batch_plan_mode`; if the user asks for small-sample execution, ask for confirmation or limit to representative samples.
- Strategy recommendation, expansion, grey release, false-positive control, monitoring, and governance requests remain plan mode even when user ids are attached.
- Required batch output fields: `batch_clustering_mode`, `relation_family`, `evidence_basis`, `denominator_status`, `relationship_strength`, `reverse_check_result`, `confounder_risk`, `cannot_conclude_boundary`, `representative_cases`, `pattern_summary`, `required_validation`, `candidate_strategy_direction`.

### B2. evidence boundary mode

Applies to principle questions:

- "登录日志查不到异常登录，是不是可以排除盗号？"
- "设备关联是否能直接判定作弊？"
- "只有模型高风险分，能不能作为强证据？"
- "只有用户反馈，没有平台证据，能不能判定账号被盗？"

Behavior:

- Pure analysis by default.
- Do not call platform tools unless the user explicitly asks to query a concrete `user_id` / `device_id`.
- Respond within short-answer budget.
- Explain that `no_data`, `timeout`, `blocked`, model scores, user feedback and device association are not standalone strong evidence.

### B3. non-ATO expert mode

Applies to anti-crawler, protocol attack, traffic diversion, activity abuse, channel arbitrage, and generalized group-control questions without explicit platform lookup request.

Behavior:

- Expert analysis first.
- Do not default to browser / Archives / Weapon.
- Output attack-path hypothesis, evidence fields, low-cost validation plan and strategy direction.
- If data is needed, produce readonly/API plan or DataAgent/Hive query plan, not execution by default.

### C. fast_ack / async_ack

Applies to:

- `black_market_account_matrix` paused branch.
- Offline long-running tasks.
- Paused deep-dive branches.

Behavior:

- Reply immediately with status.
- Do not enter heavy skill loading.
- Do not block the current entry response.
- If offline analysis is needed, return async acknowledgement only; do not treat it as executed.

## 4. Mixed Request Decomposition

When one user message includes:

- ATO single case.
- ATO expansion / similar victims / same attack batch check.
- black_market_account_matrix / side-branch analysis.

The entry route layer must decompose it before Dennis execution:

- ATO single case -> Dennis execution slice.
- ATO expansion -> plan-only response.
- black_market_account_matrix -> fast_ack / closure.

Never pass the full mixed prompt to one Dennis execution task.

Main-agent routing contract:

- ATO single case -> `execution_readonly`.
- ATO expansion / 举一返三 -> `plan_mode_only`.
- black_market_account_matrix paused branch -> `fast_ack` / `async_ack`.
- DataAgent request -> `plan_only` / `require_confirmation` unless explicitly authorized in a separate offline flow; account security / ATO DataAgent prompts must run `hive_source_registry_preflight` first and cite `account_security_hive_source_registry_v1.md`.
- write / mutation / disposition request -> `deny` or `plan_only` with manual review boundary.
- credential or high-sensitive raw output request -> `deny` / `redact`.

Required output order:

1. Routing Summary.
2. Plan-only response for ATO expansion.
3. Fast-ack / closure for black_market_account_matrix.
4. ATO single-case concise execution, if available within time budget.

If execution times out, parts 1-3 must still be returned.

## 5. Entry Differences

| Entry | Runtime constraint | Recommended response |
|---|---|---|
| KIM | Short message, latency sensitive, easy to timeout | Routing Summary first, fast_ack, concise evidence card |
| APP | Can render structured cards and buttons | Separate cards for execution result, query plan, follow-up choices |
| Web | Can carry longer reports and tables | Evidence table, run log link, exportable report, still obeying field policy |

## 5A. Timeout, Browser, API Stability And Length Control

Runtime fallback rules:

- Browser auth blocked -> `permission_or_runtime_gap`.
- 2FA -> `auth_factor_required`.
- HTML / auth page returned to API or browser fetch -> `auth_session_issue`.
- Cookie bridge missing -> `cookie_bridge_missing`.
- JSON parse failure -> include `raw_response_type` and `parse_error`, then degrade to partial evidence.
- Single source timeout must not become a bare timeout response.
- Batch single-user failure must not block the whole batch plan or summary.

No live auth repair in business case:

- Applies to KNC case execution, single-user account security execution, small batch execution, batch execution, and normal user risk investigation.
- If any platform redirects to a login page / SSO page / `account.p` page, returns HTML login content, reports auth failure, permission blocked, or path error, stop that source within 30 seconds.
- Mark `source_status=auth_session_issue` or `source_gap`, add it to `remaining_source_gaps`, and do not block completed P0 evidence card output.
- Do not treat `auth_session_issue` / `source_gap` as low-risk or no-risk counter evidence.
- Forbidden in business case execution: click login page, type username/account, complete SSO interactively, guess URL/domain/API path, search historical sessions for URL, debug cookie/session/header, or repair auth state for a conditional source.
- Archives Center special rule: use only `admin.p.adm-corp.kuaishou.com` as the confirmed entry. If it redirects to `account.p.adm-corp.kuaishou.com`, mark `archives_auth_session_issue`; do not click "next" / "下一步" in the business case. "下一步" is allowed only in a separate auth activation task.

Answer length:

- Expert cognition answers default to about 500 Chinese characters.
- Batch analysis defaults to about 800 Chinese characters.
- KIM always prefers concise evidence card and safe_ref / follow-up for long details.

Device SDK shorthand:

- For "设备 SDK 指纹取数怎么看", answer directly with three layers: device risk labels, SDK fingerprint fields, and device-side corroboration boundary.

## 6. Field Output Classification

All entries must use `computer_use_poc/field_output_classification_policy_v1.md`:

- Credential plaintext is never output.
- High-sensitive personal information is redacted by default.
- Risk entity fields are controlled by audience scope.
- Derived / aggregate features are preferred.

For broader semi-open or external sharing, prefer `safe_ref`, partial mask, counts, distributions, and derived features over raw detail.

## 7. Relationship To KIM Patch

- `computer_use_poc/kim_runtime_prompt_patch_v1.md` remains the KIM-specific implementation sample.
- `computer_use_poc/multi_entry_runtime_guard_v1.md` is the higher-level unified rule.
- APP and Web should implement this multi-entry guard directly rather than copying the KIM patch.

## 8. Validation Rules

- `multi_entry_runtime_guard_required_before_dennis_spawn`.
- `app_entry_ato_expansion_plan_mode_only`.
- `web_entry_ato_expansion_plan_mode_only`.
- `kim_entry_black_market_fast_ack`.
- `app_web_field_policy_consistent_with_kim`.
- `mixed_request_decomposed_before_dennis_execution_for_all_entries`.

## 9. Boundaries

- This is a routing and output policy contract.
- It does not call real platforms.
- It does not call DataAgent.
- It does not modify release / dist.
- It does not create a new KIM patch version.
