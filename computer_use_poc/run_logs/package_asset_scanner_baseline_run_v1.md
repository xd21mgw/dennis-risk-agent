# Package Asset Scanner Baseline Run v1

## 1. Goal

Add a lightweight local package scanner for Dennis Risk Agent semi-open release candidates.

The scanner checks whether a release directory accidentally includes high-risk assets such as auth state files, historical packages, full run logs, full test libraries, prompt/skill source, source observations, drafts, POC process files, and development artifacts.

This run is local-only:

- no real platform access
- no real API call
- no auth state read
- no DataAgent call
- no formal release/dist package update

## 2. Added Files

- `computer_use_poc/package_asset_scanner.py`
- `computer_use_poc/package_asset_scanner_rules.json`
- `computer_use_poc/run_logs/package_asset_scanner_baseline_run_v1.md`

## 3. Modified Files

- `computer_use_poc/smoke_tests.md`

## 4. Scanner Behavior

Scanner properties:

- path-level scan only
- does not read file contents
- does not open suspected auth state / cookie / token / session files
- supports allowlist and denylist rules
- emits `pass / fail / warning`
- can emit human-readable text or JSON

Default command:

```bash
python3 computer_use_poc/package_asset_scanner.py outputs/release/<release_name>
```

JSON command:

```bash
python3 computer_use_poc/package_asset_scanner.py outputs/release/<release_name> --json
```

Custom rules:

```bash
python3 computer_use_poc/package_asset_scanner.py <target_dir> --rules <rules.json>
```

## 5. Check Coverage

Covered by path rules:

- `.git/`
- `.ks_sso/`
- auth state JSON
- browser_storage_state_marker JSON
- cookie / session path names
- nested `outputs/dist`
- nested `outputs/release`
- drafts / intermediate artifacts
- run_logs
- regression case libraries
- prompt injection cases
- asset extraction cases
- full `smoke_tests.md`
- raw `SKILL.md`
- prompt assets
- POC process files
- source observations

## 6. Example Scan Result

Target:

- `outputs/release/dennis_risk_agent_v2_6_full_experience_first_release`

Result:

```text
status=warning
summary={'fail': 0, 'warning': 54, 'pass': 0, 'total_findings': 54}
category_counts={'poc_process_file': 38, 'auth-state category_doc': 1, 'raw_observation': 4, 'run_logs': 10, 'full_test_suite': 1}
```

Interpretation:

- No P0 packaged credential/auth-state file was detected by path-level scan.
- Existing full release still contains many development/POC files, selected run logs, source observation samples, and full smoke tests.
- It is acceptable as a historical full release, but should not be used as a slim semi-open package without minimization.

## 7. Known Limits

- Path-level only; no content scanning.
- Does not prove a file is safe, only catches known risky path patterns.
- May warn on safe documentation if filename contains risk keywords.
- Does not replace manual manifest review.
- Does not implement runtime asset extraction enforcement.

## 8. Next TODO

- Add optional content scanner for non-sensitive text files.
- Add CI check for release candidate packaging.
- Produce a minimized semi-open package allowlist.
- Generate a safe smoke test summary to replace full `smoke_tests.md` in semi-open packages.
