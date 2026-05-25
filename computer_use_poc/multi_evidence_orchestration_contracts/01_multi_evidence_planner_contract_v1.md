# Multi Evidence Planner Contract v1

## Goal

The multi-source evidence planner builds a minimal, ordered evidence plan for complete risk assessment questions. Its goal is to avoid single-source overclaiming and make missing evidence visible.

The planner coordinates strategy evidence, login evidence, and profile evidence first. It only adds request-level Tianshi detail, offline aggregation, frontend behavior, or device evidence when the user question requires those sources.

## Input Fields

```yaml
source_id:
time_window:
user_question:
known_event_time:
known_event_type:
risk_domain:
```

## Output Fields

```yaml
query_plan:
evidence_sources:
execution_order:
fallback_rule:
boundary_notes:
```

## Default Minimum Three-source Plan

```yaml
default_minimum_sources:
  - tianshi_strategy_hit_check
  - unified_login_log_check
  - archives_center_profile_check
```

Execution order:

1. `tianshi_strategy_hit_check`: use C package `fastQueryHbase` to summarize strategy hit evidence.
2. `unified_login_log_check`: check login, token, verification, failed login, and account-security behavior chain.
3. `archives_center_profile_check`: check account profile, historical risk, current status, and profile-level counter evidence.

## Conditional Triggers

### tianshi_eventlist_api_read

Trigger only when the user needs:

- Specific request fields.
- eventType detail.
- Error code or realtime feedback.
- Punishment / side effect operation.
- IP, device signal, openId presence, or raw field summary.

Use the C package eventList contract. It requires non-empty `source_id`, small time window, and no cross-day query by default.

### DataAgent / Hive

Trigger only as query plan, not execution, when the user needs:

- Batch analysis.
- Cross-day or long-window analysis.
- Historical aggregation.
- Offline metrics, denominator, or baseline.

## Not Default

B v1 does not default-trigger:

- Strategy tree D package.
- Frontend activity E package.
- Device SDK F package.

These can be mentioned as future or optional evidence sources only when the user question requires them and their contracts are available.

## Boundary Notes

- Do not output a definitive conclusion from a single strong source.
- Tianshi hit is strategy evidence, not final cheating or ATO determination.
- Login token success can be nuance or counter evidence, not automatic no-risk proof.
- Historical punishment and today's strategy hit must not be merged into one causal chain without evidence.
- `blocked`, `timeout`, `auth blocker`, and `no_data` must remain separate states.
