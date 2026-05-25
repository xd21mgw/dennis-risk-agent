# Context Boundary Guard Generalization Patch v1

## 1. Goal

Generalize the context contamination fix beyond `CONTEXT-CONTAMINATION-CROSS-TASK-001`.

The prior fix covered macro traffic dashboard contamination. This patch adds a generic context boundary mechanism for all entry points and task types.

## 2. Scope

Local-only updates:

- runtime guard contract;
- scene routing;
- response templates;
- runtime validation cases;
- smoke tests.

No runtime hook, gateway config, real platform access, DataAgent call, release repack, or auth change was performed.

## 3. New Task Fingerprint

```yaml
task_fingerprint:
  task_type: single_case_analysis | interface_alert_analysis | batch_analysis | strategy_design | methodology | validation_followup
  subject_type: user | device | interface | campaign | channel | batch | general
  subject_ids:
    - UID/DID/IP/interface/rule_id/batch_id/safe_ref
  time_window:
  risk_domain:
  user_intent:
```

## 4. New Context Modes

- `fresh_context`: new subject, new task type, new risk domain, new time window, or unclear relation.
- `same_task_continuation`: same task fingerprint and same subject/time window.
- `same_batch_continuation`: same batch id or same case set and same risk domain.
- `methodology_mode`: concepts, methodology, strategy principles, or evaluation framework.

## 5. Inheritance Policy

Allowed by default:

- `domain_knowledge`
- `methodology`
- `response_template`

Denied by default:

- `previous_case_evidence`
- `previous_tool_observation`
- `previous_entity_ids`
- `previous_final_judgement`

Evidence inheritance is allowed only when `same_task_continuation` or `same_batch_continuation` matches the task fingerprint. Inherited evidence must carry provenance.

Historical cases may be used as general pattern / hypothesis, not current evidence.

## 6. Response-time Provenance Check

Facts in the output must come from:

- `current_input`, or
- `current_task_observation`.

The Agent must not cite out-of-scope UID / DID / IP / BSSID / interface / platform observation as current evidence.

Missing join key means no conclusion of:

- same gang;
- same attack chain;
- same batch risk;
- shared infrastructure.

If historical cases are mentioned, label them as "historical experience / similar pattern".

## 7. Regression Cases Added

- `PREVIOUS_ATO_CASE_THEN_NEW_INTERFACE_ALERT`
- `PREVIOUS_DEVICE_CASE_THEN_STRATEGY_DESIGN`
- `PREVIOUS_BATCH_THEN_NEW_SINGLE_CASE`
- `SAME_ALERT_CONTINUE_VALIDATION_CAN_INHERIT`
- `SHORT_FOLLOWUP_WITH_NEW_SUBJECT_SHOULD_FRESH`
- `METHODOLOGY_QUESTION_SHOULD_NOT_INHERIT_CASE_EVIDENCE`

## 8. Files Updated

- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`

## 9. Boundaries

- real_platform_called: false
- DataAgent_called: false
- release_repacked: false
- auth_or_gateway_modified: false
- runtime_modified: false
- git_committed: false
