# Tianshi Dual Interface Orchestration v1

## Default Combination Order

1. Run `fastQueryHbase` first when strategy hit overview is needed.
2. Add `eventList API-read` only if specific request / event fields are needed.
3. Reconcile Tianshi evidence with login logs and account profile before producing a risk assessment.

## When to Use Only fastQueryHbase

Use only `fastQueryHbase` when the user asks:

- "有没有被风控打到？"
- "是否命中生产策略？"
- "今天是否被阻止 / 验证？"
- "有没有策略命中证据？"

Output should summarize strategy hit evidence and boundary notes. It should not explain strategy tree logic.

## When to Use fastQueryHbase + eventList

Use both when:

- `fastQueryHbase` finds a relevant hit and the user asks for request fields.
- The user asks why a specific registration or login was allowed / blocked and wants IP, error code, realtime feedback, or side effect operations.
- A known event time and event type can define a small eventList window.

Example:

```yaml
user_question: "这次注册为什么允许，IP 和 sideEffect 是什么？"
plan:
  - tianshi_strategy_hit_check:
      query_type: fastQueryHbase
  - tianshi_eventlist_api_read:
      event_types:
        - USER_REGISTER_NEW
        - REGISTER_NEW
      window_policy: known_event_time_plus_minus_5_to_15_minutes
```

## When Not to Use eventList

Do not use `eventList` when:

- The user only asks for strategy hit overview.
- `source_id` is missing.
- Time window is missing and cannot be safely narrowed.
- The request is cross-day, trend-oriented, or large-scale aggregation.
- The user asks for strategy tree, node, condition expression, hit path, version, experiment, or grey-release explanation.

## Boundary Rules

- `eventList` does not cross days by default.
- `sourceIds` must not be empty when consumed as user-level evidence.
- `eventList no_data` does not mean the behavior did not happen.
- Non-hit events may be sampled.
- Strategy tree questions are outside B/C current capability and must be marked as future D package.
