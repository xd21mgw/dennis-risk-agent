# Multi-entry Runtime Guard v1

Guard marker: `DENNIS_ROUTING_GUARD_V1`.

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
- Evidence mode output must include `evidence_card`, `source_quality`, and `routing_metadata`.
- If any required block is missing, self-correct before final output.
- Do not output natural-language judgement only.
- `no_data`, `timeout`, `blocked`, `auth_failed`, stale source, and partial source are quality states, not no-risk counter evidence.
- Strategy hit, rule hit, model score, blacklist hit, risk tag, or confidence level cannot be the only strong evidence.
- Separate `raw_evidence`, `strategy_hit`, `model_score`, `inference`, `user_claim`, `counter_evidence`, and `missing_evidence`.
- When new evidence arrives after an initial answer, recompute conclusion and mark `conclusion_recompute_after_new_evidence`.
- Every source must expose time window and coverage boundary; out-of-window gaps become `required_offline_check` / `missing_evidence`.

Release / overlay readiness gate:

- Before any release or live overlay, run `python3 computer_use_poc/runtime_preflight_check.py`.
- A checked-in template is not live runtime. Live config must still be validated separately.
- If runtime config is not applied, mark `runtime_config_not_applied`.
- If source wrapper is unavailable, expose `source_quality` and do not pretend wrapper-first succeeded.

Platform call preflight:

- Before any realtime platform source, read `computer_use_poc/platform_call_playbook_index.md` and the referenced platform playbook.
- If memory retrieval fails, fall back to files; do not guess platform paths.
- 实时只读 API 查询不需要用户确认 when required fields are complete.
- DataAgent / Hive / 大批量 / 写操作 / 高风险操作需要确认 or query plan.
- Each source must produce a checkpoint and source_quality.
- P1/P2 browser source must not block P0 partial evidence output.
- Old observations must not be used as "no-cache" realtime results.

DataAgent / Hive registry preflight:

- Before any DataAgent/Hive call for account security, ATO, login anomaly, password reset, passToken, kick out, login success/failure, or historical login-chain analysis, read `computer_use_poc/batch_risk_clustering/account_security_hive_source_registry_v1.md`.
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
- Source priority: P0 = unified login log, Weapon riskData/graphData, Tianshi strategy hit summary; P1 = archives profile, track-analysis stats-first; P2 = RCP browser, archives browser recoverable_preflight, track-analysis SPA detail.
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
