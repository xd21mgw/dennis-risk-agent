# Browser-Backed Service Adapter v1

This adapter lets Dennis consume the local browser-backed API service without opening a browser or handling platform auth material inside `dennis-risk-agent`.

## Scope

- Service base URL: `http://127.0.0.1:8787`.
- Dennis calls only fixed service actions.
- The browser-backed service owns persistent browser context, origin readiness, same-origin checks, and source extraction.
- Dennis receives normalized source results and writes them into the source completion matrix.
- Action failures are source quality, not Dennis runtime failures, when the service returns the standard result contract.

## Fixed Action Mapping

| Dennis source need | Browser-backed action | Endpoint |
| --- | --- | --- |
| RCP strategy hit entry | `rcp_snapshot` | `POST /actions/rcp_snapshot` |
| Weapon device relation / risk | `weapon_inventory` | `POST /actions/weapon_inventory` |
| Login log online source | `login_logs_search` | `POST /actions/login_logs_search` |
| Track-analysis activity / profile | `track_analysis_summary` | `POST /actions/track_analysis_summary` |

## Adapter Boundary

Dennis must not:

- Start or debug a browser.
- Read `.ks_sso`, browser profile files, credential stores, or cookie DBs.
- Read, build, log, or forward cookie, token, session, authorization, or custom header material.
- Debug `sso_session_runner`, `SmartSSOSession`, auth bridge internals, gateway, or safeBins.
- Accept caller-provided `url`, `path`, `header`, `cookie`, `token`, `session`, or `secret` fields for this adapter.
- Expand the action allowlist from Dennis runtime.
- Treat `blocked`, `auth_failed`, `network_error`, or `platform_error` as a runtime crash when a standard source result is returned.

## Input Contract

The adapter passes only the minimal business identifiers required by the fixed action contract. If a required identifier is unavailable, Dennis records a source result with `source_status=invalid_parameter` or `source_status=missing_upstream_id` and does not guess values.

Forbidden input keys are rejected before service invocation:

```yaml
forbidden_input_keys:
  - url
  - path
  - header
  - cookie
  - token
  - session
  - secret
```

## Normalized Output

Every service action result entering Dennis should normalize to:

```yaml
browser_backed_source_result:
  source_name:
  action_name:
  source_status:
  failure_layer:
  error_type:
  latency_ms:
  source_card:
  source_quality:
  sensitive_output: false
  source_provenance: browser_backed_service
```

Required service fields:

- `source_card`
- `source_quality`
- `source_status` or `status`
- `error_type`
- `latency_ms`
- `sensitive_output=false`

Dennis must not persist or display a raw response full body from the browser-backed service.

## Status Normalization

| Service status / error | Dennis source_status | failure_layer | Handling |
| --- | --- | --- | --- |
| `ok` / `completed` | `completed` | `no_failure` | Enter completed source evidence. |
| `blocked` | `blocked` | `same_origin_context` or `path_permission` | Enter source completion matrix with source quality. |
| `auth_failed` | `auth_failed` | `auth_session` | Enter source completion matrix; do not start auth debug. |
| `network_error` | `blocked` | `network` | Enter source completion matrix; do not retry through browser debug. |
| `platform_error` | `platform_partial_available` | `platform_contract` | Enter source completion matrix as platform/source quality. |
| `parameter_error` | `invalid_parameter` | `parameter_contract` | Record missing or invalid action input. |
| `parse_error` | `parse_error` | `parser` | Record parser/source shape issue. |
| `timeout` | `timeout` | `timeout` | Record timeout source quality. |

If the HTTP transport to `127.0.0.1:8787` itself is unavailable, the adapter records `source_status=tool_gap` with `failure_layer=runner_invocation` and continues partial evidence.

## Partial Evidence Card Rule

Browser-backed action failures still produce a partial evidence card when any source result is standard:

```yaml
partial_evidence_card:
  source_name: login_logs_search
  source_status: auth_failed
  source_quality:
    permission_status: auth_not_ready
    freshness_status: current_task_observation
    error_type: auth_redirect
  evidence_value: missing_evidence
  next_action: "Retry after browser-backed service origin readiness is restored."
```

`blocked`, `auth_failed`, `network_error`, and `platform_error` must never be rewritten as low risk, no risk, or source absence.

## Executable Adapter

Implementation: `computer_use_poc/browser_backed_service_client.py`.

The executable client is intentionally narrow:

- Default `base_url`: `http://127.0.0.1:8787`.
- Default timeout: `10s`.
- Fixed action allowlist only:
  - `track_analysis_summary`
  - `rcp_snapshot`
  - `weapon_inventory`
  - `login_logs_search`
- Only typed params are serialized into the JSON body.
- Caller-provided route, credential, or transport override fields are rejected before service invocation.
- HTTP transport errors, connection refused, timeout, HTTP error, and non-JSON responses are normalized as source results instead of Dennis runtime failures.

Fixture self-test:

```bash
python3 computer_use_poc/browser_backed_service_client.py --self-test
```

The self-test does not require the browser-backed service to be running and does not call any live platform.

## Executable Normalization

The client reads these service fields when present:

- `source_status`
- `error_type`
- `latency_ms`
- `source_card`
- `source_quality`
- `sensitive_output`
- `status`

Normalization buckets:

| Normalized Dennis bucket | Accepted service statuses / errors |
| --- | --- |
| `completed_sources` | `completed`, `ok` |
| `no_data_sources` | `no_data`, `completed_no_data`, `completed_no_hit_for_small_window` |
| `auth_failed_sources` | `auth_failed`, `auth_redirect` |
| `blocked_sources` | `blocked`, `network_error`, `platform_error`, connection refused, service HTTP error |
| `timeout_sources` | `timeout`, service timeout |
| `parse_error_sources` | `parse_error`, non-JSON service response |
| `invalid_parameter_sources` | `parameter_error`, `invalid_parameter`, `wrong_request_body_shape` |

`sensitive_output` must be exactly `false`. If the service returns any other value, the adapter replaces the result with `source_status=blocked`, `error_type=sensitive_output_violation`, and `sensitive_output=false`.

## Partial Evidence Construction

`build_source_completion_matrix()` and `build_partial_evidence_card()` produce display-safe structures for Dennis runtime:

```yaml
partial_evidence_card:
  sensitive_output: false
  completed_sources: []
  no_data_sources: []
  blocked_sources: []
  source_quality: {}
  no_data_not_risk_exclusion: true
```

The adapter does not persist raw response full bodies, raw login records, raw device identifiers, raw IPs, raw labelInfo, or raw originalLog. It relies on `source_card`, `source_quality`, and service-provided shape summaries that are already sanitized by the browser-backed service.
