# Tianshi Routing and Tool Selection v1

## fastQueryHbase Trigger Conditions

Use `fastQueryHbase` when the user asks:

- Whether a `sourceId` hit a strategy.
- Whether it was hit by production risk-control / anti-cheating strategy.
- Whether there is strategy hit evidence in a bounded window.
- Why a request was blocked or verified at the strategy-evidence level.

Default capability: `strategy_hit_read`.

## eventList Trigger Conditions

Use `eventList API-read` when the user asks:

- Specific request fields.
- Specific eventType details.
- Realtime feedback, error code, punishment action, IP, device signal, openId presence, or side effect operations.
- Registration or login event detail around a known event time.

Default capability: `tianshi_eventlist_read`.

## Combination Strategy

- If the user only asks "was it hit by strategy", start with `fastQueryHbase`.
- If `fastQueryHbase` finds a relevant hit and the user needs field-level explanation, use `eventList API-read` for small-window detail.
- If `eventList` detail is blocked, sampled, or empty, preserve the strategy overview from `fastQueryHbase` and mark the detail source as partial.

## Do Not Trigger Tianshi

Do not trigger Tianshi query execution when:

- `source_id` is missing.
- Time window is missing and cannot be safely narrowed from existing evidence.
- The user asks for cross-day trends, large-scale statistics, or batch aggregation.
- The user asks for strategy tree, node, condition expression, hit path, version, experiment, or grey-release explanation.

For cross-day trends, large-scale statistics, denominators, or batch aggregation, generate a DataAgent / Hive query plan or ask the user to narrow the scope. Do not use `eventList` as a batch statistics tool.

## Relationship to Three-source E2E

In E2E user risk judgement:

- Tianshi provides strategy evidence.
- Unified login logs provide login / token / account-security behavior evidence.
- Account profile or archive sources provide profile / history / status evidence.

Tianshi alone must not be used as final cheating or ATO determination.

## Future D Package Boundary

If the user asks:

- Why exactly did this strategy condition trigger?
- What is the strategy tree?
- Which node / condition expression / hit path fired?
- What did this grey experiment or strategy version mean?

Then C package must mark:

```yaml
future_strategy_tree_capability: true
package_boundary: D_strategy_tree_capability
current_answer: C package can provide hit evidence and event detail only.
```
