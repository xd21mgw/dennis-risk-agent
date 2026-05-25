# Batch Risk Case Schema v1

## 1. Purpose

This schema standardizes batch risk clustering input. It supports user, device, event, interface, channel, campaign and alert batches.

The schema separates:

- batch level context.
- case level entities and events.
- source metadata.
- evidence output boundary.

## 2. Batch Level Fields

| field | required | meaning |
|---|---|---|
| `batch_id` | yes | Stable batch identifier or safe_ref. |
| `batch_name` | no | Human-readable batch name. |
| `risk_domain` | yes | Account security, traffic anti-cheating, anti-crawler, activity abuse, diversion, infra, strategy recall, etc. |
| `scenario_type` | yes | ATO batch, device group-control, interface spike, channel arbitrage, alert secondary attribution, etc. |
| `source_channel` | no | Where the batch came from: alert, ops feedback, strategy recall, dashboard, manual sample. |
| `batch_trigger_reason` | yes | Why this batch needs analysis. |
| `time_window_start` | yes | Start time. |
| `time_window_end` | yes | End time. |
| `entity_count` | yes | Count of unique core entities. |
| `case_count` | yes | Count of cases / rows / alerts. |
| `user_goal` | yes | User asks for judgement, clustering, strategy plan, false-positive review, expansion, etc. |
| `expected_output_mode` | no | Desired output: short summary, pattern summary, report, strategy plan. |
| `available_evidence_summary` | no | Existing evidence sources and quality. |
| `missing_evidence_summary` | no | Known evidence gaps. |
| `sensitivity_level` | yes | internal_only, cross_team_safe_ref, external_redacted, etc. |

## 3. Case Level Fields

| field | required | meaning |
|---|---|---|
| `case_id` | yes | Stable case identifier. |
| `user_id` | conditional | User entity. |
| `device_id` | conditional | Device entity / DID / deviceceid. |
| `ip` | conditional | IP or safe_ref / subnet. |
| `app_version` | no | App version. |
| `os_type` | no | Android / iOS / Harmony / Web / unknown. |
| `os_version` | no | OS version. |
| `channel` | no | Acquisition / traffic / campaign channel. |
| `campaign_id` | no | Campaign or activity id. |
| `interface` | no | Endpoint / API / interface name. |
| `strategy_id` | no | Strategy or rule id. |
| `event_time` | yes | Main event time. |
| `abnormal_action` | yes | Abnormal action under review. |
| `risk_event` | no | Alert / hit / risk event name. |
| `user_claim` | no | User / ops feedback; weak evidence only. |
| `available_evidence` | no | Current evidence list. |
| `missing_evidence` | no | Missing evidence list. |
| `source_reference` | no | Safe source reference. |
| `priority` | no | high / medium / low / unknown. |
| `known_label` | no | Existing manual / strategy / model label. |
| `analyst_note` | no | Analyst note; manual_input only. |

## 4. Source Metadata

Each evidence item should carry:

| field | required | meaning |
|---|---|---|
| `source_name` | yes | Source name. |
| `source_type` | yes | internal_platform_api, browser_dom_read, dataagent_hive, manual_input, model_inference, historical_doc, user_claim. |
| `source_platform` | no | Platform name or safe_ref. |
| `collected_at` | no | Collection timestamp. |
| `evidence_time_range` | no | Time range covered by this source. |
| `freshness_status` | yes | fresh, stale, over_online_window, unknown. |
| `permission_status` | yes | available, blocked, timeout, partial, not_requested. |
| `reliability_level` | yes | high, medium, low, unknown. |
| `raw_reference` | no | Internal safe reference only. |

## 5. Field Output Boundary

- UID, DID, device_id and IP may be retained as internal risk analysis entity fields when audience and channel allow.
- Cross-team or external sharing should use safe_ref, partial mask, subnet, count or distribution.
- Do not output cookie / token / session / authorization / header / phone number / API key / password / secret.
- `raw_reference` must not contain credential, session, header or phone plaintext.
- raw platform response should be summarized into evidence metadata and derived features.

## 6. Minimal YAML Shape

```yaml
batch:
  batch_id:
  risk_domain:
  scenario_type:
  time_window_start:
  time_window_end:
  entity_count:
  case_count:
  user_goal:
  sensitivity_level:
cases:
  - case_id:
    user_id:
    device_id:
    ip:
    app_version:
    channel:
    interface:
    event_time:
    abnormal_action:
    available_evidence:
    missing_evidence:
source_metadata:
  - source_name:
    source_type:
    freshness_status:
    permission_status:
    reliability_level:
    raw_reference:
```
