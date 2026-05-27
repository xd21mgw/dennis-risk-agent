# Runtime Integration Validation Checklist v1

## Scope

This checklist validates whether the semi-open runtime, feedback loop, evidence quality patches, asset preflight, and batch risk clustering pack are connected correctly in a live or staging runtime. It is a validation checklist, not a data query plan. Do not access real platforms, call DataAgent, or mutate auth/gateway state while using this checklist unless a separate production rollout owner explicitly approves.

## Execution policy

- Default validation mode: local / staging dry-run.
- Platform calls: not allowed for this checklist.
- DataAgent calls: not allowed for this checklist.
- Output policy: safe_summary only.
- Sensitive content: do not print cookie, token, session, header, API key, phone number, raw internal platform JSON, or raw historical run log.
- Release gate: future packages must pass `python3 computer_use_poc/release_preflight_check.py outputs/release/<release_name>`.

## Checklist

| check_id | area | validation | expected result | status |
|---|---|---|---|---|
| RUNTIME-INTEGRATION-001 | routing | KIM/webchat risk question is routed to `dennis-risk-agent` rather than generic assistant handling. | Dennis risk runtime is spawned for risk scenes. | pending |
| RUNTIME-INTEGRATION-002 | routing | Main agent direct-exec behavior still works for non-Dennis local coding tasks. | Main agent is not hijacked by Dennis routing. | pending |
| RUNTIME-INTEGRATION-003 | follow-up | Follow-up prompts such as `查一下吧` / `继续` / `看下` inherit the prior risk context when no new batch fingerprint exists. | Prior context is inherited and Dennis is spawned. | pending |
| RUNTIME-INTEGRATION-004 | follow-up | New `batch_id`, new entity set, new time window, or new risk domain appears after prior ATO task. | `fresh_context` is selected; prior evidence is not reused. | pending |
| RUNTIME-INTEGRATION-005 | semi-open logging | Semi-open pilot observation can write safe summary logs. | `semi_open_pilot_logs` write path is append-only and redacted. | pending |
| RUNTIME-INTEGRATION-006 | feedback | `feedback_record` can be written after a KIM follow-up. | Feedback record includes `linked_previous_record_id` when available. | pending |
| RUNTIME-INTEGRATION-007 | feedback | High-value feedback enters the runtime candidate queue. | Runtime path is `runtime_logs/question_collection/question_learning_candidate_queue_v1.csv`. | pending |
| RUNTIME-INTEGRATION-008 | feedback | `useful` feedback without high-value learning signal is recorded but not queued by default. | Candidate queue is not polluted by generic useful feedback. | pending |
| RUNTIME-INTEGRATION-009 | feedback | Template candidate queue is not used as live output. | `computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv` remains template/sample only. | pending |
| RUNTIME-INTEGRATION-009A | feedback | `DENNIS_AGENT_HOME` is set in live and writer runs from different CWDs. | Observation log and candidate queue resolve under the same Dennis home; output includes `path_resolution`, `log_path_resolution`, and `candidate_queue_path_resolution`. | pending |
| RUNTIME-INTEGRATION-009B | feedback | Observation writer output format is inspected. | Markdown block only, with JSON metadata containing `direct_tool_bypass`, `bypass_reason`, `risk_review_required`, `feedback_type`, `candidate_appended`, `candidate_queue_path`, `path_resolution`, `subagent_session_id`, and `main_session_id`. | pending |
| RUNTIME-INTEGRATION-009C | feedback | Candidate queue explicit path points at `computer_use_poc/question_collection/question_learning_candidate_queue_v1.csv` or release template CSV. | Writer fails closed; runtime never appends to template CSV. | pending |
| RUNTIME-INTEGRATION-009D | metadata | Formal answer routing metadata is inspected. | Metadata is YAML, not JSON; includes `evidence_mode`, `direct_tool_bypass`, and nested `source_quality`; route / capability use registered names. | pending |
| RUNTIME-INTEGRATION-010 | evidence | Evidence type separation is applied. | Output separates `raw_evidence`, `behavior_event`, `user_claim`, `inference`, `hypothesis`, and `missing_evidence`. | pending |
| RUNTIME-INTEGRATION-011 | evidence | Single case ATO response uses the evidence card. | Output contains source quality, completed/blocked/timeout sources, current confidence, and required follow-up. | pending |
| RUNTIME-INTEGRATION-012 | boundary | `no_data`, timeout, blocked, or partial source appears. | It is marked as `source_gap` / `permission_or_runtime_gap`, not as no-risk counter-evidence. | pending |
| RUNTIME-INTEGRATION-012A | orchestration | ATO single case has unified login log completed, then Weapon / RCP / archives browser timeout. | Completed source checkpoint is preserved; partial evidence card is emitted with routing_metadata `final_status=partial`; no bare timeout. | pending |
| RUNTIME-INTEGRATION-012B | deadline | ATO single case P0/P1 source completes before P2 browser source hangs. | Runtime stops P2 expansion at 120s/150s checkpoint and emits partial evidence before 180s overall deadline. | pending |
| RUNTIME-INTEGRATION-013 | track analysis | Track-analysis task starts stats-first. | Aggregate stats or query plan comes before browser exploration. | pending |
| RUNTIME-INTEGRATION-014 | browser | Track-analysis SPA loop fails 3 times. | Runtime downgrades to partial evidence card and stops looping. | pending |
| RUNTIME-INTEGRATION-015 | context | Cross-task context contamination regression is replayed. | Historical evidence is not reused as current task fact evidence. | pending |
| RUNTIME-INTEGRATION-016 | bad case | `BC-HARMONY-ATO-001` is replayed. | Harmony/OAuth/one-click takeover is not collapsed into credential stuffing. | pending |
| RUNTIME-INTEGRATION-017 | bad case | Batch ATO has mixed case types. | Runtime samples 3-5 representative users and asks for per-user timeline before strong attribution. | pending |
| BATCH-INTEGRATION-001 | batch routing | User asks: `这 10 个用户像不像一批 ATO？` | `batch_clustering_mode`; no one-by-one online checks; output clusters, representatives, abnormal correlation matrix, follow-up plan. | pending |
| BATCH-INTEGRATION-001A | batch routing | User provides 10 IDs and explicitly asks for batch clustering rather than per-user lookup. | Hard guard forces `batch_clustering_mode`; no platform API; output includes `required_validation` and no same-gang conclusion without join key. | pending |
| BATCH-INTEGRATION-002 | batch routing | Mixed positive and negative ATO-like cases are provided. | Layered cluster judgement; no forced single ATO conclusion. | pending |
| BATCH-INTEGRATION-003 | batch matrix | Inputs include multiple devices, IPs, versions, and nickname mutations. | Abnormal correlation matrix is emitted with direction and evidence boundary. | pending |
| BATCH-INTEGRATION-004 | batch denominator | Denominator or control baseline is missing. | `denominator_status=denominator_required` or equivalent; no strong enrichment claim. | pending |
| BATCH-INTEGRATION-005 | batch join key | Only correlation exists and no join key / shared infrastructure is present. | `cannot_conclude_boundary` states why same-source or group conclusion cannot be made. | pending |
| BATCH-INTEGRATION-006 | batch plan mode | User asks strategy recommendation, grey release, false-positive control, or expansion investigation with attached IDs. | `strategy_recommendation_plan_mode`; no platform call; DataAgent/Hive only as plan. | pending |
| BATCH-INTEGRATION-007 | batch threshold | Batch has more than 3 entities. | Default is no one-by-one online execution unless user confirms cost and scope. | pending |
| BATCH-INTEGRATION-008 | batch threshold | Batch has 50+ entities. | `large_batch_aggregation_mode` or population analysis; DataAgent/Hive query plan only. | pending |
| BATCH-INTEGRATION-009 | batch response | Batch clustering response is checked for required sections. | Pattern summary, cluster explanation, representative cases, candidate strategy direction, and required validation are present. | pending |
| BATCH-INTEGRATION-010 | batch matrix | Matrix row is checked for runtime fields. | Includes `relation_family`, `evidence_basis`, `denominator_status`, `relationship_strength`, `reverse_check_result`, `confounder_risk`, and `cannot_conclude_boundary`. | pending |
| ASSET-INTEGRATION-001 | preflight | Safe mock release preflight is run. | Exit 0 with `preflight_pass=true`. | pending |
| ASSET-INTEGRATION-002 | preflight | Risky mock release preflight is run. | Exit 1 with `preflight_pass=false` and `package_should_block=true`. | pending |
| ASSET-INTEGRATION-003 | preflight | Scanner emits no JSON, parse error, or execution error. | Preflight fails closed and exits 1. | pending |
| ASSET-INTEGRATION-004 | preflight | Release package contains critical or unallowed high findings. | Packaging and upload are blocked. | pending |
| ASSET-INTEGRATION-005 | preflight output | Preflight output is inspected. | Safe summary only; no raw sensitive file content. | pending |
| CONSISTENCY-001 | release/live/local | Local runtime files, live overlay files, and release candidate file list are compared. | No missing required runtime files and no local-test-only files copied into release. | pending |
| CONSISTENCY-002 | release/live/local | `outputs/dist` and `.DS_Store` are checked. | Neither enters release. | pending |
| CONSISTENCY-003 | release/live/local | Field output policy is checked. | Credential cleartext is never output; high-sensitive personal fields are redacted. | pending |

## Pass criteria

- All routing, evidence, batch, asset, and consistency checks are marked pass by the release owner.
- `ASSET-INTEGRATION-001` passes.
- `ASSET-INTEGRATION-002` blocks.
- No checklist step requires real platform access or DataAgent execution.
- Any failed step blocks release overlay until the owning file is corrected and revalidated.

## Fail criteria

- Dennis risk scenes are not spawned from KIM/webchat.
- Main agent direct-exec is broken for non-risk coding tasks.
- Follow-up context contaminates a new batch.
- `no_data`, timeout, or blocked source is treated as no-risk evidence.
- Batch risk clustering does not produce an abnormal correlation matrix.
- Batch correlation is upgraded to same-source/group conclusion without join key or shared infrastructure.
- Preflight fails, scanner fails, scanner output cannot be parsed, or high-risk package findings exist.
