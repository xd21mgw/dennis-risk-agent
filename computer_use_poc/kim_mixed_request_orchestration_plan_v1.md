# KIM Mixed Request Orchestration Plan v1

## 1. Purpose

This plan fixes the remaining KIM E2E F failure after KIM routing patch v1. KIM is the first validation entry; the same mixed request decomposition rule should apply to APP, Web, and future entries through `multi_entry_runtime_guard_v1.md`.

Patch v1 proves that the runtime task prefix works for single-purpose requests:

- B ATO expansion: pass, `plan_mode_only=true`, no tools, no DataAgent.
- E black_market_account_matrix paused branch: pass, `fast_ack=true`, no platform tools, no timeout.

F still fails because a single Dennis task receives execution, plan-only, and fast-ack work together. The execution part can consume the task budget before the plan-only and fast-ack parts are emitted.

## 2. Mixed Request Definition

A mixed request is one user message from KIM / APP / Web that simultaneously contains:

- ATO single-case fact judgement.
- ATO expansion / similar victims / same attack batch / expansion planning.
- black_market_account_matrix / 小号矩阵 / paused branch follow-up.

Example:

```text
看这个 ATO 单 case，同时判断有没有类似受害者，并看小号矩阵要不要继续排查。
```

## 3. Core Principle

Mixed request must not be passed to Dennis as one execution task.

The main agent / entry route layer must decompose the request before spawning or calling Dennis. Only the ATO single-case execution slice may be sent to Dennis execution. ATO expansion and black_market_account_matrix paused branch must be handled by the main agent as plan-only / fast-ack text.

This must be implemented as entry-layer routing logic, not only as a downstream Dennis prompt instruction. The routing layer must create an explicit decomposition record before `sessions_spawn`.

## 4. Recommended Orchestration

### Step 1: Main Agent Outputs Routing Summary

Before any tool call or child task spawn, the main agent outputs:

- ATO single case: route to Dennis execution, readonly only.
- ATO expansion: `plan_mode_only`, no tools, no DataAgent, no more user lookup.
- black_market_account_matrix: `fast_ack` / lightweight closure, no deep dive.

### Step 2: Main Agent Directly Emits Plan / Fast-Ack

The main agent emits these two lightweight parts before ATO execution:

- ATO expansion: concise DataAgent / Hive query plan, expansion anchors, scope control, manual review boundary, `offline_hive_required=true`, `DataAgent_plan_needed=true`.
- black_market_account_matrix: `pause_deep_dive=true`, `lightweight_closure=true`, `not_blocking_runtime_semi_open_test=true`, `batch_analysis_follow_up=true`, `async_ack_if_future_offline_analysis=true`.

These outputs must not wait for ATO execution to complete.

### Step 3: Spawn Only ATO Single-Case Execution To Dennis

The spawned Dennis task prompt must contain only the ATO single-case judgement request.

It must not include:

- ATO expansion / similar victims / 举一返三.
- black_market_account_matrix / 小号矩阵 follow-up.
- DataAgent / Hive expansion execution.

Dennis execution should return a concise evidence card:

- readonly only.
- key chain summary.
- strong / medium / weak / counter / missing evidence.
- no large log expansion in KIM response.
- no credential plaintext.

### Step 4: Main Agent Merges Three Result Parts

The final KIM response order is:

1. Routing Summary.
2. ATO expansion plan-only result.
3. black_market_account_matrix fast-ack.
4. ATO single-case concise execution result, if available within time budget.

If ATO execution times out, the response must still preserve parts 1-3.

## 5. Alternative

The main agent may split the mixed request into three child tasks:

- Dennis execution task for ATO single case.
- Plan-only task for ATO expansion.
- Fast-ack task for black_market_account_matrix.

This is acceptable, but less preferred than main-agent direct plan/fast-ack generation because the latter avoids unnecessary child task latency.

Do not put execution, plan-only, and fast-ack into the same child task.

## 6. Acceptance Criteria

- F is no longer handled by one Dennis task that receives the full mixed user prompt.
- Routing Summary is produced before any tool call or child task spawn.
- ATO expansion plan-only output is not blocked by ATO execution.
- black_market_account_matrix fast-ack output is not blocked by ATO execution.
- ATO execution timeout does not suppress Routing Summary, plan-only output, or fast-ack.
- Only the ATO single-case slice is spawned to Dennis execution.
- No DataAgent call is made for ATO expansion.
- No platform tool is called for black_market_account_matrix paused branch.

## 7. Boundaries

- This is an orchestration design, not a runtime implementation.
- No real platform call.
- No DataAgent call.
- No release / dist update.
- No automatic expansion.
- No automatic disposition.
