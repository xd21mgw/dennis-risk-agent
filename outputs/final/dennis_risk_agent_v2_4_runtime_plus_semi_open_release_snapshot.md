# Dennis Risk Agent v2.4 Runtime Plus Semi-open Release Snapshot

## 1. Snapshot Status

```yaml
release_name: dennis_risk_agent_v2_4_runtime_plus_semi_open_release
release_path: outputs/release/dennis_risk_agent_v2_4_runtime_plus_semi_open_release/
tarball_path: outputs/dist/dennis_risk_agent_v2_4_runtime_plus_semi_open_release.tar.gz
package_type: full_scenario_semi_open_test
ato_deep_sample: true
non_ato_formal_capabilities: true
question_collection_full_scenario: true
append_only_logging_contract_included: true
package_scanner_status: warning
package_scanner_fail: 0
package_scanner_warning: 63
package_scanner_pass: 6
git_committed: false
```

## 2. Package Decision

This package is a full-scenario semi-open runtime release, not an ATO-only package.

Included:

- ATO deep sample contracts and selected evidence / pilot / browser smoke logs.
- Non-ATO runtime summaries as formal capabilities.
- Security guardrails, field classification, and asset extraction protection.
- question_collection as a full-scenario candidate learning queue with append-only runtime logging contract.
- Semi-open validation cases, user guide, and prompt matrix.

Not included:

- auth states.
- cookie / token / session / header plaintext.
- raw observation dumps.
- historical full run logs.
- unreviewed eval pilot raw assets.
- outputs/dist old packages.
- full source / full prompt / full skill corpora.

## 3. Runtime Logging Boundary

question_collection in this release means:

- `question_learning_candidate_queue_v1.csv` is template-only.
- real user questions append to `runtime_logs/question_collection/question_records_YYYYMMDD.jsonl`.
- `agent_observed` / `agent_suggested` / `reviewer_final` three-layer record structure.
- `reviewer_decision` defaults to `pending`.
- no automatic Skill / Prompt / release update.

## 4. Scanner Result

Local package asset scanner result:

- `status=warning`
- `fail=0`
- `warning=63`
- `pass=6`

Interpretation:

- no hard exclusion violation.
- warnings are expected from selected POC / run log / prompt matrix / runtime summary paths.
- release README and manifest explain these warnings as selected, minimized, or summary assets.

## 5. Recommended Next Step

Use this package for semi-open validation only.
Do not treat it as a production auto-learning or auto-governance system.

