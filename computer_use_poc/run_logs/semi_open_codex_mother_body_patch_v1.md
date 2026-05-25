# Semi-open Codex Mother Body Patch v1

## 1. Goal

This run records local Codex mother-body fixes for confirmed semi-open pilot issues.

This round only updates local rules, templates, playbooks, regression cases, smoke tests, and run logs.

## 2. Boundaries

- real_platform_called: false
- DataAgent_called: false
- auth_or_gateway_modified: false
- real_query_executed: false
- runtime_modified: false
- release_repacked: false
- git_committed: false

## 3. Fixed Issue Classes

### 3.1 Evidence Type Separation

Problem:

- The Agent previously wrote inferred phishing entry or frontend/OAuth path as confirmed evidence.
- It also over-weighted "user says not me" and "违规内容发布" as if they were hard ATO evidence.

Fix:

- Evidence card must separate `raw_evidence`, `behavior_event`, `user_claim`, `inference`, `hypothesis`, and `missing_evidence`.
- User claim is weak evidence.
- Violation publish only proves behavior event occurred.
- Unobserved phishing page / OAuth / frontend behavior / token path must be missing evidence.
- Each single-case evidence item must include `evidence_type` and `strength`.

Regression:

- `EVIDENCE-TYPE-SEPARATION-001`

### 3.2 Single-case Evidence Card Required

Problem:

- Explicit single-user/case questions sometimes returned methodology or timed out without a stable evidence card.

Fix:

- `single_entity_execution_mode` must output evidence card or partial evidence card.
- Required fields: conclusion, confidence, strong/medium/weak/counter/missing evidence, completed_sources, blocked_or_timeout_sources, source_quality, next_action.

Regression:

- `SINGLE-CASE-EVIDENCE-CARD-001`
- `PARTIAL-EVIDENCE-BROWSER-BLOCKED-001`

### 3.3 Track-analysis Stats-first

Problem:

- Agent over-focused on behavior sequence detail and SPA controls, although stats-layer fields are sufficient first evidence.

Fix:

- Use `sequence_list` `USER_PROFILE_QUERY` direct URL first.
- Read stats-layer evidence first: monthly active days, device type, region, registration time, fan distribution, user/device profile.
- Behavior sequence is optional.
- Detail unavailable means `partial_source`, not timeout.

Regression:

- `TRACK-ANALYSIS-STATS-FIRST-001`

### 3.4 Browser / SPA Loop Guard

Problem:

- In one case, the Agent looped on track-analysis device dropdown and repeated screenshot/click attempts without progress.

Fix:

- Stop same browser/SPA action after 3 failed attempts.
- Mark `operation_loop_detected`, `platform_access_partial`, `browser_overuse`.
- Return partial evidence card and next action.

Regression:

- `TRACK-SPA-LOOP-001`

### 3.5 4972532542 Runtime Bad Case

Problem:

- A user-provided ATO-like case was over-scoped into Archives + track-analysis + device graph + login log full observation.
- Sub-agent looped or stalled in browser/SPA preflight / track-analysis controls.

Fix:

- Treat this as browser/SPA operation boundary issue, not core risk-brain failure.
- Publishing device mismatch is medium evidence, not standalone ATO proof.
- User claim is weak evidence.
- Browser blocked/loop returns partial evidence card.

Regression:

- `DEVICE-MISMATCH-ATO-001`
- `USER-CLAIM-WEAK-EVIDENCE-001`
- `PARTIAL-EVIDENCE-BROWSER-BLOCKED-001`

### 3.6 Field Semantic Bad Case

Problem:

- `mods=['POST', ...]` was misread as HTTP method POST.

Fix:

- `mod` / `mods` / `model` / `device_model` are device model fields.
- HTTP method evidence requires `method` / `request_method` / `http_method` / `requestMethod`.
- Protocol login requires combined evidence.

Regression:

- `BC-FIELD-SEMANTIC-001`

### 3.7 Protocol Downgrade Good Case

Fix:

- Client downgrade itself is not a risk conclusion.
- High-suspicion protocol login requires combined evidence: abnormal mod, encrypted-looking string, mixed versions, high old-version frequency, did mismatch, device profile difference, shared abnormal version/mod across users.

Regression:

- `GC-PROTOCOL-DOWNGRADE-001`

### 3.8 Cross-task Context Contamination

Problem:

- In macro traffic anti-cheating dashboard analysis, the Agent incorrectly linked current metric anomalies to previous micro cases without join keys.

Fix:

- Macro dashboard analysis must start from current metrics.
- Historical cases are `historical_context` or `hypothesis`, not current evidence.
- Cross-domain linkage requires join key: user_id, device_id, IP, BSSID, interface, surface, time window, strategy hit, or data-source return.
- Output must separate `current_metric_evidence`, `historical_context`, `hypothesis`, `missing_join_key`, and `required_validation`.

Regression:

- `CONTEXT-CONTAMINATION-CROSS-TASK-001`

## 4. Files Updated

- account security skill and runtime summary.
- protocol attack skill and runtime summary.
- traffic anti-cheating skill and runtime summary.
- answer templates.
- observation contract.
- track-analysis playbook and URL template.
- browser auth preflight checklist.
- scene routing.
- runtime validation cases.
- smoke tests.
- semi-open release manifest patch plan.

## 5. Still Not Done

- No runtime hook update.
- No gateway post-spawn hook.
- No live overlay.
- No real platform validation.
- No package rebuild.

## 6. Next Step

After review, sync these mother-body rules into the live overlay or next release package, then run targeted runtime validation for the new regression cases.
