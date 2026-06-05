# Bin Runner Contract v1

## Purpose

Bin runners are the controlled execution entrypoints for `dennis-risk-agent` source calls. They let the child agent invoke readonly platform sources without writing scripts, using arbitrary URLs, passing headers, or relying on main-agent direct execution.

## Required Invocation Boundary

- The child agent must execute the runner binary under `bin/` by runner name.
- The main agent must not execute platform runners on behalf of Dennis.
- Do not invoke runners with `uv run`.
- Do not invoke implementation files directly with `python3 runner.py`.
- Do not use curl plus cookies.
- Do not pass arbitrary target URLs, headers, cookies, sessions, or tokens.
- Every runner must expose a fixed action whitelist and argument schema.

Allowed pattern:

```text
bin/<runner_name> --action <allowed_action> --fixed-argument ...
```

Disallowed patterns:

```text
uv run computer_use_poc/<runner>.py ...
python3 computer_use_poc/<runner>.py ...
curl -H "Cookie field ..." ...
bin/<runner_name> --target-url ...
bin/<runner_name> --header ...
```

## Runner Output Contract

Every runner must emit one structured JSON object to stdout. It must include:

```yaml
source_card:
  source_name:
  source_status:
  evidence_summary:
  records_count:
source_quality:
  permission_status:
  auth_status:
  response_type:
  reliability_level:
  no_data_not_risk_exclusion: true
source_checkpoint_private:
  raw_references: []
  downstream_source_chaining: []
redaction:
  redaction_applied: true
  sensitive_output: false
  raw_reference_retained_for_followup: true/false
```

## Sensitive Output Policy

- cookie, token, session, header, password, and authorization material must never be printed.
- User-visible fields must use summaries, aliases, or masked values where required by field-output policy.
- Raw references may exist only in `source_checkpoint_private` for current-task source chaining.

## Runner Readiness

Runner registry lives in `computer_use_poc/runner_registry_v1.yaml`.

Readiness values:

- `runner_ready`
- `candidate_runner`
- `planned_or_minimal_stub`
- `playbook_ready_not_runner_ready`
- `endpoint_verified_not_runner_ready`

`playbook_ready` or `endpoint_verified` never means source completed in the current task.
