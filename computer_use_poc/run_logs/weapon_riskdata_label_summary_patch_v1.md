# Weapon riskData Label Summary Patch v1

## Purpose

Weapon `riskData` can return `labelInfo`, but the previous runner output did not convert those labels into a safe evidence-card summary. That made device-risk analysis weak even when the source completed.

This patch adds a local summary layer that converts raw `labelInfo` into `risk_label_summary`.

## Code Change

Updated `computer_use_poc/sso_session_runner.py`:

- recursively finds `labelInfo` / label-like fields in Weapon riskData JSON;
- converts labels into safe readable summaries;
- counts high / medium / weak labels;
- extracts group name / level if present;
- flags key risk themes when present:
  - `machine_account`
  - `no_sim`
  - `no_lock_screen`
  - `factory_reset`
  - `low_launch_count`
  - `uid_cluster`
- stores output under `source_card.risk_label_summary`;
- marks `source_quality.raw_labelInfo_retained_for_summary=true`;
- keeps `sensitive_output=false`.

## Boundary

- Raw labelInfo is only used in the internal summary generation layer.
- Final answer, evidence card, and run log must not output full raw labelInfo JSON.
- Full deviceId and auth material must not be output.
- Empty `labelInfo` must produce:
  - `risk_label_summary.empty=true`
  - `no_risk_label_not_no_risk_proof=true`
- Empty labels are not no-risk proof.

## Regression

- `WEAPON-RISKDATA-LABEL-SUMMARY-001`
- `RISKDATA-RAW-LABELINFO-NOT-FINAL-OUTPUT-001`
- `RISKDATA-EMPTY-LABEL-NOT-NO-RISK-001`

## Safety

- Did not access real platforms.
- Did not call DataAgent.
- Did not modify live config.
- Did not modify `TOOLS.md`.
