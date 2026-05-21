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

Behavior:

- May perform readonly observation.
- Output concise evidence card.
- No disposition.
- No automatic expansion.
- No DataAgent unless explicitly authorized by a separate offline analysis flow.

### B. plan mode

Applies to:

- ATO 举一返三.
- Similar victim discovery.
- Same attack batch check.
- Expansion planning.
- Strategy evaluation / kill-vs-review separation / batch expansion.

Behavior:

- Do not call tools.
- Do not call DataAgent.
- Do not query more users.
- Only output DataAgent / Hive query plan.
- Must explicitly include `offline_hive_required=true` and `DataAgent_plan_needed=true`.

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
