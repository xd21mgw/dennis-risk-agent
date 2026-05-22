# Multi-entry Runtime Guard v1

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
- execution / plan / fast_ack mode decision.
- mixed request decomposition.
- field output policy selection.
- DataAgent execution boundary.
- response length / channel constraint.

The guard must run before tool call, browser access, DataAgent call, or `sessions_spawn`.

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

### B. plan mode

Applies to:

- ATO 举一返三.
- Similar victim discovery.
- Same attack batch check.
- Expansion planning.
- Strategy evaluation / kill-vs-review separation / batch expansion.
- Strategy recommendation / monitoring metrics / grey release / false-positive control / governance design even when the prompt contains `user_id`.
- 3+ `user_id` or `device_id` batch analysis unless the user has explicitly confirmed real batch execution cost and scope.

Behavior:

- Do not call tools.
- Do not call DataAgent.
- Do not query more users.
- Only output DataAgent / Hive query plan.
- Must explicitly include `offline_hive_required=true` and `DataAgent_plan_needed=true`.
- For batch prompts, output case registry requirements, pattern summary plan, evidence layering, missing evidence, and DataAgent/Hive query plan.

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
- DataAgent request -> `plan_only` / `require_confirmation` unless explicitly authorized in a separate offline flow.
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
