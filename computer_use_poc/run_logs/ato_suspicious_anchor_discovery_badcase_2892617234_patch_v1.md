# ATO Suspicious Anchor Discovery Bad Case 2892617234 Patch v1

## 1. Bad Case Background

User asked whether user `2892617234` was stolen. The runtime produced a partial evidence answer organized around Track, RCP, Weapon, login logs, and Archives source status. It did not first discover suspicious anchors. After the user added `WEB 登录发了导流视频`, the correct ATO path became obvious.

## 2. Root Cause

- ATO naked question path lacked `suspicious_anchor_discovery` as first step.
- The answer structure favored source inventory over control-chain / action-chain reasoning.
- Track was treated too close to owner/device-normal support.
- Login log `response_too_large` was not strongly separated from completed login evidence.
- Device evaluation over-focused on `device_id`, missing model / OS / UA / IP / login source / login type drift.
- User-facing response could expose runtime process fields instead of a business evidence card.

## 3. Modified Files

- `computer_use_poc/source_orchestration_plan_v1.yaml`
- `computer_use_poc/scene_to_capability_routing.md`
- `computer_use_poc/capability_registry.md`
- `computer_use_poc/answer_experience_templates.md`
- `computer_use_poc/multi_entry_runtime_guard_v1.md`
- `computer_use_poc/runtime_semi_open_user_guide_v1.md`
- `computer_use_poc/browser_backed_service_adapter_v1.md`
- `computer_use_poc/source_orchestration_check.py`
- `computer_use_poc/runtime_validation_cases_v1.yaml`
- `computer_use_poc/browser_backed_fixed_actions_text_dryrun.py`
- `computer_use_poc/browser_backed_fixed_actions_text_regression_cases_v1.yaml`
- `computer_use_poc/smoke_tests.md`
- `skills/dennis_risk_agent_skills_v2_1_focused_deep/11_runtime_summaries/account_security_runtime_summary_v1.md`
- `computer_use_poc/bad_cases/BC-ATO-SUSPICIOUS-ANCHOR-2892617234.md`
- `computer_use_poc/run_logs/ato_suspicious_anchor_discovery_badcase_2892617234_patch_v1.md`

## 4. New Rules

- ATO single-case first step is `suspicious_anchor_discovery`.
- Login/control-chain and content/action-chain are the suspicious-source discovery mainline.
- Track / Weapon / RCP are auxiliary support sources, not anchor discovery replacements.
- Device risk uses `device_identity_consistency`, not `device_id` alone.
- `common_device_id_not_sufficient_to_exclude_ato` blocks common-device no-risk shortcuts.
- `response_too_large` is `source_contract_gap`, not login evidence.
- UI no-data plus wrapper large response becomes `wrapper_response_mismatch` and `login_log_evidence_unusable`.
- User-facing ATO answer must use business evidence-card sections and must not expose runtime YAML.
- Offline Hive query plans for login-chain gaps must cite `account_security_hive_source_registry_v1.md` and remain plan-only until user authorization.

## 5. New Regression

- `ATO-SINGLE-NAKED-QUESTION-ANCHOR-FIRST-001`
- `ATO-NAKED-QUESTION-ACTION-DISCOVERY-001`
- `ATO-WEB-PUBLISH-DEEP-DIVE-001`
- `ATO-PUBLISH-VIDEO-ANCHOR-001`
- `ATO-COMMON-DEVICE-ID-SPOOFING-001`
- `ATO-DEVICE-ID-NOT-SOLE-IDENTITY-001`
- `ATO-COMMON-DEVICE-NOT-EXCLUSION-001`
- `TRACK-NOT-PROOF-OF-OWNER-001`
- `TRACK-BACKEND-MISMATCH-001`
- `LOGIN-RESPONSE-TOO-LARGE-NOT-EVIDENCE-001`
- `LOGIN-UI-NODATA-WRAPPER-LARGE-MISMATCH-001`
- `ATO-LOGIN-HIVE-REGISTRY-FIRST-001`
- `USER-FACING-NO-ROUTING-METADATA-001`
- `SOURCE-PLAN-NOT-FLAT-SOURCE-SUMMARY-001`

## 6. Validation Commands

Executed local-only validation:

```bash
git status --short
git diff --stat
git diff --check
PYTHONPYCACHEPREFIX=/private/tmp/pycache-dennis python3 -m py_compile computer_use_poc/source_orchestration_check.py computer_use_poc/browser_backed_fixed_actions_text_dryrun.py
python3 -c 'import json, pathlib; json.loads(pathlib.Path("computer_use_poc/source_orchestration_plan_v1.yaml").read_text()); print("SOURCE_PLAN_JSON_OK")'
python3 - <<'PY'
import yaml, pathlib
p = pathlib.Path("computer_use_poc/runtime_validation_cases_v1.yaml")
yaml.safe_load(p.read_text())
print("YAML_OK")
PY
python3 computer_use_poc/source_orchestration_check.py --format json
python3 computer_use_poc/source_orchestration_check.py --ato-single-case --answer-text '<business answer sample>' --format json
python3 computer_use_poc/browser_backed_fixed_actions_text_dryrun.py --format markdown
grep -R "suspicious_anchor_discovery\|device_identity_consistency\|possible_device_id_spoofing\|wrapper_response_mismatch\|login_log_evidence_unusable\|front_backend_activity_mismatch" computer_use_poc AGENTS.md 2>/dev/null
```

Results:

- `git diff --check`: passed.
- `py_compile`: passed for modified Python files.
- `source_orchestration_plan_v1.yaml` JSON-compatible parse: `SOURCE_PLAN_JSON_OK`.
- `runtime_validation_cases_v1.yaml`: Python PyYAML command failed because `yaml` module is not installed in the local Python; Ruby stdlib YAML parse passed with `YAML_OK_RUBY`.
- `source_orchestration_check.py --format json`: `validation_pass=true`, `static_plan_contract_valid=true`; default single-user ATO plan now starts with `ato_suspicious_anchor_discovery`.
- ATO user-facing answer gate sample: `validation_pass=true`, `ato_single_case_answer_validated=true`.
- `browser_backed_fixed_actions_text_dryrun.py --format markdown`: `57/57` passed; `real_platform_called=false`, `dataagent_called=false`, `hive_called=false`.
- Keyword check found required ATO anchor/device/login-contract markers.
- Diff check for `outputs/full_runtime`, `outputs/release`, and `outputs/dist`: no modified files.

## 7. Not Done

- Did not access real platforms.
- Did not call DataAgent/Hive.
- Did not change auth, gateway, safeBins, or TOOLS configuration.
- Did not modify `outputs/full_runtime`, `outputs/release`, or `outputs/dist`.
- Did not repackage runtime assets.
- Did not commit git changes.
