# eventList API-read Event Detail Contract v1

## Capability Positioning

`eventList API-read` provides request-level / event-level detail lookup for a specific event type and small time window. It complements `fastQueryHbase`; it does not replace it.

## Difference from fastQueryHbase

- `fastQueryHbase` answers whether there is a production strategy hit overview for a `sourceId` and time window.
- `eventList API-read` answers what a specific event record looked like, including request-level fields and realtime feedback details.

## Applicable Questions

- Check a specific registration event.
- Check a specific login event.
- Inspect eventType-level details.
- Inspect realtime feedback, error code, punishment action, IP, device signal, openId presence, or side effect operations.

## Not Applicable Questions

- Large-scale statistics.
- Cross-day query.
- Trend analysis.
- Full-scale estimation of non-hit requests.
- Strategy tree parsing.
- Strategy configuration logic explanation.

## Account EventType Mapping

```yaml
app_login:
  - LOGIN_AUDIT
  - ASYNC_LOGIN
web_login:
  - LOGIN_AUDIT_FROM_WEB
  - ASYNC_WEB_LOGIN
registration:
  - USER_REGISTER_NEW
  - REGISTER_NEW
```

## Input Fields

```yaml
source_id:
event_type:
start_time:
end_time:
page_index:
page_size:
status:
  observed_value: 2
tableHeaderList:
```

## Query Window Rules

- Keep the query window small.
- Prefer a window around known event time, usually plus / minus 5 to 15 minutes.
- Principle: do not query across days.
- If the user only says "today", first use existing evidence to locate a smaller window.
- If a long window is truly required, split it into bounded segments and record segmentation.

## Sampling Rules

- Strategy-hit events are treated as complete records.
- Non-hit strategy events may be sampled.
- `no_data` does not mean no risk.
- `no_data` does not mean no login, no registration, or no behavior occurred.
- `auth blocker` or permission failure must not be reported as `no_data`.

## Output Fields

```yaml
query_status:
event_list_count:
records_total:
requested_page_size:
returned_page_size:
extracted_events:
sampling_note:
limitations:
```

## Boundaries

- `sourceIds` empty means the query cannot be consumed as user-level evidence.
- Event detail can strengthen field-level evidence but cannot directly become final risk classification.
- Sensitive request metadata must be summarized, not pasted verbatim.
